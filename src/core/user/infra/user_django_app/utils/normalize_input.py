from typing import Any, Optional


def normalize_reset_token(value: Any) -> str:
    """
    Código de recuperação como o usuário digitou: teclado de celular e "colar" do
    e-mail deixam espaço sobrando e põem a primeira letra em maiúscula. O token é
    gerado em minúsculas (secrets.token_hex), então comparar assim é seguro.
    """
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def normalize_email_input(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def find_user_by_email(user_model: Any, email: str) -> Optional[Any]:
    """Acha por e-mail exato e, se não achar, ignorando maiúsculas (emails são salvos em minúsculas)."""
    if not email:
        return None
    return (
        user_model.objects.filter(email=email).first()
        or user_model.objects.filter(email__iexact=email).first()
    )
