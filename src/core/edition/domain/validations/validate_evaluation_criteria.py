from decimal import Decimal, InvalidOperation
from typing import Any

from core.edition.infra.edition_django_app.defaults import default_evaluation_criteria


VALID_TARGETS = {"work", "student"}


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError("O peso do criterio deve ser numerico.") from error


def _validate_weight(value: Any, message: str) -> Decimal:
    weight = _to_decimal(value)
    if weight <= 0:
        raise ValueError(message)
    return weight


def _validate_total(total: Decimal, message: str) -> None:
    if total != Decimal("100"):
        raise ValueError(message)


def validate_evaluation_criteria(value: Any) -> list[dict[str, Any]]:
    if value in (None, ""):
        return default_evaluation_criteria()

    if not isinstance(value, list) or not value:
        raise ValueError("Os criterios de avaliacao devem ter ao menos um bloco.")

    groups: list[dict[str, Any]] = []
    group_keys: set[str] = set()
    group_targets: set[str] = set()
    groups_total = Decimal("0")

    for group_index, group in enumerate(value, start=1):
        if not isinstance(group, dict):
            raise ValueError("Cada bloco de avaliacao deve ser um objeto.")

        key = str(group.get("key") or "").strip()
        target = str(group.get("target") or "").strip()
        label = str(group.get("label") or "").strip()
        group_weight = _validate_weight(
            group.get("weight"),
            "O peso do bloco de avaliacao deve ser maior que zero.",
        )
        criteria = group.get("criteria")

        if not key:
            raise ValueError(f"O identificador do bloco {group_index} e obrigatorio.")

        if key in group_keys:
            raise ValueError(f"O identificador de bloco '{key}' esta duplicado.")

        if target not in VALID_TARGETS:
            raise ValueError("O alvo do bloco deve ser 'work' ou 'student'.")

        if target in group_targets:
            raise ValueError(f"O alvo de avaliacao '{target}' esta duplicado.")

        if not label:
            raise ValueError(f"O nome do bloco {group_index} e obrigatorio.")

        if not isinstance(criteria, list) or not criteria:
            raise ValueError(f"O bloco '{label}' deve ter ao menos um criterio.")

        normalized_criteria: list[dict[str, Any]] = []
        criteria_keys: set[str] = set()
        criteria_total = Decimal("0")

        for criterion_index, criterion in enumerate(criteria, start=1):
            if not isinstance(criterion, dict):
                raise ValueError("Cada criterio de avaliacao deve ser um objeto.")

            criterion_key = str(criterion.get("key") or "").strip()
            criterion_label = str(criterion.get("label") or "").strip()
            criterion_description = str(criterion.get("description") or "").strip()
            criterion_weight = _validate_weight(
                criterion.get("weight"),
                "O peso do criterio deve ser maior que zero.",
            )

            if not criterion_key:
                raise ValueError(
                    f"O identificador do criterio {criterion_index} do bloco '{label}' e obrigatorio."
                )

            if criterion_key in criteria_keys:
                raise ValueError(
                    f"O criterio '{criterion_key}' esta duplicado no bloco '{label}'."
                )

            if not criterion_label:
                raise ValueError(
                    f"O nome do criterio {criterion_index} do bloco '{label}' e obrigatorio."
                )

            criteria_keys.add(criterion_key)
            criteria_total += criterion_weight
            normalized_criteria.append(
                {
                    "key": criterion_key,
                    "label": criterion_label,
                    "description": criterion_description,
                    "weight": float(criterion_weight),
                }
            )

        _validate_total(
            criteria_total,
            f"A soma dos criterios do bloco '{label}' deve ser 100.",
        )

        group_keys.add(key)
        group_targets.add(target)
        groups_total += group_weight
        groups.append(
            {
                "key": key,
                "target": target,
                "label": label,
                "weight": float(group_weight),
                "criteria": normalized_criteria,
            }
        )

    missing_targets = VALID_TARGETS - group_targets
    if missing_targets:
        raise ValueError(
            "Os criterios de avaliacao devem conter blocos para avaliador e orientador."
        )

    _validate_total(groups_total, "A soma dos blocos de avaliacao deve ser 100.")

    return groups


def get_evaluation_group_weight(value: Any, target: str, fallback: Decimal) -> Decimal:
    try:
        groups = validate_evaluation_criteria(value)
    except ValueError:
        groups = default_evaluation_criteria()

    for group in groups:
        if group["target"] == target:
            return _to_decimal(group["weight"])

    return fallback
