from django.db import models

from core.fabrica_painel.models.edition import Edition
from core.fabrica_painel.models.field import Field
from core.usuario.models import Usuario
from core.fabrica_painel.models.team import Team
from core.fabrica_painel.models.ods import Ods


class Work(models.Model):
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    edition = models.ForeignKey(Edition, on_delete=models.PROTECT)
    field = models.ManyToManyField(Field, default=None)
    advisor = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="advisor",
        limit_choices_to={"is_advisor": True},
    )
    initial_submission_work_date = models.DateTimeField(blank=True, null=True)
    final_submission_work_date = models.DateTimeField(blank=True, null=True)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    reject_submission_work_date = models.DateTimeField(blank=True, null=True)
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    ods = models.ManyToManyField(Ods, related_name="SustainableGoals", default=None) 
    class WorkStatus(models.IntegerChoices):
        PENDING = 0, "Pendente"
        APPROVED = 1, "Aprovado"
        REJECTED = 2, "Rejeitado"
    status = models.IntegerField(choices=WorkStatus.choices, default=WorkStatus.PENDING)

    def __str__(self) -> str:
        return f"{self.title} - {self.team} - {self.WorkStatus}"

    class Meta:
        verbose_name = "Trabalho"
        verbose_name_plural = "Trabalhos"
        ordering = ["-title"]
