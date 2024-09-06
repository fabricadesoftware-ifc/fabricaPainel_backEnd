from django.db import models
from core.user.infra.user_django_app.models import User

class CrossCuttingTheme(models.Model):
    name = models.CharField(max_length=255, unique=True)
    advisor = models.ManyToManyField(
        User,
        limit_choices_to={"is_advisor": True},
        related_name="advisor",
        blank=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cross Cutting Theme"
        verbose_name_plural = "Cross Cutting Themes"