from django.db import models

# This model is about Sustainable Goals
class Ods(models.Model):
    name = models.CharField(max_length=255, verbose_name="Sustainable Goal")

    def __str__(self) -> str:
        return self.name