from decimal import Decimal

from django.core import mail
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments
from core.user.domain.value_objects import UserType
from core.work.domain.grade_reminders import collect_pending_grades, send_grade_reminders
from core.work.domain.value_objects import WorkStatusType
from core.work.infra.work_django_app.tests.test_admin_grading_overview import (
    AdminGradingOverviewApiTest,
)


class GradeRemindersTest(AdminGradingOverviewApiTest):
    """Reaproveita o setup (edicao, orientador, avaliador) do teste da visao de notas."""

    def grade_work(self, work):
        Assessment.objects.create(
            work=work,
            evaluator=self.evaluator,
            grade=Decimal("8.00"),
            date_time=timezone.now(),
        )

    def grade_student(self, work, student):
        StudentAssessments.objects.create(
            work=work, student=student, grade=Decimal("7.00"), date_time=timezone.now()
        )

    def test_quem_deve_nota_aparece_para_os_dois_papeis(self):
        work = self.create_work("Trabalho Pendente")

        pending = collect_pending_grades(self.edition)

        self.assertEqual(list(pending["advisors"].keys()), [self.advisor])
        self.assertEqual(pending["advisors"][self.advisor][0]["work"].id, work.id)
        self.assertEqual(pending["advisors"][self.advisor][0]["students"], [self.student])
        self.assertEqual(list(pending["evaluators"].keys()), [self.evaluator_user])

    def test_quem_ja_deu_nota_nao_recebe(self):
        work = self.create_work("Trabalho Completo")
        self.grade_student(work, self.student)
        self.grade_work(work)

        pending = collect_pending_grades(self.edition)

        self.assertEqual(len(pending["advisors"]), 0)
        self.assertEqual(len(pending["evaluators"]), 0)

    def test_so_orientador_pendente_nao_cobra_avaliador(self):
        work = self.create_work("So Avaliador Deu")
        self.grade_work(work)

        pending = collect_pending_grades(self.edition)

        self.assertEqual(len(pending["advisors"]), 1)
        self.assertEqual(len(pending["evaluators"]), 0)

    def test_trabalho_nao_aprovado_nao_entra(self):
        self.create_work("Rejeitado", status_value=WorkStatusType.Type.REJECTED.value)

        pending = collect_pending_grades(self.edition)

        self.assertEqual(len(pending["advisors"]), 0)
        self.assertEqual(len(pending["evaluators"]), 0)

    def test_envio_manda_um_email_por_pessoa_e_lista_trabalhos(self):
        self.create_work("Trabalho A")
        other_student = self.create_user("student2.grading@test.local", UserType.Type.STUDENT.value)
        self.create_work("Trabalho B", student=other_student)

        summary = send_grade_reminders(self.edition)

        self.assertEqual(summary["emails_sent"], 2)  # 1 orientador + 1 avaliador
        self.assertEqual(summary["failed"], 0)
        by_recipient = {message.to[0]: message for message in mail.outbox}
        self.assertIn("Trabalho A", by_recipient[self.advisor.email].body)
        self.assertIn("Trabalho B", by_recipient[self.advisor.email].body)
        self.assertIn("Trabalho A", by_recipient[self.evaluator_user.email].body)

    def test_dry_run_nao_envia(self):
        self.create_work("Trabalho A")

        summary = send_grade_reminders(self.edition, dry_run=True)

        self.assertEqual(summary["advisors"], 1)
        self.assertEqual(summary["evaluators"], 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_endpoint_so_para_admin_ou_gestao(self):
        self.create_work("Trabalho A")
        url = "/api/work/send-grade-reminders/"

        self.client.force_authenticate(self.teacher)
        self.assertEqual(self.client.post(url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.manager)
        response = self.client.post(url, {"edition": self.edition.id, "dry_run": True}, format="json")
        # edition vem por query (?edition=), como nas outras acoes; sem ela usa a padrao.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["advisors"], 1)
        self.assertEqual(len(mail.outbox), 0)

        self.client.force_authenticate(self.admin)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["emails_sent"], 2)
