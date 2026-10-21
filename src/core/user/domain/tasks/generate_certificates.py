import hashlib
import html
from django.utils import timezone
from django.conf import settings
from weasyprint import HTML
import base64
from io import BytesIO
import os

import segno


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


def build_validation_url(hash_validate: str) -> str:
    return f"{settings.PAINEL_URL.rstrip('/')}/validar-certificado/{hash_validate}"


def _qr_data_url(content: str) -> str:
    return segno.make(content, error="m").svg_data_uri(scale=4, border=0)


def generate_certificate_pdf(certificate, work, user):
    with open(os.path.join(settings.BASE_DIR, 'templates/certificate.html'), 'r', encoding='utf-8') as f:
        html_string = f.read()

    logo_fabrica_path = os.path.join(settings.BASE_DIR, 'templates/logos/logo-fabrica.png')
    logo_if_path = os.path.join(settings.BASE_DIR, 'templates/logos/logo-ifc.png')
    validation_url = build_validation_url(certificate.hash_validate)

    # Marcadores {{...}} únicos: um replace de "hash"/"nome" solto também trocava
    # nomes de classe e CSS do próprio template.
    replacements = {
        "{{LOGO_FABRICA}}": _file_to_data_url(logo_fabrica_path) or "",
        "{{LOGO_IFC}}": _file_to_data_url(logo_if_path) or "",
        "{{NOME}}": html.escape(user.name),
        "{{TITULO}}": html.escape(work.title),
        "{{CARGA_HORARIA}}": html.escape(str(work.edition.workload)),
        "{{QR_CODE}}": _qr_data_url(validation_url),
        "{{VALIDATION_URL}}": html.escape(validation_url),
        "{{HASH}}": html.escape(certificate.hash_validate),
    }
    for marker, value in replacements.items():
        html_string = html_string.replace(marker, value)

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


