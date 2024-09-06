import pdfplumber
import pandas as pd 
import json

def read_student_pdf_and_create_a_json_object(pdf_path: str, json_path: str) -> None:
    """
    Reads a PDF file containing student data and creates a JSON object.

    Args:
        pdf_path (str): The path to the PDF file.
        json_path (str): The path to save the JSON file.

    Returns:
        None
    """
    with pdfplumber.open(pdf_path) as pdf:
        data: list[dict] = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table[1:], columns=table[0])
                for index, row in df.iterrows():
                    data.append(row.to_dict())

    json_data = json.dumps(data, ensure_ascii=False, indent=4)

    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_data)

    print(f"JSON salvo em: {json_path}")

pdf_path: str = "src/core/user/pdf_files/planilha teste dois - Página1.pdf"

json_path: str = "src/core/user/json_list/student_list.json"

read_student_pdf_and_create_a_json_object(pdf_path, json_path)