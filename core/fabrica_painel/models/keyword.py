from django.db import models

from core.fabrica_painel.models.work import Work


class Keyword(models.Model):
    name = models.CharField(max_length=255)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Palavra-chave"
        verbose_name_plural = "Palavras-chave"
        ordering = ["-name"]
