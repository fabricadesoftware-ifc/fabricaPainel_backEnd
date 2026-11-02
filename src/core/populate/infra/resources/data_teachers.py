from core.populate.infra.resources._private import load_private

# Dados fictícios. Os reais ficam fora do git (veja _private.py).
teachers = load_private("teachers", [
    {
        "registration": 1000001 + i,
        "name": f"Professor Exemplo {i + 1:02d}",
        "email": f"professor{i + 1:02d}@exemplo.test",
        "password": "senha-de-exemplo",
        "specialities": ["Informática"] if i % 2 == 0 else ["Matemática"],
    }
    for i in range(10)
])
