from django.test import TestCase, override_settings
from django.core import mail
from datetime import date, timedelta

from core.edition.infra.edition_django_app.models import Edition
from core.user.infra.user_django_app.models import User
from core.field.infra.field_django_app.models import Field
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import (
    CrossCuttingTheme,
)
from core.work.infra.work_django_app.models import Team, Work

from core.work.domain.tasks.send_email_advisor.send_grade_period_opened import (
    notify_advisors_grade_period_opened,
)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class GradePeriodNotificationTest(TestCase):
    def setUp(self):
        # Datas: hoje e daqui a 2 dias
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=2)

        # Edition
        self.edition = Edition.objects.create(
            year=self.today.year,
            theme="Teste",
            edition_name="Edição Teste",
            initial_evaluators_date=self.today,
            final_evaluators_date=self.tomorrow,
            workload=10,
        )

        # Field e tema transversal
        self.field = Field.objects.create(name="Computação")
        self.theme = CrossCuttingTheme.objects.create(name="Sustentabilidade")

        # Advisors
        self.advisor1 = User.objects.create_user(
            email="advisor1@test.local",
            password="test-password-123",
            name="Advisor 1",
            is_advisor=True,
            user_type=User.TEACHER,
        )
        self.advisor2 = User.objects.create_user(
            email="advisor2@test.local",
            password="test-password-123",
            name="Advisor 2",
            is_advisor=True,
            user_type=User.TEACHER,
        )

        # Team e estudantes
        self.student = User.objects.create_user(
            email="student@test.local",
            password="test-password-123",
            name="Aluno Teste",
        )
        self.team1 = Team.objects.create(edition=self.edition)
        self.team1.team_members.add(self.student)

        self.team2 = Team.objects.create(edition=self.edition)
        self.team2.team_members.add(self.student)

        # Works
        self.work1 = Work.objects.create(
            title="Trabalho A",
            abstract="Resumo A",
            edition=self.edition,
            cross_cutting_theme=self.theme,
            team=self.team1,
            advisor=self.advisor1,
        )
        self.work1.field.add(self.field)

        self.work2 = Work.objects.create(
            title="Trabalho B",
            abstract="Resumo B",
            edition=self.edition,
            cross_cutting_theme=self.theme,
            team=self.team2,
            advisor=self.advisor2,
        )
        self.work2.field.add(self.field)

    def test_notify_advisors_sends_one_email_per_advisor_with_correct_content(self):
        # Executa a lógica de notificação sincronamente
        # Chamamos .run() da task para garantir execução imediata
        notify_advisors_grade_period_opened.run()

        # Devem ter sido enviados 2 emails (um por orientador)
        self.assertEqual(len(mail.outbox), 2)

        # Verifica conteúdo do primeiro email contém título do trabalho correspondente
        bodies = [
            m.body + (m.alternatives[0][0] if m.alternatives else "")
            for m in mail.outbox
        ]
        content = "\n\n".join(bodies)

        self.assertIn("Trabalho A", content)
        self.assertIn("Trabalho B", content)
