from django.db import models
from typing import TYPE_CHECKING
from core.user.infra.user_django_app.models import User

class CrossCuttingTheme(models.Model):
    if TYPE_CHECKING:
        id: int

    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    advisor = models.ManyToManyField(
        User,
        limit_choices_to={"is_advisor": True},
        blank=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cross Cutting Theme"
        verbose_name_plural = "Cross Cutting Themes"
