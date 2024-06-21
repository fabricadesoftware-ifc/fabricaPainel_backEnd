import pdfplumber

file_path = "core/usuario/pdf_files/example.pdf"

with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)