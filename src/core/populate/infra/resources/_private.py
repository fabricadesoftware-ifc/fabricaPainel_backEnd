"""Dados reais de pessoas (alunos, professores, TAEs) NUNCA entram no git.

Para popular com dados reais, aponte PAINEL_PRIVATE_DATA_DIR para uma pasta fora do
repositório com arquivos <nome>.json (ex.: students.json, teachers.json, tae.json,
advisors.json). Sem a variável, o populate usa os dados fictícios de cada módulo.
"""
import json
import os
from pathlib import Path


def load_private(name, fallback):
    base = os.getenv("PAINEL_PRIVATE_DATA_DIR")
    if base:
        path = Path(base) / f"{name}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return fallback
