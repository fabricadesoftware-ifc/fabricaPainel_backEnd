import pdfplumber

def is_value_in_pdf(file_path, value):
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if value in row:
                        return True
    return False