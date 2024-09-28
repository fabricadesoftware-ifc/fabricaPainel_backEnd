from dataclasses import InitVar, dataclass, field
from enum import Enum
from typing import Literal, Union
from core.__seedwork.domain.utils.utils import Either
from core.__seedwork.domain.value_objects import ValueObject
from core.work.domain.exceptions import InvalidType

@dataclass(frozen=True, slots=True)
class WorkStatusType(ValueObject):
    value: "Type" = field(init=False)  # O valor imutável representando o status
    init_value: InitVar[Union["Type", str]]  # Aceita um tipo Type ou uma string na inicialização

    class Type(Enum):
        PENDING = (1, "Pendente")
        APPROVED = (2, "Aprovado")
        NEEDS_CHANGES = (3, "Pendente com Alterações")
        CANCELED = (4, "Cancelado")

        def __init__(self, value, label):
            self._value_ = value
            self.label = label

        @property
        def description(self):
            """Retorna a descrição legível do status."""
            return self.label

    TypeValues = Literal[1, 2, 3, 4]  # Limita os valores possíveis para o status

    def __post_init__(self, init_value: Union["Type", str]) -> None:
        """Valida e define o valor correto após a inicialização."""
        value = self.__validate(init_value)  # Valida o valor fornecido
        object.__setattr__(self, "value", value)  # Define o valor imutável

    def __validate(self, value: Union["Type", str]) -> "Type":
        """Valida se o valor é uma instância de Type ou uma string válida."""
        if isinstance(value, WorkStatusType.Type):
            return value
        try:
            # Tenta converter uma string ou número para o Enum Type
            return WorkStatusType.Type(value)  
        except ValueError as ex:
            raise InvalidType(value) from ex  # Lança uma exceção personalizada se o tipo for inválido

    @staticmethod
    def create(value: Union["Type", str]):
        """Método de fábrica que tenta criar uma instância de WorkStatusType de forma segura."""
        return Either.safe(lambda: WorkStatusType(value))
