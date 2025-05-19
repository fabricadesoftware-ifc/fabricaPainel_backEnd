from django.db import models
from core.uploader.infra.uploader_django_app.models import Image
from datetime import datetime, timedelta, date

class Edition(models.Model):
    year = models.IntegerField("Ano da Edição")
    theme = models.CharField("Tema da Edição", max_length=255)
    edition_name = models.CharField("Nome da Edição", max_length=255)
    event_date = models.DateField("Data do evento", default=None, null=True, blank=True)
    final_event_date = models.DateField("Data final do evento", default=None, null=True, blank=True)

    initial_submission_date = models.DateField("Data de início de submissão", default=None, null=True, blank=True)
    final_submission_date = models.DateField("Data de fim de submissão", default=None, null=True, blank=True)
    initial_second_submission_date = models.DateField("Data de início da segunda submissão", default=None, null=True, blank=True)
    final_second_submission_date = models.DateField("Data de fim da segunda submissão", default=None, null=True, blank=True)

    initial_advisor_acceptance = models.DateField("Data de início de aceitação de orientadores", default=None, null=True, blank=True)
    final_advisor_acceptance = models.DateField("Data de fim de aceitação de orientadores", default=None, null=True, blank=True)
    initial_second_advisor_date = models.DateField("Data de início da segunda aceitação de orientadores", default=None, null=True, blank=True)
    final_second_advisor_date = models.DateField("Data de fim da segunda aceitação de orientadores", default=None, null=True, blank=True)

    initial_evaluators_date = models.DateField("Data de início para avaliadores", default=None, null=True, blank=True)
    final_evaluators_date = models.DateField("Data de fim para avaliadores", default=None, null=True, blank=True)

    members_min = models.IntegerField("Número mínimo de membros", default=5)
    members_max = models.IntegerField("Número máximo de membros", default=7)
    collaborators_min = models.IntegerField("Número mínimo de colaboradores", default=1)
    collaborators_max = models.IntegerField("Número máximo de colaboradores", default=2)
    subjects_min = models.IntegerField("Número mínimo de disciplinas", default=3)
    subjects_max = models.IntegerField("Número máximo de disciplinas", default=7)
    evaluators_count = models.IntegerField("Número de avaliadores", default=2)
    works_per_evaluator_max = models.IntegerField("Número máximo de trabalhos por avaliador", default=3)
    works_per_collaborator_max = models.IntegerField("Número máximo de trabalhos por colaborador", default=3)
    works_per_advisor_max = models.IntegerField("Número máximo de trabalhos por orientador", default=3)

    workload = models.IntegerField("Carga horária")
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
    def is_open(self):
        today = datetime.now().date()
        print(today)
        if not self.initial_submission_date or not self.final_event_date:
            return False
        return self.initial_submission_date <= today <= (self.final_event_date + timedelta(days=1))

    def __str__(self):
        return f"{self.edition_name} - {self.year}"