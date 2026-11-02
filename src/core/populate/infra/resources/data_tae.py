from core.populate.infra.resources._private import load_private

# Dados fictícios. Os reais ficam fora do git (veja _private.py).
tae = load_private("tae", [
    {
        "registration": 2000001 + i,
        "name": f"Servidor Exemplo {i + 1:02d}",
        "email": f"servidor{i + 1:02d}@exemplo.test",
        "password": "senha-de-exemplo",
        "specialities": ["Gestão"],
    }
    for i in range(5)
])
