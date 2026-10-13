"""
Lembrete de nota pendente.

Disparo manual (Django admin / botao da gestao): nao ha periodo fixo nem
agendamento automatico — a comissao decide quando lembrar.

Quem deve nota hoje:
- orientador: aluno de trabalho APROVADO da edicao sem StudentAssessments;
- avaliador da banca: trabalho APROVADO atribuido a ele sem Assessment dele.

`collect_pending_grades` so le o banco (serve pro preview do botao manual);
`send_grade_reminders` manda um e-mail por pessoa, listando o que falta.
"""
import logging
from collections import OrderedDict

from django.core.mail import send_mail
from django.utils.html import escape, strip_tags

from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments
from core.work.domain.tasks.email_branding import build_panel_email
from core.work.domain.value_objects import WorkStatusType
from core.work.infra.work_django_app.models import Work

logger = logging.getLogger("grade_reminders")


def _approved_works(edition):
    return (
        Work.objects.filter(edition=edition, status=WorkStatusType.Type.APPROVED.value)
        .select_related("advisor", "team")
        .prefetch_related("team__team_members", "evaluator__user")
        .order_by("title")
    )


def collect_pending_grades(edition):
    """
    Retorna {"advisors": {user: [{"work": Work, "students": [User]}]},
             "evaluators": {user: [Work]}} so com quem ainda deve nota.
    """
    works = list(_approved_works(edition))
    work_ids = [work.id for work in works]

    graded_students = set(
        StudentAssessments.objects.filter(work_id__in=work_ids).values_list("work_id", "student_id")
    )
    graded_by_evaluator = set(
        Assessment.objects.filter(work_id__in=work_ids).values_list("work_id", "evaluator_id")
    )

    advisors = OrderedDict()
    evaluators = OrderedDict()

    for work in works:
        missing_students = [
            member
            for member in work.team.team_members.all()
            if (work.id, member.id) not in graded_students
        ]
        if missing_students and work.advisor_id:
            advisors.setdefault(work.advisor, []).append(
                {"work": work, "students": missing_students}
            )

        for evaluator in work.evaluator.all():
            if (work.id, evaluator.id) not in graded_by_evaluator:
                evaluators.setdefault(evaluator.user, []).append(work)

    return {"advisors": advisors, "evaluators": evaluators}


def _build_email(user, role_label, items_html, deadline):
    deadline_text = deadline.strftime("%d/%m/%Y") if deadline else None
    deadline_html = (
        f"<p style='margin:16px 0 0;'>O prazo para lançar as notas vai até "
        f"<strong>{deadline_text}</strong>.</p>"
        if deadline_text
        else ""
    )
    body = (
        f"<p style='margin:0 0 16px;'>Olá, <strong>{escape(user.name or user.email)}</strong>.</p>"
        f"<p style='margin:0 0 16px;'>Você ainda tem notas a lançar como <strong>{role_label}</strong>:</p>"
        "<div style='background:#f8fafc;border:1px solid #edf2f7;border-radius:6px;padding:16px 18px;'>"
        f"<ul style='margin:0;padding-left:20px;line-height:1.7;'>{items_html}</ul></div>"
        f"{deadline_html}"
        "<p style='margin:16px 0 0;color:#66788a;font-size:14px;'>"
        "Acesse o Painel, abra o trabalho e registre a nota.</p>"
    )
    return build_panel_email("Lembrete: notas pendentes", body)


def _advisor_items(entries):
    lines = []
    for entry in entries:
        names = ", ".join(escape(student.name or student.email) for student in entry["students"])
        lines.append(
            f"<li><strong>{escape(entry['work'].title)}</strong> — falta nota de: {names}</li>"
        )
    return "".join(lines)


def _evaluator_items(works):
    return "".join(f"<li><strong>{escape(work.title)}</strong></li>" for work in works)


def send_grade_reminders(edition, dry_run=False):
    """
    Manda (ou so conta, com dry_run) os lembretes da edicao.
    Retorna {"advisors": n, "evaluators": n, "emails_sent": n, "failed": n,
             "advisor_names": [...], "evaluator_names": [...]}.
    """
    from django_project.settings import EMAIL_HOST_USER

    pending = collect_pending_grades(edition)
    summary = {
        "advisors": len(pending["advisors"]),
        "evaluators": len(pending["evaluators"]),
        "emails_sent": 0,
        "failed": 0,
        "advisor_names": [user.name or user.email for user in pending["advisors"]],
        "evaluator_names": [user.name or user.email for user in pending["evaluators"]],
    }
    if dry_run:
        return summary

    deadline = edition.final_evaluators_date

    # Quem e orientador e avaliador recebe um e-mail por papel; cada um lista so o seu.
    jobs = [
        (user, "orientador(a)", _advisor_items(entries))
        for user, entries in pending["advisors"].items()
    ] + [
        (user, "avaliador(a) da banca", _evaluator_items(works))
        for user, works in pending["evaluators"].items()
    ]

    for user, role_label, items_html in jobs:
        if not user.email:
            continue
        html = _build_email(user, role_label, items_html, deadline)
        try:
            send_mail(
                "Lembrete: notas pendentes no Painel de Integração",
                strip_tags(html),
                EMAIL_HOST_USER,
                [user.email],
                html_message=html,
                fail_silently=False,
            )
            summary["emails_sent"] += 1
        except Exception:  # noqa: BLE001 - um e-mail ruim nao pode parar o resto
            summary["failed"] += 1
            logger.exception("grade_reminders: falha ao enviar para %s", user.email)

    return summary
