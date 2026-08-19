from rest_framework.exceptions import ValidationError

# Um trabalho rejeitado (4) ou expirado (5) não ocupa vaga do orientador: só contam
# os que continuam vivos na edição. Mesma regra já usada para colaboradores em
# validate_work_collaborators.
ACTIVE_WORK_STATUS = [1, 2, 3]


def count_advisor_accepted_works(advisor, edition, current_work_id=None) -> int:
    """
    Conta quantos trabalhos vivos da edição o orientador já *aceitou* orientar.

    A vaga só é ocupada quando o orientador aceita (advisor_status = APPROVED).
    Convites pendentes não contam, senão um único convite ainda não respondido
    deixaria a vaga presa e impediria outras equipes de convidar o mesmo professor.
    """
    from core.work.infra.work_django_app.models import Work, WorkAdvisorStatusType

    works = Work.objects.filter(
        advisor=advisor,
        advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
        edition=edition,
        status__in=ACTIVE_WORK_STATUS,
    )

    if current_work_id:
        works = works.exclude(id=current_work_id)

    return works.count()


def advisor_work_limit_reached(advisor, edition, current_work_id=None) -> bool:
    """Indica se o orientador já bateu o limite de trabalhos da edição."""
    if not advisor or not edition:
        return False

    limit = edition.works_per_advisor_max
    if not limit:
        return False

    return count_advisor_accepted_works(advisor, edition, current_work_id) >= limit


def validate_advisor_work_limit(advisor, edition, current_work_id=None):
    """
    Garante que nenhum orientador ultrapasse 'works_per_advisor_max' da edição.

    Usado tanto na criação/edição do trabalho quanto no momento em que o orientador
    aceita o convite: a checagem na criação apenas antecipa o erro, porque entre o
    convite e o aceite outras equipes podem ter ocupado as vagas restantes.
    """
    if advisor_work_limit_reached(advisor, edition, current_work_id):
        raise ValidationError(
            f"O orientador {advisor.name or advisor.email} já atingiu o limite de "
            f"{edition.works_per_advisor_max} trabalho(s) nesta edição."
        )

    return advisor
