def validate_dates(attrs):
    required_fields = [
        'initial_submission_date', 'final_submission_date',
        'initial_second_submission_date', 'final_second_submission_date',
        'initial_advisor_acceptance', 'final_advisor_acceptance',
        'initial_second_advisor_date', 'final_second_advisor_date',
        'initial_evaluators_date', 'final_evaluators_date',
    ]

    for field in required_fields:
        if field not in attrs:
            raise ValueError(f"O campo '{field}' não está presente em attrs")

    # if attrs['initial_submission_date'] > attrs['final_submission_date']:
    #     raise ValueError("A data de início de submissão não pode ser maior que a data final de submissão")
    # if attrs['initial_advisor_date'] > attrs['final_advisor_date']:
    #     raise ValueError("A data de início dos orientadores não pode ser maior que a data final dos orientadores")
    # if attrs['initial_evaluators_date'] > attrs['final_evaluators_date']:
    #     raise ValueError("A data de início dos avaliadores não pode ser maior que a data final dos avaliadores")
    # if attrs['initial_registration_theme_date'] > attrs['final_registration_theme_date']:
    #     raise ValueError("A data de início do tema não pode ser maior que a data final do tema")
    # if attrs['initial_registration_evaluator_date'] > attrs['final_registration_evaluator_date']:
    #     raise ValueError("A data de início dos avaliadores não pode ser maior que a data final dos avaliadores")

    if attrs['initial_submission_date'] > attrs['final_submission_date']:
        raise ValueError("A data de início de submissão não pode ser maior que a data final de submissão")
    if attrs['final_submission_date'] > attrs['initial_second_submission_date']:
        raise ValueError("A data de início da submissão não pode ser maior que a data de início da segunda submissão")
    if attrs['initial_second_submission_date'] > attrs['final_second_submission_date']:
        raise ValueError("A data de início da segunda submissão não pode ser maior que a data final da segunda submissão")
    
    if attrs['final_second_submission_date'] > attrs['initial_advisor_acceptance']:
        raise ValueError("A data final da segunda submissão não pode ser maior que a data de início de aceitação de orientadores")
    

    if attrs['initial_advisor_acceptance'] > attrs['final_advisor_acceptance']:
        raise ValueError("A data de início de aceitação de orientadores não pode ser maior que a data final de aceitação de orientadores")
    if attrs['initial_second_advisor_date'] < attrs['final_advisor_acceptance']:
        raise ValueError("A data final de aceitação de orientadores não pode ser maior que a data de início da segunda aceitação de orientadores")
    if attrs['final_second_advisor_date'] > attrs['initial_evaluators_date']:
        raise ValueError("A data final da segunda aceitação de orientadores não pode ser maior que a data de início para avaliadores")
    
    if attrs['initial_evaluators_date'] > attrs['final_evaluators_date']:
        raise ValueError("A data de início dos avaliadores não pode ser maior que a data final dos avaliadores")
    
    return False

