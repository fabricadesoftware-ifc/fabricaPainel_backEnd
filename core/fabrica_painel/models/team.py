from core.fabrica_painel.models.work import Work
from django.db import models

from core.usuario.models import Usuario


class Team(models.Model):
    team_student = models.ForeignKey(
        Usuario,
        related_name="teams",
        limit_choices_to={'user_type': Usuario.UserType},
        on_delete=models.PROTECT)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)
