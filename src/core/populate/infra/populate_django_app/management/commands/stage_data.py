from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.edition.infra.edition_django_app.models import Edition
from core.field.infra.field_django_app.models import Field
from core.user.domain.value_objects import UserType
from core.user.infra.user_django_app.models import Class, Evaluator, User, UserClass
from core.work.domain.value_objects import (
    WorkAdvisorStatusType,
    WorkCollaboratorStatusType,
    WorkStatusType,
)
from core.work.infra.work_django_app.models import Ods, Team, Work, WorkCollaborator


PASSWORD = "Painel@123"
WORK_TITLE = "[TESTE GUIADO] Proposta de Integracao"
EDITION_NAME = "[TESTE GUIADO] Painel de Integracao"
ADVISOR_TOKEN = "stage-advisor-token"
COLLABORATOR_TOKEN = "stage-collaborator-token"


@dataclass(frozen=True)
class StageInfo:
    label: str
    route_owner: str
    route: str


STAGES = {
    1: StageInfo(
        "Base pronta: usuarios, turma, area, tema, ODS e edicao com datas abertas.",
        "student",
        "/panel/works/add/",
    ),
    2: StageInfo(
        "Equipe criada para o aluno testar a tela de criacao/edicao da proposta.",
        "student",
        "/panel/works/add/",
    ),
    3: StageInfo(
        "Trabalho submetido, aguardando aceite do orientador.",
        "advisor",
        "/panel/works/view/{work_id}",
    ),
    4: StageInfo(
        "Orientador aceitou e aprovou o trabalho, colaborador ainda pendente.",
        "collaborator",
        "/panel/works/view/{work_id}",
    ),
    5: StageInfo(
        "Colaborador aceitou e avaliador foi vinculado, pronto para tela de avaliacao.",
        "evaluator_user",
        "/panel/works/view/{work_id}",
    ),
    6: StageInfo(
        "Avaliacoes lancadas e relatorio pronto para conferencia.",
        "advisor",
        "/panel/works/view/{work_id}",
    ),
}


