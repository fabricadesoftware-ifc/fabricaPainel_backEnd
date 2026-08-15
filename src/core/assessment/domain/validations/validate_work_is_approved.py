from rest_framework import serializers
from core.work.domain.value_objects import WorkStatusType


def validate_work_is_approved(work) -> bool:
    """
    Garante que só é possível lançar avaliação/nota em um trabalho cuja
    submissão já foi aprovada pelo orientador (Work.status == APPROVED) —
    evita nota em trabalho pendente, rejeitado ou que ainda precisa de ajustes.
    """
    if not work:
        raise serializers.ValidationError("Trabalho não informado para avaliação.")

    if work.status != WorkStatusType.Type.APPROVED.value:
        raise serializers.ValidationError(
            "Só é possível lançar avaliação em trabalhos com status 'Aprovado'."
        )

    return True
