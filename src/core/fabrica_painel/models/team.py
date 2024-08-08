from django.db import models


from core.user.models import User


class Team(models.Model):
    team_members = models.ManyToManyField(User)
    

    def __str__(self) -> str:
        return f"{self.team_members}"