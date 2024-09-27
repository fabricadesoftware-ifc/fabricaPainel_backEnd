from typing import Callable, Tuple, TypeVar

Ok = TypeVar("Ok")
Error = TypeVar("Error")


class Either(Tuple[Ok, Error]):
    def __new__(cls, ok: Ok, error: Error):
        return super().__new__(cls, (ok, error))

    @staticmethod
    def ok(ok: Ok) -> "Either[Ok, None]":
        return Either(ok, None)

    @staticmethod
    def fail(error: Error) -> "Either[None, Error]":
        return Either(None, error)

    @staticmethod
    def safe(fn: Callable[[], Ok]) -> "Either[Ok, Exception]":
        try:
            return Either.ok(fn())
        except Exception as ex:
            return Either.fail(ex)