from dataclasses import InitVar, dataclass, field
from django.utils.translation import gettext_lazy as _  
from enum import Enum
from typing import Union
from core.__seedwork.domain.utils.utils import Either
from core.__seedwork.domain.value_objects import ValueObject
from core.work.domain.exceptions import InvalidType

@dataclass(frozen=True, slots=True)
class UserType(ValueObject):
    value: "UserType.Type" = field(init=False)
    init_value: InitVar[Union["UserType.Type", str]]

    class Type(str, Enum):
        STUDENT = "STUDENT"
        TEACHER = "TEACHER"
        ADMIN = "ADMIN"
        TAE = "TAE"

        def __init__(self, value):
            self._value_ = value

        @property
        def description(self):
            labels = {
                "STUDENT": _("Student"),
                "TEACHER": _("Teacher"),
                "ADMIN": _("Admin"),
                "TAE": _("TAE"),
            }
            return labels.get(self._value_, "Unknown")

    def __post_init__(self, init_value: Union["Type", str]) -> None:
        value = self.__validate(init_value)
        object.__setattr__(self, "value", value)

    def __validate(self, value: Union["Type", str]) -> "Type":
        if isinstance(value, UserType.Type):
            return value
        try:
            return UserType.Type(value)
        except ValueError as ex:
            raise InvalidType(value) from ex

    @staticmethod
    def create(value: Union["Type", str]):
        return Either.safe(lambda: UserType(value))
