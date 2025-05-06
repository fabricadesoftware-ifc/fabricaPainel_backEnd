import json
from typing import Optional

def read_json(json_path: str, registration: str, **kwargs) -> Optional[bool]:
    with open(json_path, 'r', encoding='utf-8') as f: 
        data: dict  = json.load(f)
        
        matricula: str = "MATRICULA:"
        for value in data:
            if value.get(matricula) == registration:
                print('Matrícula encontrada')
                return True
        
        print('Matrícula não encontrada')
        return None
