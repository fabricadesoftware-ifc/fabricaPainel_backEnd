from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from core.field.infra.field_django_app.models import Field
from core.user.domain.value_objects import UserType
from .managers import CustomUserManager
import unicodedata

def remove_accent(text):
    text_normal = unicodedata.normalize('NFKD', text)
    text_without_accent = ''.join(c for c in text_normal if not unicodedata.combining(c))
    return text_without_accent

class Class(models.Model):
    name = models.CharField(max_length=20, help_text="Exemplo: 1info1")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ["name"]
    


class User(AbstractUser):
    STUDENT = UserType.Type.STUDENT.value
    TEACHER = UserType.Type.TEACHER.value
    ADMIN = UserType.Type.ADMIN.value
    TAE = UserType.Type.TAE.value
    
    USER_TYPE_CHOICE = (
        (STUDENT, UserType.Type.STUDENT),
        (TEACHER, UserType.Type.TEACHER),
        (ADMIN, UserType.Type.ADMIN),
        (TAE, UserType.Type.TAE),
    )
    username = None
    email = models.EmailField(_("e-mail address"), unique=True)
    registration = models.IntegerField(null=True, unique=True)
    name = models.CharField(max_length=255, null=True)
    name_search = models.CharField(max_length=255, null=True)
    is_advisor = models.BooleanField(default=False, null=True, blank=True)
    is_collaborator = models.BooleanField(default=False, null=True, blank=True)
    password_reset_token = models.CharField(
        _("Password Reset Token"), max_length=255, blank=True, null=True
    )
    password_reset_token_created = models.DateTimeField(
        _("Password Reset Token Created"), blank=True, null=True
    )  
    field = models.ForeignKey(Field, on_delete=models.SET_NULL, null=True)
    user_type = models.CharField(max_length=10,choices=USER_TYPE_CHOICE, default=STUDENT)
    is_management = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['name']
    EMAIL_FIELD = "email"

    objects = CustomUserManager()

    def __str__(self):
        return self.email + " - " + (self.name or "No Name")

    def get_user_type_display(self):
        return dict(self.USER_TYPE_CHOICE).get(self.user_type, "Unknown")

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["-date_joined"]

class UserClass(models.Model):
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="user_classes", help_text="turma do aluno")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_classes")
    year = models.IntegerField("Ano da classe")
    
    def __str__(self):
        return f"{self.class_name.name} - {self.year}"

    class Meta:
        verbose_name = "Classe do Usuário"
        verbose_name_plural = "Classes dos Usuários"
        ordering = ["-user__date_joined"]

class Evaluator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="evaluator")

    def __str__(self):
        return self.user.name

    class Meta:
        verbose_name = "Avaliador"
        verbose_name_plural = "Avaliadores"
        ordering = ["-user__date_joined"]
        

