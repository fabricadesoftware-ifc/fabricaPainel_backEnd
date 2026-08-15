from rest_framework.exceptions import ValidationError


def validate_work_evaluator_limits(edition, evaluators, current_work_id=None) -> str | bool:
    """
    Garante que um trabalho não receba mais avaliadores do que 'evaluators_count'
    da edição, e que nenhum avaliador ultrapasse 'works_per_evaluator_max'
    trabalhos na mesma edição.
    """
    from core.work.infra.work_django_app.models import Work

    if not evaluators or not edition:
        return False

    evaluators = list(evaluators)

    if len(evaluators) > edition.evaluators_count:
        raise ValidationError(
            f"Este trabalho pode ter no máximo {edition.evaluators_count} "
            f"avaliador(es) nesta edição."
        )

    for evaluator in evaluators:
        works_qs = Work.objects.filter(evaluator=evaluator, edition=edition)
        if current_work_id:
            works_qs = works_qs.exclude(id=current_work_id)

        if works_qs.count() >= edition.works_per_evaluator_max:
            raise ValidationError(
                f"O avaliador {evaluator.user.name or evaluator.user.email} já atingiu "
                f"o limite de {edition.works_per_evaluator_max} trabalho(s) nesta edição."
            )

    return False
