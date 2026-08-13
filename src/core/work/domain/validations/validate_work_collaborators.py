from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.user.domain.validations import validate_user_can_be_collaborator
from core.work.infra.work_django_app.models import Work


def validate_work_collaborators(attrs):
    """
    Valida as regras de negocio para colaboradores:
    - numero minimo e maximo de colaboradores por trabalho;
    - limite de trabalhos ativos por colaborador;
    - colaborador deve ter is_collaborator=True;
    - colaborador nao pode ser estudante;
    - criacao deve estar dentro da primeira ou segunda janela de submissao.
    """
    collaborators = attrs.get("collaborators", [])
    edition = attrs.get("edition")

    if not edition:
        raise ValidationError({"edition": "O campo 'edition' e obrigatorio"})

    today = timezone.localdate()
    first_submission_open = (
        edition.initial_submission_date
        and edition.final_submission_date
        and edition.initial_submission_date <= today <= edition.final_submission_date
    )
    second_submission_open = (
        edition.initial_second_submission_date
        and edition.final_second_submission_date
        and edition.initial_second_submission_date <= today <= edition.final_second_submission_date
    )

    if not (first_submission_open or second_submission_open):
        raise ValidationError({
            "collaborators": "Nao e possivel adicionar colaboradores fora do periodo de submissao"
        })

    if not collaborators:
        return attrs

    num_collaborators = len(collaborators)

    if num_collaborators < edition.collaborators_min:
        raise ValidationError({
            "collaborators": f"O trabalho deve ter no minimo {edition.collaborators_min} colaboradores"
        })

    if num_collaborators > edition.collaborators_max:
        raise ValidationError({
            "collaborators": f"O trabalho deve ter no maximo {edition.collaborators_max} colaboradores"
        })

    for collaborator in collaborators:
        if not collaborator.is_collaborator:
            raise ValidationError({
                "collaborators": f"O usuario {collaborator.name or collaborator.email} nao e um colaborador valido"
            })

    for collaborator in collaborators:
        try:
            validate_user_can_be_collaborator(collaborator)
        except ValidationError as exc:
            raise ValidationError({"collaborators": str(exc)}) from exc

    for collaborator in collaborators:
        current_works_count = Work.objects.filter(
            work_collaborator__collaborator=collaborator,
            work_collaborator__status=2,
            edition=edition,
            status__in=[1, 2, 3],
        ).count()

        if current_works_count >= edition.works_per_collaborator_max:
            raise ValidationError({
                "collaborators": (
                    f"O colaborador {collaborator.name or collaborator.email} ja atingiu "
                    f"o limite maximo de {edition.works_per_collaborator_max} trabalhos"
                )
            })

    return attrs
