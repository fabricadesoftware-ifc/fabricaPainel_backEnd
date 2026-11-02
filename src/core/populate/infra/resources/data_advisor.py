from core.populate.infra.resources._private import load_private

# Dados fictícios. Os reais ficam fora do git (veja _private.py).
advisors = load_private("advisors", [
    {
        "name": f"Orientador Exemplo {i + 1:02d}",
        "email": f"orientador{i + 1:02d}@exemplo.test",
        "registration": str(3000001 + i),
        "password": "senha-de-exemplo",
        "is_advisor": True,
        "field": (i % 4) + 1,
        "user_type": "TEACHER",
    }
    for i in range(10)
])
