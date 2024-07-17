from django.db import models
from core.uploader.models import Image

class Edition(models.Model):
    year = models.IntegerField()
    theme = models.CharField(max_length=255)
    edition_name = models.CharField(max_length=255)
    initil_submission_date = models.DateTimeField("Data de início de submissão")
    final_submission_date = models.DateTimeField("Data de fim de submissão")
    initial_advisor_date = models.DateTimeField("Data de início de orientação")
    final_advisor_date = models.DateTimeField("Data de fim de orientação")
    initial_evaluators_date = models.DateTimeField("Data de início para avaliadores")
    final_evaluators_date = models.DateTimeField("Data de fim para avaliadores")
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

    def __str__(self):
        return self.edition_name