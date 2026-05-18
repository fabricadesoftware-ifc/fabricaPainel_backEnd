from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments
from core.edition.infra.edition_django_app.models import Edition
from core.populate.infra.populate_django_app.management.commands.stage_data import EDITION_NAME, WORK_TITLE
from core.user.infra.user_django_app.models import User
from core.work.domain.value_objects import (
    WorkAdvisorStatusType,
    WorkCollaboratorStatusType,
    WorkStatusType,
)
from core.work.infra.work_django_app.models import Team, Work


@override_settings(
    DEBUG=True,
    PAINEL_URL="http://localhost:3000",
    API_URL="http://localhost:8000",
)
class StageDataCommandTest(TestCase):
    def test_stage_zero_keeps_only_users_for_edition_creation(self):
        call_command("stage_data", stage=4, quiet=True)
        self.assertTrue(Edition.objects.filter(edition_name=EDITION_NAME).exists())
        self.assertTrue(Work.objects.filter(title=WORK_TITLE).exists())

        call_command("stage_data", stage=0, quiet=True)

        self.assertFalse(Edition.objects.filter(edition_name=EDITION_NAME).exists())
        self.assertFalse(Work.objects.filter(title=WORK_TITLE).exists())
        self.assertEqual(Team.objects.count(), 0)
        self.assertTrue(User.objects.filter(email="stage.admin@ifc.local").exists())

    def test_stage_four_prepares_approved_work_with_pending_collaborator(self):
        call_command("stage_data", stage=4, quiet=True)

        work = Work.objects.get(title=WORK_TITLE)
        collaborator_link = work.work_collaborator.get()

        self.assertEqual(work.status, WorkStatusType.Type.APPROVED.value)
        self.assertEqual(work.advisor_status, WorkAdvisorStatusType.Type.APPROVED.value)
        self.assertEqual(collaborator_link.status, WorkCollaboratorStatusType.Type.PENDING.value)
        self.assertEqual(work.evaluator.count(), 0)
        self.assertLessEqual(work.edition.initial_submission_date, timezone.localdate())
        self.assertGreaterEqual(work.edition.final_submission_date, timezone.localdate())

    def test_stage_three_after_stage_six_rewinds_owned_work_state(self):
        call_command("stage_data", stage=6, quiet=True)
        self.assertEqual(Assessment.objects.count(), 1)
        self.assertEqual(StudentAssessments.objects.count(), 2)

        call_command("stage_data", stage=3, quiet=True)

        work = Work.objects.get(title=WORK_TITLE)
        collaborator_link = work.work_collaborator.get()

        self.assertEqual(work.status, WorkStatusType.Type.PENDING.value)
        self.assertEqual(work.advisor_status, WorkAdvisorStatusType.Type.PENDING.value)
        self.assertEqual(collaborator_link.status, WorkCollaboratorStatusType.Type.PENDING.value)
        self.assertEqual(work.evaluator.count(), 0)
        self.assertEqual(Assessment.objects.count(), 0)
        self.assertEqual(StudentAssessments.objects.count(), 0)

    def test_stage_one_keeps_only_base_data_for_guided_scenario(self):
        call_command("stage_data", stage=4, quiet=True)
        self.assertTrue(Work.objects.filter(title=WORK_TITLE).exists())

        call_command("stage_data", stage=1, quiet=True)

        self.assertFalse(Work.objects.filter(title=WORK_TITLE).exists())
        self.assertEqual(Team.objects.count(), 0)
