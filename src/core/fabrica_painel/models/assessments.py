from django.db import models
from core.user.models import User
from core.fabrica_painel.models.work import Work

class Assessments(models.Model):
    registration =  models.ForeignKey(User,
        related_name="assessments",
        on_delete=models.PROTECT)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.registration} - {self.work}"