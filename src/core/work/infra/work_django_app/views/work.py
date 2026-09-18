import logging
from datetime import timedelta
from io import BytesIO

from django.http import FileResponse
from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework.throttling import UserRateThrottle
from django_project.settings import EMAIL_HOST_USER
from django_project.permissions import IsAdminOrManagement, IsWorkOwnerOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from core.edition.infra.edition_django_app.models import Edition
from core.user.infra.user_django_app.models import User, UserClass
from core.work.infra.work_django_app.models import Work, WorkCollaborator
from core.work.infra.work_django_app.serializers import (
    WorkDetailSerializer,
    WorkWriteSerializer,
    WorkListSerializer
)
from core.__seedwork.domain.actions.work_path import work_path, work_path_submission, work_collaborator_path
from core.work.infra.work_django_app.filters import WorkFilter
from core.work.domain.value_objects import WorkAdvisorStatusType, WorkCollaboratorStatusType, WorkStatusType
from core.work.domain.tasks.send_email_advisor.send_work_email_to_advisor import send_work_email_to_advisor
from core.work.domain.tasks.send_email_collaborator.send_work_email_to_collaborator import send_work_email_to_collaborator
from core.work.domain.tasks.send_email_advisor.send_work_update_to_advisor import notify_advisor_on_data_update

logger = logging.getLogger(__name__)


KANBAN_COLUMNS = [
    ("waiting_advisor", "Aguardando orientador"),
    ("advisor_rejected", "Orientador recusou"),
    ("needs_changes", "Precisa de ajustes"),
    ("ready", "Orientador aceitou"),
    ("approved", "Trabalho aprovado"),
    ("rejected", "Trabalho rejeitado/cancelado"),
    ("expired", "Expirado"),
]


def _choice_label(enum_cls, value):
    for member in enum_cls:
        if member.value == value:
            return member.label
    return "Nao informado"


def _serialize_user(user):
    if not user:
        return None

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


def _format_date(value):
    if not value:
        return None

    return value.strftime("%d/%m/%Y")


def _default_edition():
    editions = list(Edition.objects.order_by("-year", "-id"))
    if not editions:
        return None

    for edition in editions:
        if (
            edition.is_active
            or edition.is_open_for_submissions
            or edition.is_open_for_advisors
            or edition.is_open_for_evaluators
            or edition.is_edition_running
        ):
            return edition

    return editions[0]


def _report_release_date(edition):
    if not edition.final_second_advisor_date:
        return None

    return edition.final_second_advisor_date + timedelta(days=1)


def _proposal_report_availability(edition):
    release_date = _report_release_date(edition)
    if not release_date:
        return {
            "available": False,
            "available_after": None,
            "message": "A edicao nao possui data final da segunda aceitacao de orientadores.",
        }

    if timezone.localdate() < release_date:
        return {
            "available": False,
            "available_after": release_date.isoformat(),
            "message": f"Relatorio disponivel a partir de {_format_date(release_date)}.",
        }

    return {
        "available": True,
        "available_after": release_date.isoformat(),
        "message": None,
    }


def _accepted_collaborators_for(work):
    return [
        link.collaborator
        for link in work.work_collaborator.all()
        if link.status == WorkCollaboratorStatusType.Type.APPROVED.value
    ]


def _team_classes_label(work, edition):
    classes = sorted(
        {
            user_class.class_name.name
            for member in work.team.team_members.all()
            for user_class in member.user_classes.all()
            if user_class.year == edition.year and user_class.class_name
        }
    )
    return ", ".join(classes) or "-"


def _member_classes_label(member, edition):
    classes = sorted(
        {
            user_class.class_name.name
            for user_class in member.user_classes.all()
            if user_class.year == edition.year and user_class.class_name
        }
    )
    return ", ".join(classes) or "Sem turma cadastrada"


def _serialize_team_member_for_report(member, edition):
    return {
        "id": member.id,
        "name": member.name,
        "email": member.email,
        "classes_label": _member_classes_label(member, edition),
    }


def _team_members_label(work):
    members = [
        f"{member.name or member.email} ({_member_classes_label(member, work.edition)})"
        for member in work.team.team_members.all()
    ]
    return "; ".join(members) or "-"


def _team_members_for_report(work):
    return [
        _serialize_team_member_for_report(member, work.edition)
        for member in work.team.team_members.all()
    ]


