from typing import Any


class InvalidType(Exception):
    def __init__(self, invalid_type: Any) -> None:
        self.status: Any = invalid_type
        self.message = f"Invalid work type: {invalid_type}"
        super().__init__(self.message)