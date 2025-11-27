import hashlib
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from io import BytesIO
import os


def generate_certificate_pdf(certificate, work, user):
    """
    Gera um PDF de certificado para o usuário e trabalho fornecidos.
    """
    html_string = render_to_string('certificate.html', {
        'certificate': certificate,
        'work': work,
        'user': user,
    })

    # Gera o PDF a partir do HTML renderizado
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