class Command(BaseCommand):
    help = "Prepara dados de desenvolvimento em estagios do fluxo do Painel."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--stage",
            type=int,
            choices=STAGES.keys(),
            help="Estagio do fluxo a preparar. Use --list para ver as opcoes.",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="Lista os estagios disponiveis.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Imprime o resultado em JSON para automacoes.",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Reduz a saida do comando.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options["list"] or not options["stage"]:
            self._print_stage_list(as_json=options["json"])
            if not options["stage"]:
                return

        if not settings.DEBUG:
            raise CommandError("stage_data so pode rodar com DEBUG=True.")

        with transaction.atomic():
            context = self._prepare_stage(options["stage"])

        if options["json"]:
            self.stdout.write(json.dumps(context, indent=2, default=str))
            return

        if not options["quiet"]:
            self._print_summary(context)

    def _print_stage_list(self, *, as_json: bool = False) -> None:
        data = {
            number: {
                "label": stage.label,
                "login": stage.route_owner,
                "route": stage.route,
            }
            for number, stage in STAGES.items()
        }
        if as_json:
            self.stdout.write(json.dumps(data, indent=2))
            return

        self.stdout.write("Estagios disponiveis:")
        for number, stage in STAGES.items():
            self.stdout.write(f"  {number}: {stage.label}")

    def _prepare_stage(self, stage: int) -> dict[str, Any]:
        today = timezone.localdate()
        accounts = self._create_accounts()
        edition = self._create_edition(today)
        field = self._first_or_create(Field, {"name": "[TESTE] Informatica"})
        theme = self._first_or_create(
            CrossCuttingTheme,
            {"name": "[TESTE] Sustentabilidade"},
            {"description": "Tema criado pelo stage_data."},
        )
        theme.advisor.set([accounts["advisor"]])
        ods = self._first_or_create(Ods, {"name": "[TESTE] ODS 4 - Educacao de Qualidade"})
        class_name = self._first_or_create(Class, {"name": "TESTE1"})

        for student in (accounts["student"], accounts["student_two"]):
            UserClass.objects.get_or_create(
                user=student,
                class_name=class_name,
                year=today.year,
            )

        self._clear_stage_work(edition)
        if stage < 2:
            self._clear_stage_team(edition, accounts)

        team = None
        work = None
        collaborator_link = None

        if stage >= 2:
            team = self._create_team(edition, accounts)

        if stage >= 3:
            if team is None:
                team = self._create_team(edition, accounts)
            work = self._create_work(edition, team, accounts, field, theme, ods, stage)
            collaborator_link = self._create_collaborator_link(work, accounts["collaborator"], stage)

        if stage >= 5 and work:
            evaluator = accounts["evaluator"]
            work.evaluator.set([evaluator])

        if stage >= 6 and work:
            self._create_assessments(work, accounts)

        stage_info = STAGES[stage]
        route = stage_info.route.format(work_id=work.id if work else "")

        return {
            "stage": stage,
            "description": stage_info.label,
            "frontend_url": f"{settings.PAINEL_URL}{route}",
            "api_url": settings.API_URL,
            "login_as": stage_info.route_owner,
            "password": PASSWORD,
            "accounts": {
                key: {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                }
                for key, user in accounts.items()
                if isinstance(user, User)
            },
            "edition": {
                "id": edition.id,
                "year": edition.year,
                "name": edition.edition_name,
            },
            "team_id": team.id if team else None,
            "work": self._serialize_work(work, collaborator_link),
        }

    def _create_accounts(self) -> dict[str, Any]:
        users = {
            "student": self._upsert_user(
                "stage.student@ifc.local",
                "Aluno Stage",
                UserType.Type.STUDENT.value,
                990001,
            ),
            "student_two": self._upsert_user(
                "stage.student2@ifc.local",
                "Aluno Stage Dois",
                UserType.Type.STUDENT.value,
                990002,
            ),
            "advisor": self._upsert_user(
                "stage.advisor@ifc.local",
                "Orientador Stage",
                UserType.Type.TEACHER.value,
                990003,
                is_advisor=True,
            ),
            "collaborator": self._upsert_user(
                "stage.collaborator@ifc.local",
                "Colaborador Stage",
                UserType.Type.TEACHER.value,
                990004,
                is_collaborator=True,
            ),
            "evaluator_user": self._upsert_user(
                "stage.evaluator@ifc.local",
                "Avaliador Stage",
                UserType.Type.TEACHER.value,
                990005,
            ),
            "admin": self._upsert_user(
                "stage.admin@ifc.local",
                "Admin Stage",
                UserType.Type.ADMIN.value,
                990006,
                is_staff=True,
                is_superuser=True,
            ),
        }
        evaluator, _ = Evaluator.objects.get_or_create(user=users["evaluator_user"])
        users["evaluator"] = evaluator
        return users

    def _upsert_user(
        self,
        email: str,
        name: str,
        user_type: str,
        registration: int,
        **flags: Any,
    ) -> User:
        user, created = User.objects.get_or_create(email=email)
        user.name = name
        user.registration = self._registration_for(user, registration)
        user.user_type = user_type
        user.is_confirmed = True
        user.is_advisor = flags.pop("is_advisor", False)
        user.is_collaborator = flags.pop("is_collaborator", False)
        user.is_staff = flags.pop("is_staff", False)
        user.is_superuser = flags.pop("is_superuser", False)
        for key, value in flags.items():
            setattr(user, key, value)
        if created or not user.check_password(PASSWORD):
            user.set_password(PASSWORD)
        user.save()
        return user

    def _registration_for(self, user: User, preferred: int) -> int:
        registration = preferred
        while User.objects.filter(registration=registration).exclude(id=user.id).exists():
            registration += 100
        return registration

    def _create_edition(self, today):
        edition = Edition.objects.filter(
            year=today.year,
            edition_name=EDITION_NAME,
        ).first()
        if not edition:
            edition = Edition(
                year=today.year,
                edition_name=EDITION_NAME,
            )
        dates = {
            "event_date": today + timedelta(days=10),
            "final_event_date": today + timedelta(days=12),
            "initial_submission_date": today - timedelta(days=2),
            "final_submission_date": today + timedelta(days=2),
            "initial_second_submission_date": today + timedelta(days=3),
            "final_second_submission_date": today + timedelta(days=6),
            "initial_advisor_acceptance": today - timedelta(days=2),
            "final_advisor_acceptance": today + timedelta(days=3),
            "initial_second_advisor_date": today + timedelta(days=3),
            "final_second_advisor_date": today + timedelta(days=6),
            "initial_evaluators_date": today - timedelta(days=1),
            "final_evaluators_date": today + timedelta(days=20),
        }
        for attr, value in {
            "theme": "Fluxo guiado para testes manuais",
            "members_min": 2,
            "members_max": 4,
            "collaborators_min": 1,
            "collaborators_max": 2,
            "subjects_min": 1,
            "subjects_max": 3,
            "evaluators_count": 1,
            "works_per_evaluator_max": 5,
            "works_per_collaborator_max": 5,
            "works_per_advisor_max": 5,
            "words_per_work_min": 3,
            "words_per_work_max": 200,
            "workload": 10,
            **dates,
        }.items():
            setattr(edition, attr, value)
        edition.save()
        return edition

    def _clear_stage_work(self, edition: Edition) -> None:
        works = Work.objects.filter(edition=edition, title=WORK_TITLE)
        Assessment.objects.filter(work__in=works).delete()
        StudentAssessments.objects.filter(work__in=works).delete()
        WorkCollaborator.objects.filter(work__in=works).delete()
        works.delete()

    def _clear_stage_team(self, edition: Edition, accounts: dict[str, Any]) -> None:
        team_ids = list(
            Team.objects.filter(edition=edition, team_members=accounts["student"])
            .filter(team_members=accounts["student_two"])
            .distinct()
            .values_list("id", flat=True)
        )
        Team.objects.filter(id__in=team_ids).delete()

    def _create_team(self, edition: Edition, accounts: dict[str, Any]) -> Team:
        team = (
            Team.objects.filter(edition=edition, team_members=accounts["student"])
            .filter(team_members=accounts["student_two"])
            .distinct()
            .first()
        )
        if not team:
            team = Team.objects.create(edition=edition)
        team.team_members.set([accounts["student"], accounts["student_two"]])
        return team

    def _create_work(
        self,
        edition: Edition,
        team: Team,
        accounts: dict[str, Any],
        field: Field,
        theme: CrossCuttingTheme,
        ods: Ods,
        stage: int,
    ) -> Work:
        advisor_status = WorkAdvisorStatusType.Type.PENDING.value
        work_status = WorkStatusType.Type.PENDING.value
        if stage >= 4:
            advisor_status = WorkAdvisorStatusType.Type.APPROVED.value
            work_status = WorkStatusType.Type.APPROVED.value

        work = Work.objects.create(
            title=WORK_TITLE,
            abstract="Resumo de teste com palavras suficientes para navegar pelo fluxo guiado.",
            edition=edition,
            cross_cutting_theme=theme,
            team=team,
            advisor=accounts["advisor"],
            advisor_status=advisor_status,
            status=work_status,
            verification_token=ADVISOR_TOKEN,
            integrated_project=False,
        )
        work.field.set([field])
        work.ods.set([ods])
        return work

    def _create_collaborator_link(
        self,
        work: Work,
        collaborator: User,
        stage: int,
    ) -> WorkCollaborator:
        status = WorkCollaboratorStatusType.Type.PENDING.value
        if stage >= 5:
            status = WorkCollaboratorStatusType.Type.APPROVED.value

        return WorkCollaborator.objects.create(
            work=work,
            collaborator=collaborator,
            status=status,
            verification_token=COLLABORATOR_TOKEN,
        )

    def _create_assessments(self, work: Work, accounts: dict[str, Any]) -> None:
        Assessment.objects.create(
            work=work,
            evaluator=accounts["evaluator"],
            grade=Decimal("8.50"),
            date_time=timezone.now(),
            committee_feedback="Avaliacao criada pelo stage_data.",
        )
        for student, grade in (
            (accounts["student"], Decimal("9.00")),
            (accounts["student_two"], Decimal("8.75")),
        ):
            StudentAssessments.objects.create(
                work=work,
                student=student,
                grade=grade,
                date_time=timezone.now(),
            )

    def _serialize_work(
        self,
        work: Work | None,
        collaborator_link: WorkCollaborator | None,
    ) -> dict[str, Any] | None:
        if not work:
            return None
        return {
            "id": str(work.id),
            "title": work.title,
            "status": work.status,
            "advisor_status": work.advisor_status,
            "advisor_token": work.verification_token,
            "collaborator_status": collaborator_link.status if collaborator_link else None,
            "collaborator_token": collaborator_link.verification_token if collaborator_link else None,
        }

    def _first_or_create(
        self,
        model,
        lookup: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ):
        instance = model.objects.filter(**lookup).first()
        if not instance:
            instance = model(**lookup)
        for attr, value in (defaults or {}).items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def _print_summary(self, context: dict[str, Any]) -> None:
        self.stdout.write(self.style.SUCCESS(f"Stage {context['stage']} pronto."))
        self.stdout.write(context["description"])
        self.stdout.write("")
        self.stdout.write(f"URL sugerida: {context['frontend_url']}")
        self.stdout.write(f"Login recomendado: {context['login_as']}")
        self.stdout.write(f"Senha padrao: {context['password']}")
        self.stdout.write("")
        self.stdout.write("Contas:")
        for role, account in context["accounts"].items():
            self.stdout.write(f"  {role}: {account['email']}")
        if context["work"]:
            self.stdout.write("")
            self.stdout.write(f"Trabalho: {context['work']['id']}")
            self.stdout.write(f"Token orientador: {context['work']['advisor_token']}")
            self.stdout.write(f"Token colaborador: {context['work']['collaborator_token']}")
