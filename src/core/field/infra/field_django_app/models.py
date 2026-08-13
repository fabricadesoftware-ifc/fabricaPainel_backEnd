from django.db import models
from typing import TYPE_CHECKING

class Field(models.Model):
    if TYPE_CHECKING:
        id: int

    name = models.CharField(max_length=255)
    
    
    def __str__(self):
        return self.name

