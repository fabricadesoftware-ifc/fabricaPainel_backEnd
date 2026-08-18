from datetime import date


def is_within_window(current_date: date, windows: list[tuple[date | None, date | None]]) -> bool:
    """Verifica se a data atual cai dentro de alguma das janelas (início, fim) informadas."""
    return any(initial and final and initial <= current_date <= final for initial, final in windows)


def advisor_decision_windows(edition) -> list[tuple[date | None, date | None]]:
    """
    Janelas em que o orientador pode decidir sobre um trabalho — tanto aceitar a
    orientação quanto aprovar a submissão.

    As duas ações são decisões do mesmo orientador e por isso compartilham o mesmo
    prazo. As datas de submissão (initial/final_submission_date) governam até quando
    os *alunos* podem enviar o trabalho, não até quando o *orientador* pode responder:
    como a validação da edição só exige `final_submission_date <= final_advisor_acceptance`,
    usar a janela de submissão para aprovar criava um intervalo em que o orientador
    conseguia aceitar a orientação mas não conseguia aprovar o trabalho.
    """
    return [
        (edition.initial_advisor_acceptance, edition.final_advisor_acceptance),
        (edition.initial_second_advisor_date, edition.final_second_advisor_date),
    ]


def acceptance_window_notice(current_date: date, windows: list[tuple[date | None, date | None]]) -> str:
    """
    Gera um aviso em HTML para ser embutido no e-mail quando a decisão (aceite de
    orientação, aprovação de submissão etc.) ainda não pode ser feita hoje.
    Retorna string vazia quando a data atual já está dentro de alguma janela.
    """
    if is_within_window(current_date, windows):
        return ""

    valid_windows = [(initial, final) for initial, final in windows if initial and final]
    upcoming = [initial for initial, _ in valid_windows if initial > current_date]

    if upcoming:
        message = f"Esta decisão só poderá ser feita a partir de {min(upcoming).strftime('%d/%m/%Y')}."
    elif valid_windows:
        message = "O período para esta decisão já se encerrou."
    else:
        return ""

    return (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:0 0 18px;">'
        '<tr><td style="background:#fff6e5;border:1px solid #f0d08a;border-radius:6px;padding:12px 16px;'
        f'font-size:14px;color:#8a6d1f;">{message}</td></tr></table>'
    )