def _serialize_work_for_advisor_report(work):
    collaborators = [_serialize_user(collaborator) for collaborator in _accepted_collaborators_for(work)]

    return {
        "id": str(work.id),
        "title": work.title,
        "team_members": _team_members_for_report(work),
        "team_members_label": _team_members_label(work),
        "classes_label": _team_classes_label(work, work.edition),
        "collaborators": collaborators,
        "collaborators_label": ", ".join(
            collaborator["name"] or collaborator["email"]
            for collaborator in collaborators
            if collaborator
        ) or "Sem colaborador",
    }


def _advisor_report_queryset(edition):
    return (
        Work.objects.filter(
            edition=edition,
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            status__in=[
                WorkStatusType.Type.PENDING.value,
                WorkStatusType.Type.APPROVED.value,
            ],
        )
        .select_related("advisor", "team", "edition")
        .prefetch_related(
            "team__team_members",
            Prefetch(
                "team__team_members__user_classes",
                queryset=UserClass.objects.select_related("class_name").filter(year=edition.year),
            ),
            Prefetch(
                "work_collaborator",
                queryset=WorkCollaborator.objects.select_related("collaborator").order_by("collaborator__name"),
            ),
        )
        .distinct()
        .order_by("advisor__name", "title")
    )


def _group_works_by_advisor(works):
    groups = {}

    for work in works:
        advisor_key = work.advisor_id
        if advisor_key not in groups:
            groups[advisor_key] = {
                "advisor": _serialize_user(work.advisor),
                "rows": [],
            }
        groups[advisor_key]["rows"].append(_serialize_work_for_advisor_report(work))

    grouped = list(groups.values())
    grouped.sort(
        key=lambda group: (
            (group["advisor"] or {}).get("name")
            or (group["advisor"] or {}).get("email")
            or ""
        ).lower()
    )

    for group in grouped:
        group["count"] = len(group["rows"])

    return grouped


def _advisor_label(advisor):
    if not advisor:
        return "Orientador nao informado"

    return advisor.get("name") or advisor.get("email") or "Orientador nao informado"


