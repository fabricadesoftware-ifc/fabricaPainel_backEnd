from django.db import models
from uuid import uuid4

from core.edition.infra.edition_django_app.models import Edition
from core.user.infra.user_django_app.models import User, Evaluator
from core.field.infra.field_django_app.models import Field
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
    
class Team(models.Model):
    team_members = models.ManyToManyField(User)

    def __str__(self) -> str:
        members = ", ".join([user.name if user.name else "Unknown" for user in self.team_members.all()])
        return f"Team Members: {members}"

class Ods(models.Model):
    name = models.CharField(max_length=255, verbose_name="Sustainable Goal")

    def __str__(self) -> str:
        return self.name

class Work(models.Model):
    id = models.UUIDField(primary_key=True, default = uuid4, editable=False)
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    edition = models.ForeignKey(Edition, on_delete=models.PROTECT)
    field = models.ManyToManyField(Field, default=None, blank=True)
    evaluator = models.ManyToManyField(Evaluator, related_name="evaluator", default=None, blank=True)
    cross_cutting_theme = models.ForeignKey(CrossCuttingTheme, on_delete=models.PROTECT)
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
        CANCELED = 3, "Cancelado"
    status = models.IntegerField(choices=WorkStatus.choices, default=WorkStatus.PENDING)

    def __str__(self) -> str:
        return f"{self.title} - {self.team} - {self.status}"

    class Meta:
        verbose_name = "Trabalho"
        verbose_name_plural = "Trabalhos"
        ordering = ["-title"]

class Keyword(models.Model):
    name = models.CharField(max_length=255)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Palavra-chave"
        verbose_name_plural = "Palavras-chave"
        ordering = ["-name"]
