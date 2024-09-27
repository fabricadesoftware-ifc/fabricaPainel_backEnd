from dataclasses import InitVar, dataclass, field
from enum import Enum
from typing import Literal, Union
from core.__seedwork.domain.utils.utils import Either
from core.__seedwork.domain.value_objects import ValueObject
from core.work.domain.exceptions import InvalidType

@dataclass(frozen=True, slots=True)
class WorkStatusType(ValueObject):
    value: "Type" = field(init=False)
    init_value: InitVar[Union["Type", str]]

    class Type(Enum):
        PENDING = (1, "Pendente")
        APPROVED = (2, "Aprovado")
        REJECTED = (3, "Rejeitado")
        CANCELED = (4, "Cancelado")

     
        def __init__(self, value, label):
            self._value_ = value
            self.label = label

        @property
        def description(self):
            return self.label

    TypeValues = Literal[1, 2, 3, 4]

    def __post_init__(self, init_value: Union["Type", str]) -> None:
        value = self.__validate(init_value) 
        object.__setattr__(self, "value", value)

    def __validate(self, value: Union["Type", str]) -> "Type":
        if isinstance(value, WorkStatusType.Type):
            return value
        try:
            return WorkStatusType.Type(value)  
        except ValueError as ex:
            raise InvalidType(value) from ex 

    @staticmethod
    def create(value: Union["Type", str]):
        
        return Either.safe(lambda: WorkStatusType(value))
