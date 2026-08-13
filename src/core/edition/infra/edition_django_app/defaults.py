from typing import Any


def default_evaluation_criteria() -> list[dict[str, Any]]:
    return [
        {
            "key": "work",
            "target": "work",
            "label": "Nota do avaliador",
            "weight": 50,
            "criteria": [
                {
                    "key": "work_general",
                    "label": "Nota geral do trabalho",
                    "description": "",
                    "weight": 100,
                },
            ],
        },
        {
            "key": "student",
            "target": "student",
            "label": "Nota do orientador",
            "weight": 50,
            "criteria": [
                {
                    "key": "student_general",
                    "label": "Nota geral do aluno",
                    "description": "",
                    "weight": 100,
                },
            ],
        },
    ]