def _build_advisor_report_pdf(*, edition, groups):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]

    elements = [
        Paragraph("Relatorio de propostas por orientador", styles["Heading1"]),
        Spacer(1, 8),
        Paragraph(f"Edicao: {edition.edition_name} ({edition.year})", normal),
        Spacer(1, 14),
    ]

    if not groups:
        elements.append(Paragraph("Nenhum trabalho encontrado para esta edicao.", normal))
    else:
        for group in groups:
            elements.append(Paragraph(f"Orientador: {_advisor_label(group['advisor'])}", styles["Heading2"]))
            elements.append(Spacer(1, 6))

            data = [["Titulo do trabalho", "Equipe / turma", "Turmas", "Colaborador(es)"]]
            for row in group["rows"]:
                data.append(
                    [
                        Paragraph(row["title"] or "-", normal),
                        Paragraph(row["team_members_label"], normal),
                        Paragraph(row["classes_label"], normal),
                        Paragraph(row["collaborators_label"], normal),
                    ]
                )

            table = Table(
                data,
                colWidths=[doc.width * 0.34, doc.width * 0.30, doc.width * 0.14, doc.width * 0.22],
                repeatRows=1,
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            elements.append(table)
            elements.append(Spacer(1, 14))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def _work_submission_date(work):
    first_record = work.history.order_by("history_date").first()
    return first_record.history_date if first_record else None


def _serialize_work_for_team_report(work):
    advisor = _serialize_user(work.advisor)

    return {
        "id": str(work.id),
        "title": work.title or "-",
        "status": work.status,
        "status_label": _choice_label(WorkStatusType.Type, work.status),
        "advisor_status": work.advisor_status,
        "advisor_status_label": _choice_label(WorkAdvisorStatusType.Type, work.advisor_status),
        "advisor": advisor,
        "advisor_label": _advisor_label(advisor),
        "submitted_at": _format_date(_work_submission_date(work)),
    }


def _team_report_queryset(edition):
    return (
        Work.objects.filter(edition=edition)
        .select_related("advisor", "team", "edition")
        .prefetch_related(
            "team__team_members",
            Prefetch(
                "team__team_members__user_classes",
                queryset=UserClass.objects.select_related("class_name").filter(year=edition.year),
            ),
        )
        .order_by("team_id", "title")
    )


def _group_works_by_team(works, edition):
    groups = {}

    for work in works:
        team_key = work.team_id
        if team_key not in groups:
            groups[team_key] = {
                "team_id": team_key,
                "team_members": _team_members_for_report(work),
                "team_members_label": _team_members_label(work),
                "classes_label": _team_classes_label(work, edition),
                "rows": [],
            }
        groups[team_key]["rows"].append(_serialize_work_for_team_report(work))

    grouped = list(groups.values())
    grouped.sort(key=lambda group: group["team_members_label"].lower())

    for group in grouped:
        group["count"] = len(group["rows"])

    return grouped


def _build_team_report_xlsx(*, edition, groups):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Propostas por equipe"

    headers = [
        "Equipe",
        "Turmas da equipe",
        "Aluno",
        "Turma do aluno",
        "Trabalho",
        "Status do trabalho",
        "Orientador",
        "Status do orientador",
        "Data da submissao",
    ]
    sheet.append(headers)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
    for column_index in range(1, len(headers) + 1):
        cell = sheet.cell(row=1, column=column_index)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center")

    for group in groups:
        for row in group["rows"]:
            members = group["team_members"] or [{"name": None, "email": None, "classes_label": "-"}]
            for member in members:
                sheet.append(
                    [
                        group["team_members_label"],
                        group["classes_label"],
                        member["name"] or member["email"] or "Nao informado",
                        member["classes_label"],
                        row["title"],
                        row["status_label"],
                        row["advisor_label"],
                        row["advisor_status_label"],
                        row["submitted_at"] or "-",
                    ]
                )

    column_widths = [34, 18, 28, 18, 32, 22, 28, 22, 18]
    for index, width in enumerate(column_widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width

    sheet.freeze_panes = "A2"

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def _teacher_workload_report_queryset(edition):
    return (
        Work.objects.filter(edition=edition)
        .select_related("advisor", "edition")
        .prefetch_related(
            Prefetch(
                "work_collaborator",
                queryset=WorkCollaborator.objects.select_related("collaborator"),
            ),
        )
        .order_by("title")
    )


def _group_works_by_teacher_workload(works):
    teachers = {}

    def _teacher_entry(user):
        key = user.id
        if key not in teachers:
            teachers[key] = {
                "teacher": _serialize_user(user),
                "advising_titles": [],
                "collaboration_titles": [],
            }
        return teachers[key]

    for teacher in User.objects.filter(user_type=User.TEACHER).order_by("name"):
        _teacher_entry(teacher)

    for work in works:
        if work.advisor and work.advisor_status == WorkAdvisorStatusType.Type.APPROVED.value:
            entry = _teacher_entry(work.advisor)
            entry["advising_titles"].append(work.title or "-")

        for collaborator in _accepted_collaborators_for(work):
            entry = _teacher_entry(collaborator)
            entry["collaboration_titles"].append(work.title or "-")

    grouped = list(teachers.values())
    for entry in grouped:
        entry["advising_count"] = len(entry["advising_titles"])
        entry["collaboration_count"] = len(entry["collaboration_titles"])
        entry["total_count"] = entry["advising_count"] + entry["collaboration_count"]

    grouped.sort(
        key=lambda entry: (
            (entry["teacher"] or {}).get("name")
            or (entry["teacher"] or {}).get("email")
            or ""
        ).lower()
    )

    return grouped


def _build_teacher_workload_report_xlsx(*, edition, groups):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Orientacao e colaboracao"

    headers = [
        "Professor",
        "E-mail",
        "Qtd. orientacoes",
        "Trabalhos orientados",
        "Qtd. colaboracoes",
        "Trabalhos em colaboracao",
        "Total de trabalhos",
    ]
    sheet.append(headers)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
    for column_index in range(1, len(headers) + 1):
        cell = sheet.cell(row=1, column=column_index)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center")

    for entry in groups:
        teacher = entry["teacher"] or {}
        sheet.append(
            [
                teacher.get("name") or teacher.get("email") or "Nao informado",
                teacher.get("email") or "-",
                entry["advising_count"],
                "; ".join(entry["advising_titles"]) or "-",
                entry["collaboration_count"],
                "; ".join(entry["collaboration_titles"]) or "-",
                entry["total_count"],
            ]
        )

    column_widths = [28, 30, 16, 40, 16, 40, 16]
    for index, width in enumerate(column_widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width

    sheet.freeze_panes = "A2"

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def _kanban_column_for(work):
    if (
        work.status == WorkStatusType.Type.EXPIRED.value
        or work.advisor_status == WorkAdvisorStatusType.Type.EXPIRED.value
    ):
        return "expired"

    if work.status == WorkStatusType.Type.REJECTED.value:
        return "rejected"

    if work.status == WorkStatusType.Type.NEEDS_CHANGES.value:
        return "needs_changes"

    if work.status == WorkStatusType.Type.APPROVED.value:
        return "approved"

    if work.advisor_status == WorkAdvisorStatusType.Type.REJECTED.value:
        return "advisor_rejected"

    if work.advisor_status == WorkAdvisorStatusType.Type.APPROVED.value:
        return "ready"

    return "waiting_advisor"


def _history_actor(history_record):
    user = getattr(history_record, "history_user", None)
    if not user:
        return None

    return _serialize_user(user)


def _history_entry(history_record, *, source, fallback_label, collaborator=None):
    reason = getattr(history_record, "history_change_reason", None) or fallback_label
    entry = {
        "source": source,
        "event": reason,
        "history_type": history_record.history_type,
        "date": history_record.history_date.isoformat(),
        "actor": _history_actor(history_record),
    }

    if source == "work":
        entry["status"] = history_record.status
        entry["status_label"] = _choice_label(WorkStatusType.Type, history_record.status)
        entry["advisor_status"] = history_record.advisor_status
        entry["advisor_status_label"] = _choice_label(WorkAdvisorStatusType.Type, history_record.advisor_status)

    if source == "collaborator":
        entry["collaborator"] = _serialize_user(collaborator.collaborator if collaborator else None)
        entry["status"] = history_record.status
        entry["status_label"] = _choice_label(WorkCollaboratorStatusType.Type, history_record.status)

    return entry


def _timeline_for(work):
    entries = []

    for record in work.history.order_by("history_date"):
        fallback = {
            "+": "Trabalho criado",
            "~": "Trabalho atualizado",
            "-": "Trabalho removido",
        }.get(record.history_type, "Trabalho atualizado")
        entries.append(_history_entry(record, source="work", fallback_label=fallback))

    for collaborator in work.work_collaborator.all():
        for record in collaborator.history.order_by("history_date"):
            fallback = {
                "+": "Colaborador vinculado",
                "~": "Colaborador atualizado",
                "-": "Colaborador removido",
            }.get(record.history_type, "Colaborador atualizado")
            entries.append(
                _history_entry(
                    record,
                    source="collaborator",
                    fallback_label=fallback,
                    collaborator=collaborator,
                )
            )

    return sorted(entries, key=lambda item: item["date"])


def _serialize_work_for_kanban(work):
    collaborators = [
        {
            "id": link.id,
            "status": link.status,
            "status_label": _choice_label(WorkCollaboratorStatusType.Type, link.status),
            "collaborator": _serialize_user(link.collaborator),
        }
        for link in work.work_collaborator.all()
    ]
    timeline = _timeline_for(work)

    return {
        "id": str(work.id),
        "title": work.title,
        "abstract": work.abstract,
        "status": work.status,
        "status_label": _choice_label(WorkStatusType.Type, work.status),
        "advisor_status": work.advisor_status,
        "advisor_status_label": _choice_label(WorkAdvisorStatusType.Type, work.advisor_status),
        "feedback": work.feedback,
        "needs_changes_submission_work_date": work.needs_changes_submission_work_date,
        "integrated_project": work.integrated_project,
        "edition": {
            "id": work.edition_id,
            "year": work.edition.year,
            "edition_name": work.edition.edition_name,
        },
        "advisor": _serialize_user(work.advisor),
        "team_members": [_serialize_user(member) for member in work.team.team_members.all()],
        "collaborators": collaborators,
        "has_collaborators": bool(collaborators),
        "timeline": timeline,
        "last_event": timeline[-1] if timeline else None,
    }

@extend_schema(tags=["work"])
class WorkViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = Work.objects.select_related(
            'cross_cutting_theme',
            'advisor',
            'team',
            'edition',
        )
        
        if self.action == 'retrieve':
            # Otimiza prefetch apenas para detail view
            return queryset.prefetch_related(
                'field',
                'ods',
                'evaluator',
                'team__team_members',
                Prefetch(
                    'work_collaborator',
                    queryset=WorkCollaborator.objects.select_related('collaborator')
                )
            )
        
        # Lista não precisa de tantos relacionamentos
        return queryset.prefetch_related('field', 'ods')
    serializer_class = WorkDetailSerializer
    throttle_classes = [UserRateThrottle]
    filterset_class = WorkFilter
    http_method_names = ["get", "post", "patch", "put", "delete"]
    permission_classes = [IsWorkOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return WorkListSerializer
        elif self.action == "retrieve":
            return WorkDetailSerializer
        return WorkWriteSerializer

    @action(
        detail=False,
        methods=["get"],
        url_path="admin-kanban",
        permission_classes=[IsAdminOrManagement],
    )
    def admin_kanban(self, request):
        edition_id = request.query_params.get("edition")
        search = (request.query_params.get("search") or "").strip()

        if edition_id:
            try:
                edition = Edition.objects.get(id=edition_id)
            except Edition.DoesNotExist:
                return Response(
                    {"error": "Edicao nao encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            edition = _default_edition()

        columns = [
            {"key": key, "title": title, "count": 0, "items": []}
            for key, title in KANBAN_COLUMNS
        ]

        if not edition:
            return Response(
                {
                    "edition": None,
                    "summary": [],
                    "columns": columns,
                }
            )

        queryset = (
            Work.objects.filter(edition=edition)
            .select_related("advisor", "team", "edition", "cross_cutting_theme")
            .prefetch_related(
                "team__team_members",
                Prefetch(
                    "work_collaborator",
                    queryset=WorkCollaborator.objects.select_related("collaborator"),
                ),
            )
        )

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(team__team_members__name__icontains=search)
                | Q(team__team_members__email__icontains=search)
                | Q(advisor__name__icontains=search)
                | Q(advisor__email__icontains=search)
                | Q(work_collaborator__collaborator__name__icontains=search)
                | Q(work_collaborator__collaborator__email__icontains=search)
                | Q(
                    team__team_members__user_classes__class_name__name__icontains=search,
                    team__team_members__user_classes__year=edition.year,
                )
            ).distinct()

        column_map = {column["key"]: column for column in columns}
        for work in queryset:
            column = column_map[_kanban_column_for(work)]
            column["items"].append(_serialize_work_for_kanban(work))

        for column in columns:
            column["count"] = len(column["items"])

        return Response(
            {
                "edition": {
                    "id": edition.id,
                    "year": edition.year,
                    "edition_name": edition.edition_name,
                },
                "summary": [
                    {"key": column["key"], "title": column["title"], "count": column["count"]}
                    for column in columns
                ],
                "columns": columns,
            }
        )

    def _get_advisor_report_context(self, request):
        edition_id = request.query_params.get("edition")

        if not edition_id:
            return None, Response(
                {"error": "Informe a edicao para gerar o relatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            edition = Edition.objects.get(id=edition_id)
        except Edition.DoesNotExist:
            return None, Response(
                {"error": "Edicao nao encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        availability = _proposal_report_availability(edition)
        groups = _group_works_by_advisor(_advisor_report_queryset(edition)) if availability["available"] else []

        return {
            "edition": edition,
            "availability": availability,
            "groups": groups,
            "total_works": sum(group["count"] for group in groups),
        }, None

    @action(
        detail=False,
        methods=["get"],
        url_path="admin-advisor-report-data",
        permission_classes=[IsAdminOrManagement],
    )
    def admin_advisor_report_data(self, request):
        context, error_response = self._get_advisor_report_context(request)
        if error_response:
            return error_response

        edition = context["edition"]

        return Response(
            {
                "edition": {
                    "id": edition.id,
                    "year": edition.year,
                    "edition_name": edition.edition_name,
                    "final_second_advisor_date": edition.final_second_advisor_date,
                },
                "available": context["availability"]["available"],
                "available_after": context["availability"]["available_after"],
                "message": context["availability"]["message"],
                "total_works": context["total_works"],
                "groups": context["groups"],
            }
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="admin-advisor-report",
        permission_classes=[IsAdminOrManagement],
    )
    def admin_advisor_report(self, request):
        context, error_response = self._get_advisor_report_context(request)
        if error_response:
            return error_response

        availability = context["availability"]
        if not availability["available"]:
            return Response(
                {"error": availability["message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        edition = context["edition"]
        buffer = _build_advisor_report_pdf(
            edition=edition,
            groups=context["groups"],
        )
        filename = f"relatorio_propostas_orientadores_{edition.year}.pdf".replace(" ", "_")

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )

    def _get_team_report_context(self, request):
        edition_id = request.query_params.get("edition")

        if not edition_id:
            return None, Response(
                {"error": "Informe a edicao para gerar o relatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            edition = Edition.objects.get(id=edition_id)
        except Edition.DoesNotExist:
            return None, Response(
                {"error": "Edicao nao encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        groups = _group_works_by_team(_team_report_queryset(edition), edition)

        return {
            "edition": edition,
            "groups": groups,
            "total_works": sum(group["count"] for group in groups),
        }, None

    @action(
        detail=False,
        methods=["get"],
        url_path="admin-team-report-data",
        permission_classes=[IsAdminOrManagement],
    )
    def admin_team_report_data(self, request):
        context, error_response = self._get_team_report_context(request)
        if error_response:
            return error_response

        edition = context["edition"]

        return Response(
            {
                "edition": {
                    "id": edition.id,
                    "year": edition.year,
                    "edition_name": edition.edition_name,
                },
                "total_works": context["total_works"],
                "groups": context["groups"],
            }
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="admin-team-report",
        permission_classes=[IsAdminOrManagement],
    )
    def admin_team_report(self, request):
        context, error_response = self._get_team_report_context(request)
        if error_response:
            return error_response

        edition = context["edition"]
        buffer = _build_team_report_xlsx(edition=edition, groups=context["groups"])
        filename = f"relatorio_propostas_equipes_{edition.year}.xlsx".replace(" ", "_")

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def _get_teacher_workload_report_context(self, request):
        edition_id = request.query_params.get("edition")

        if not edition_id:
            return None, Response(
                {"error": "Informe a edicao para gerar o relatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            edition = Edition.objects.get(id=edition_id)
        except Edition.DoesNotExist:
            return None, Response(
                {"error": "Edicao nao encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        groups = _group_works_by_teacher_workload(_teacher_workload_report_queryset(edition))

        return {
            "edition": edition,
            "groups": groups,
            "total_teachers": len(groups),
        }, None

    @action(
        detail=False,
        methods=["get"],
        url_path="admin-teacher-workload-report-data",
        permission_classes=[IsAdminOrManagement],
    )
    def admin_teacher_workload_report_data(self, request):
        context, error_response = self._get_teacher_workload_report_context(request)
        if error_response:
            return error_response

        edition = context["edition"]

        return Response(
            {
                "edition": {
                    "id": edition.id,
                    "year": edition.year,
                    "edition_name": edition.edition_name,
                },
                "total_teachers": context["total_teachers"],
                "groups": context["groups"],
            }
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="admin-teacher-workload-report",
        permission_classes=[IsAdminOrManagement],
    )
    def admin_teacher_workload_report(self, request):
        context, error_response = self._get_teacher_workload_report_context(request)
        if error_response:
            return error_response

        edition = context["edition"]
        buffer = _build_teacher_workload_report_xlsx(edition=edition, groups=context["groups"])
        filename = f"relatorio_orientacao_colaboracao_{edition.year}.xlsx".replace(" ", "_")

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def _normalize_collaborators_data(self, collaborators_data):
        """Normaliza dados de colaboradores para sempre retornar uma lista de inteiros"""
        if isinstance(collaborators_data, (int, str)):
            return [int(collaborators_data)]
        elif isinstance(collaborators_data, list):
            return [int(c) for c in collaborators_data if c]
        return []

    def _send_collaborator_emails(self, work, collaborators_data):
        """Envia emails para novos colaboradores"""
        if not collaborators_data:
            return

        for collaborator_id in collaborators_data:
            work_collaborator = WorkCollaborator.objects.filter(
                work=work, collaborator_id=collaborator_id
            ).first()
            
            if work_collaborator:
                accept_work_link, reject_work_link = work_collaborator_path(work_collaborator)
                email_subject = f"Convite para colaborar no trabalho: {work.title}"
                
                send_work_email_to_collaborator.delay(
                    work_collaborator.id,
                    email_subject,
                    EMAIL_HOST_USER,
                    accept_work_link,
                    reject_work_link
                )

    def _send_advisor_email(self, work, email_subject_prefix="Convite para orientar o trabalho"):
        """Envia email para o advisor"""
        if not work.advisor:
            return

        accept_link, reject_link, _, _ = work_path(work)
        email_subject = f"{email_subject_prefix}: {work.title}"
        email_recipient_list = [work.advisor.email]
        students_emails = [member.email for member in work.team.team_members.all()]

        send_work_email_to_advisor.delay(
            str(work.id),
            email_subject,
            EMAIL_HOST_USER,
            email_recipient_list,
            accept_link,
            reject_link,
            students_emails
        )

    def _send_pending_collaborator_reminders(self, work):
        """Envia lembretes para colaboradores pendentes"""
        pending_collaborators = WorkCollaborator.objects.filter(
            work=work, 
            status=WorkCollaboratorStatusType.Type.PENDING.value
        )
        
        for work_collaborator in pending_collaborators:
            accept_link, reject_link = work_collaborator_path(work_collaborator)
            email_subject = f"Lembrete: Convite para colaborar no trabalho: {work.title}"
            
            send_work_email_to_collaborator.delay(
                work_collaborator.id,
                email_subject,
                EMAIL_HOST_USER,
                accept_link,
                reject_link
            )

    def create(self, request, *args, **kwargs):
        collaborators_data = self._normalize_collaborators_data(
            request.data.get("collaborators", [])
        )
        
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_201_CREATED and "id" in response.data:
            work_id = response.data["id"]
            
            def send_creation_emails():
                try:
                    work = Work.objects.get(id=work_id)
                    self._send_collaborator_emails(work, collaborators_data)
                    self._send_advisor_email(work)
                except Work.DoesNotExist:
                    logger.error(f"Trabalho com ID {work_id} não encontrado para envio de emails")
                except Exception as e:
                    logger.error(f"Erro ao enviar emails na criação do trabalho: {e}")
            
            transaction.on_commit(send_creation_emails)
            
        logger.info(f"Work created with ID: {response.data.get('id')}")
        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_advisor = instance.advisor
        
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            def send_update_emails():
                try:
                    updated_work = Work.objects.get(id=instance.id)
                    
                    self._send_pending_collaborator_reminders(updated_work)
                    
                    if updated_work.advisor != old_advisor:
                        self._send_advisor_email(updated_work, "Alteração no trabalho")
                        
                except Exception as e:
                    logger.error(f"Erro ao enviar emails no update: {e}")
            
            transaction.on_commit(send_update_emails)

        return response

    def partial_update(self, request, *args, **kwargs):
        work = self.get_object()
        
        if work.status == 4:  # REJECTED
            return Response(
                {"error": "Este trabalho foi rejeitado e não pode mais ser alterado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action')
        abstract = request.data.get('abstract')
        
        if abstract:
            work.abstract = abstract
            work.save()
            
        if action == 'submission':
            def send_submission_email():
                try:
                    updated_work = Work.objects.get(id=work.id)
                    accept_link, reject_link = work_path_submission(updated_work)
                    notify_advisor_on_data_update.delay(
                        str(updated_work.id),
                        accept_link,
                        reject_link
                    )
                except Exception as e:
                    logger.error(f"Erro ao enviar email de submissão: {e}")
            
            transaction.on_commit(send_submission_email)
            return Response(
                {"message": "Abstract enviado para o orientador"}, 
                status=status.HTTP_200_OK
            )
            
        return Response(
            {"message": "Atualização realizada"}, 
            status=status.HTTP_200_OK
        )
        
    def destroy(self, request, *args, **kwargs):
        from core.work.domain.value_objects import WorkStatusType
        
        work = self.get_object()
        
        work.status = WorkStatusType.Type.REJECTED.value
        work.verification_token = None
        work._change_reason = "Trabalho rejeitado/cancelado"
        work.save()
        
        WorkCollaborator.objects.filter(work=work).update(verification_token=None)
        
        return Response(
            {"message": "Trabalho removido com sucesso. O registro foi mantido no histórico."},
            status=status.HTTP_200_OK
        )
    
