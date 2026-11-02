from core.populate.infra.resources._private import load_private

# Dados fictícios. Os reais ficam fora do git (veja _private.py).
students = load_private("students", [
    {
        "registration": 2025000001 + i,
        "name": f"Aluno Exemplo {i + 1:02d}",
        "email": f"aluno{i + 1:02d}@exemplo.test",
        "password": "senha-de-exemplo",
    }
    for i in range(35)
])
