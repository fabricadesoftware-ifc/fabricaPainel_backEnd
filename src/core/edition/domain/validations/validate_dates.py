def validate_dates(attrs):
    required_fields = [
        "event_date",
        "final_event_date",
        "initial_submission_date",
        "final_submission_date",
        "initial_advisor_acceptance",
        "final_advisor_acceptance",
        "initial_second_submission_date",
        "final_second_submission_date",
        "initial_second_advisor_date",
        "final_second_advisor_date",
        "initial_evaluators_date",
        "final_evaluators_date",
    ]

    for field in required_fields:
        if field not in attrs:
            raise ValueError(f"O campo '{field}' nao esta presente em attrs")

    if attrs["event_date"] > attrs["final_event_date"]:
        raise ValueError("A data de inicio do evento nao pode ser maior que a data final do evento")

    if attrs["initial_submission_date"] > attrs["final_submission_date"]:
        raise ValueError("A data de inicio da primeira submissao nao pode ser maior que a data final")

    if attrs["initial_advisor_acceptance"] > attrs["final_advisor_acceptance"]:
        raise ValueError("A data de inicio da primeira aceitacao nao pode ser maior que a data final")

    if attrs["initial_submission_date"] > attrs["initial_advisor_acceptance"]:
        raise ValueError("A primeira aceitacao nao pode iniciar antes da primeira submissao")

    if attrs["initial_advisor_acceptance"] > attrs["final_submission_date"]:
        raise ValueError("A primeira aceitacao deve iniciar antes do fim da primeira submissao")

    if attrs["final_submission_date"] > attrs["final_advisor_acceptance"]:
        raise ValueError("A primeira aceitacao deve terminar junto ou depois da primeira submissao")

    if attrs["final_advisor_acceptance"] > attrs["initial_second_submission_date"]:
        raise ValueError("A primeira aceitacao deve terminar antes da segunda submissao")

    if attrs["initial_second_submission_date"] > attrs["final_second_submission_date"]:
        raise ValueError("A data de inicio da segunda submissao nao pode ser maior que a data final")

    if attrs["initial_second_advisor_date"] > attrs["final_second_advisor_date"]:
        raise ValueError("A data de inicio da segunda aceitacao nao pode ser maior que a data final")

    if attrs["initial_second_submission_date"] > attrs["initial_second_advisor_date"]:
        raise ValueError("A segunda aceitacao nao pode iniciar antes da segunda submissao")

    if attrs["initial_second_advisor_date"] > attrs["final_second_submission_date"]:
        raise ValueError("A segunda aceitacao deve iniciar antes do fim da segunda submissao")

    if attrs["final_second_submission_date"] > attrs["final_second_advisor_date"]:
        raise ValueError("A segunda aceitacao deve terminar junto ou depois da segunda submissao")

    if attrs["final_second_advisor_date"] > attrs["event_date"]:
        raise ValueError("A segunda aceitacao deve terminar antes do evento")

    if attrs["event_date"] > attrs["initial_evaluators_date"]:
        raise ValueError("A avaliacao nao pode iniciar antes do evento")

    if attrs["initial_evaluators_date"] > attrs["final_event_date"]:
        raise ValueError("A avaliacao deve iniciar durante o evento")

    if attrs["final_event_date"] > attrs["final_evaluators_date"]:
        raise ValueError("A avaliacao deve terminar junto ou depois do evento")

    if attrs["initial_evaluators_date"] > attrs["final_evaluators_date"]:
        raise ValueError("A data de inicio da avaliacao nao pode ser maior que a data final")

    return False
