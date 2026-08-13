from django.db import models
from core.uploader.infra.uploader_django_app.models import Image
from datetime import datetime
from typing import TYPE_CHECKING

from core.edition.infra.edition_django_app.defaults import default_evaluation_criteria


class Edition(models.Model):
    if TYPE_CHECKING:
        id: int
        banner_id: int | None
        logo_id: int | None

    year = models.IntegerField("Ano da Edição")
    theme = models.CharField("Tema da Edição", max_length=255)
    edition_name = models.CharField("Nome da Edição", max_length=255)
    event_date = models.DateField("Data do evento", default=None, null=True, blank=True)
    final_event_date = models.DateField(
        "Data final do evento", default=None, null=True, blank=True
    )

    initial_submission_date = models.DateField(
        "Data de início de submissão", default=None, null=True, blank=True
    )
    final_submission_date = models.DateField(
        "Data de fim de submissão", default=None, null=True, blank=True
    )
    initial_second_submission_date = models.DateField(
        "Data de início da segunda submissão", default=None, null=True, blank=True
    )
    final_second_submission_date = models.DateField(
        "Data de fim da segunda submissão", default=None, null=True, blank=True
    )

    initial_advisor_acceptance = models.DateField(
        "Data de início de aceitação de orientadores",
        default=None,
        null=True,
        blank=True,
    )
    final_advisor_acceptance = models.DateField(
        "Data de fim de aceitação de orientadores", default=None, null=True, blank=True
    )
    initial_second_advisor_date = models.DateField(
        "Data de início da segunda aceitação de orientadores",
        default=None,
        null=True,
        blank=True,
    )
    final_second_advisor_date = models.DateField(
        "Data de fim da segunda aceitação de orientadores",
        default=None,
        null=True,
        blank=True,
    )

    initial_evaluators_date = models.DateField(
        "Data de início para avaliadores", default=None, null=True, blank=True
    )
    final_evaluators_date = models.DateField(
        "Data de fim para avaliadores", default=None, null=True, blank=True
    )

    members_min = models.IntegerField("Número mínimo de membros", default=5)
    members_max = models.IntegerField("Número máximo de membros", default=7)
    collaborators_min = models.IntegerField("Número mínimo de colaboradores", default=1)
    collaborators_max = models.IntegerField("Número máximo de colaboradores", default=2)
    subjects_min = models.IntegerField("Número mínimo de disciplinas", default=3)
    subjects_max = models.IntegerField("Número máximo de disciplinas", default=7)
    evaluators_count = models.IntegerField("Número de avaliadores", default=2)
    works_per_evaluator_max = models.IntegerField(
        "Número máximo de trabalhos por avaliador", default=3
    )
    works_per_collaborator_max = models.IntegerField(
        "Número máximo de trabalhos por colaborador", default=3
    )
    works_per_advisor_max = models.IntegerField(
        "Número máximo de trabalhos por orientador", default=3
    )
    words_per_work_min = models.IntegerField(
        "Número mínimo de palavras por trabalho", default=200
    )
    words_per_work_max = models.IntegerField(
        "Número máximo de palavras por trabalho", default=500
    )

    workload = models.IntegerField("Carga horária")

    evaluation_criteria = models.JSONField(
        "Criterios de avaliacao",
        default=default_evaluation_criteria,
        blank=True,
    )

    banner = models.ForeignKey(
        Image,
        related_name="+",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )
    logo = models.ForeignKey(
        Image,
        related_name="+",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )

    @property
    def is_active(self) -> bool:
        today = datetime.now().date()
        if not self.initial_submission_date or not self.final_event_date:
            return False
        return self.initial_submission_date <= today <= self.final_evaluators_date

    @property
    def is_open_for_submissions(self) -> bool:
        today = datetime.now().date()
        if (
            not self.initial_submission_date
            or not self.final_submission_date
            or not self.initial_second_submission_date
            or not self.final_second_submission_date
        ):
            return False
        return (
            self.initial_submission_date <= today <= self.final_submission_date
        ) or (
            self.initial_second_submission_date
            <= today
            <= self.final_second_submission_date
        )

    @property
    def is_open_for_advisors(self) -> bool:
        today = datetime.now().date()
        if (
            not self.initial_advisor_acceptance
            or not self.final_advisor_acceptance
            or not self.initial_second_advisor_date
            or not self.final_second_advisor_date
        ):
            return False
        return (
            self.initial_advisor_acceptance <= today <= self.final_advisor_acceptance
        ) or (
            self.initial_second_advisor_date <= today <= self.final_second_advisor_date
        )

    @property
    def is_open_for_evaluators(self) -> bool:
        today = datetime.now().date()
        if (
            not self.initial_evaluators_date
            or not self.final_evaluators_date
            or not self.event_date
        ):
            return False
        return (
            self.initial_evaluators_date <= today <= self.final_evaluators_date
        ) and (self.initial_evaluators_date >= self.event_date)

    @property
    def is_edition_running(self) -> bool:
        today = datetime.now().date()
        if not self.event_date or not self.final_event_date:
            return False
        return self.event_date <= today <= self.final_event_date

    def __str__(self) -> str:
        return f"{self.edition_name} - {self.year}"
