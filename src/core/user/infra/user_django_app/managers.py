from typing import TYPE_CHECKING

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

from core.user.domain.value_objects import UserType

if TYPE_CHECKING:
    from .models import User


class CustomUserManager(BaseUserManager["User"]):
    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "User":
        if not email:
            raise ValueError(_("The Email must be set"))

        email = self.normalize_email(email)

        extra_fields.setdefault("user_type", UserType.Type.STUDENT.value)

        user = self.model(email=email, **extra_fields)

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        extra_fields.setdefault("user_type", UserType.Type.ADMIN.value)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(
            email,
            password,
            **extra_fields,
        )
