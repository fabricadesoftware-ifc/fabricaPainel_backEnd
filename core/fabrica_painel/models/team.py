from django.db import models


from core.usuario.models import Usuario


class Team(models.Model):
    team_student = models.ForeignKey(
        Usuario,
        related_name="teams",
        limit_choices_to={'user_type': Usuario.UserType.STUDENT},
        on_delete=models.PROTECT)
    

    def __str__(self) -> str:
        return f"{self.team_student}"