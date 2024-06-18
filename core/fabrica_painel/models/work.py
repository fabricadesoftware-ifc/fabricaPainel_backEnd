from django.db import models
from django.utils import timezone

from core.fabrica_painel.models.edition import Edition
from core.fabrica_painel.models.field import Field
from core.usuario.models import Usuario


class Work(models.Model):
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    edition = models.ForeignKey(
        Edition,
        on_delete=models.PROTECT
    )
    field = models.ForeignKey(
        Field,
        on_delete=models.PROTECT
    )
    advisor = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="advisor"
    )
    initial_submission_work_date = models.DateTimeField(default=timezone.now)
    final_submission_work_date = models.DateTimeField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Trabalho"
        verbose_name_plural = "Trabalhos"
        ordering = ["-title"]
