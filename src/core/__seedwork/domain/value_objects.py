from abc import ABC
from dataclasses import dataclass, fields
import json


@dataclass(frozen=True)
class ValueObject(ABC):
    def __str__(self) -> str:
        fields_name = [field.name for field in fields(self)]
        return (
            str(getattr(self, fields_name[0]))
            if len(fields_name) == 1
            else json.dumps(
                {field_name: getattr(self, field_name) for field_name in fields_name}
            )
        )