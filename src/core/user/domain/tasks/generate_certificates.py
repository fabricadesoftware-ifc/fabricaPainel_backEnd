import hashlib
from django.utils import timezone
from django.conf import settings
from weasyprint import HTML
import base64
from io import BytesIO
import os


def _file_to_data_url(path):
    if not os.path.exists(path):
        return None
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    mime = 'image/png' if ext in ('.png', '.jpg', '.jpeg') else 'image/svg+xml'
    with open(path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode('ascii')
    return f"data:{mime};base64,{b64}"


def generate_certificate_pdf(certificate, work, user):
    with open(os.path.join(settings.BASE_DIR, 'templates/certificate.html'), 'r', encoding='utf-8') as f:
        html_string = f.read()

    logo_fabrica_path = os.path.join(settings.BASE_DIR, 'templates/logos/logo-fabrica.png')
    logo_if_path = os.path.join(settings.BASE_DIR, 'templates/logos/logo-ifc.png')
    
    html_string = html_string.replace("logo_fabrica", _file_to_data_url(logo_fabrica_path))
    html_string = html_string.replace("logo_ifc", _file_to_data_url(logo_if_path))
    html_string = html_string.replace("nome", user.name)
    html_string = html_string.replace("titulo", work.title)
    html_string = html_string.replace("carga_horaria", str(work.edition.workload))
    html_string = html_string.replace("hash", certificate.hash_validate)

    pdf_file_path = os.path.join(
        settings.MEDIA_ROOT,
        f"certificate_{certificate.id}.pdf"
    )

    HTML(string=html_string).write_pdf(pdf_file_path)
    return pdf_file_path

def generate_certificate_hash(user_id: int, work_id: int) -> str:
    """
    Gera um hash único para o certificado baseado no ID do usuário, ID do trabalho e timestamp atual.
    """
    hash_input = f"{user_id}-{work_id}-{timezone.now().timestamp()}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


