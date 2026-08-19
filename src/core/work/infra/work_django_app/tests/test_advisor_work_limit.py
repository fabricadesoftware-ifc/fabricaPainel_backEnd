"""
Cobre o limite de orientações por edição (Edition.works_per_advisor_max).

O limite era conferido apenas no front, na hora de escolher o orientador, e
contando somente os aceites já confirmados. Enquanto o professor não respondia
nada ele aparecia com todas as vagas livres, então várias equipes conseguiam
convidá-lo e ele aceitava todas — furando o limite da edição.
"""

import uuid
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.edition.infra.edition_django_app.models import Edition
from core.field.infra.field_django_app.models import Field
from core.user.domain.value_objects import UserType
from core.user.infra.user_django_app.models import User
from core.work.domain.value_objects import WorkAdvisorStatusType, WorkStatusType
from core.work.infra.work_django_app.models import Ods, Team, Work


class AdvisorWorkLimitTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localdate()
        self.registration = 5000

        self.field = Field.objects.create(name="Informatica")
        self.theme = CrossCuttingTheme.objects.create(name="Sustentabilidade")
        self.ods = Ods.objects.create(name="ODS 4 - Educacao de Qualidade")

        self.advisor = self.create_user(
            "advisor-limit@test.local",
            UserType.Type.TEACHER.value,
            is_advisor=True,
        )
        self.edition = self.create_edition(works_per_advisor_max=3)

    def create_user(self, email, user_type, **flags):
        self.registration += 1
        user = User.objects.create_user(
            email=email,
            password="test-password-123",
            name=email.split("@")[0],
            registration=self.registration,
        )
        user.user_type = user_type
        for field, value in flags.items():
            setattr(user, field, value)
        user.save()
        return user

    def create_edition(self, *, works_per_advisor_max):
        return Edition.objects.create(
            year=self.today.year,
            theme="Tema de Teste",
            edition_name="Edicao Limite",
            event_date=self.today,
            final_event_date=self.today + timedelta(days=10),
            initial_submission_date=self.today - timedelta(days=1),
            final_submission_date=self.today + timedelta(days=1),
            initial_second_submission_date=self.today + timedelta(days=3),
            final_second_submission_date=self.today + timedelta(days=4),
            # Janela de decisão do orientador aberta hoje: os testes abaixo isolam
            # o limite, então a data nunca pode ser o motivo da recusa.
            initial_advisor_acceptance=self.today - timedelta(days=1),
            final_advisor_acceptance=self.today + timedelta(days=2),
            initial_second_advisor_date=self.today + timedelta(days=3),
            final_second_advisor_date=self.today + timedelta(days=5),
            initial_evaluators_date=self.today - timedelta(days=1),
            final_evaluators_date=self.today + timedelta(days=20),
            members_min=1,
            members_max=4,
            collaborators_min=0,
            collaborators_max=2,
            subjects_min=1,
            subjects_max=3,
            evaluators_count=1,
            works_per_evaluator_max=3,
            works_per_collaborator_max=3,
            works_per_advisor_max=works_per_advisor_max,
            words_per_work_min=3,
            words_per_work_max=200,
            workload=10,
        )

    def create_work(self, title, *, advisor_status, work_status=None):
        team = Team.objects.create(edition=self.edition)
        work = Work.objects.create(
            title=title,
            abstract="Resumo com conteudo suficiente para o teste de limite.",
            edition=self.edition,
            cross_cutting_theme=self.theme,
            team=team,
            advisor=self.advisor,
            advisor_status=advisor_status,
            status=work_status or WorkStatusType.Type.PENDING.value,
            verification_token=str(uuid.uuid4()),
            integrated_project=False,
        )
        work.field.set([self.field])
        work.ods.set([self.ods])
        return work

    def accept(self, work):
        self.client.force_authenticate(self.advisor)
        return self.client.get(f"/api/accept-advisor-work/{work.verification_token}/")

    def test_rejects_acceptance_when_advisor_limit_is_reached(self):
        for index in range(3):
            self.create_work(
                f"Aceito {index}",
                advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            )
        fourth = self.create_work(
            "Quarto Trabalho",
            advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
        )

        response = self.accept(fourth)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("limite de 3", response.data["error"])

        fourth.refresh_from_db()
        self.assertEqual(fourth.advisor_status, WorkAdvisorStatusType.Type.PENDING.value)

    @patch("core.work.infra.work_django_app.views.accept_advisor_work.send_work_approve_email_to_student.delay")
    def test_allows_acceptance_below_the_limit(self, accept_email_delay):
        for index in range(2):
            self.create_work(
                f"Aceito {index}",
                advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            )
        third = self.create_work(
            "Terceiro Trabalho",
            advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
        )

        response = self.accept(third)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        third.refresh_from_db()
        self.assertEqual(third.advisor_status, WorkAdvisorStatusType.Type.APPROVED.value)

    @patch("core.work.infra.work_django_app.views.accept_advisor_work.send_work_approve_email_to_student.delay")
    def test_pending_invitations_do_not_consume_the_limit(self, accept_email_delay):
        # Vários convites pendentes não podem travar a vaga: enquanto o professor
        # não responde, ele continua disponível.
        for index in range(5):
            self.create_work(
                f"Pendente {index}",
                advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
            )
        work = self.create_work(
            "Mais um convite",
            advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
        )

        response = self.accept(work)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    @patch("core.work.infra.work_django_app.views.accept_advisor_work.send_work_approve_email_to_student.delay")
    def test_rejected_and_expired_works_do_not_consume_the_limit(self, accept_email_delay):
        # Recusas do orientador e trabalhos rejeitados devolvem a vaga.
        self.create_work(
            "Recusado pelo orientador",
            advisor_status=WorkAdvisorStatusType.Type.REJECTED.value,
        )
        self.create_work(
            "Trabalho rejeitado",
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            work_status=WorkStatusType.Type.REJECTED.value,
        )
        self.create_work(
            "Trabalho expirado",
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            work_status=WorkStatusType.Type.EXPIRED.value,
        )
        work = self.create_work(
            "Novo convite",
            advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
        )

        response = self.accept(work)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    @patch("core.work.infra.work_django_app.views.accept_advisor_work.send_work_approve_email_to_student.delay")
    def test_reaccepting_the_same_work_does_not_count_itself(self, accept_email_delay):
        # O próprio trabalho é excluído da contagem, senão um reenvio do link viraria
        # um falso "limite atingido".
        for index in range(2):
            self.create_work(
                f"Aceito {index}",
                advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            )
        work = self.create_work(
            "Ja aceito",
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
        )

        response = self.accept(work)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def limit_status(self, work, as_user=None):
        self.client.force_authenticate(as_user or self.advisor)
        return self.client.get(f"/api/advisor-work-limit/{work.verification_token}/")

    def test_limit_status_reports_limit_reached(self):
        for index in range(3):
            self.create_work(
                f"Aceito {index}",
                advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            )
        fourth = self.create_work(
            "Quarto Trabalho",
            advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
        )

        response = self.limit_status(fourth)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data["limit_reached"])
        self.assertEqual(response.data["limit"], 3)
        self.assertEqual(response.data["accepted_works"], 3)
        self.assertEqual(response.data["remaining"], 0)
        self.assertTrue(response.data["within_decision_window"])

    def test_limit_status_reports_remaining_slots(self):
        self.create_work(
            "Aceito",
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
        )
        work = self.create_work(
            "Convite",
            advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
        )

        response = self.limit_status(work)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertFalse(response.data["limit_reached"])
        self.assertEqual(response.data["remaining"], 2)

    def test_limit_status_denies_advisor_of_another_work(self):
        # IsAdvisor só garante que o usuário é *algum* orientador, então o endpoint
        # precisa conferir que é o orientador *deste* trabalho.
        other_advisor = self.create_user(
            "outro-advisor@test.local",
            UserType.Type.TEACHER.value,
            is_advisor=True,
        )
        work = self.create_work(
            "Convite",
            advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
        )

        response = self.limit_status(work, as_user=other_advisor)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
