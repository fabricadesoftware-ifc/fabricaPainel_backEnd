from django.utils import timezone
from core.work.infra.work_django_app.models import Work
from core.work.domain.value_objects import WorkStatusType
from core.work.infra.work_django_app.serializers import (
    WorkDetailSerializer,
)
from celery import shared_task
import os
import logging
from io import BytesIO
from django.core.mail import EmailMessage
from django.conf import settings
from weasyprint import HTML
from django.template import engines

logger = logging.getLogger(__name__)

@shared_task
def change_status_to_expired():
    print("Expirando trabalhos pendentes")
    works = Work.objects.filter(status=WorkStatusType.Type.PENDING.value)
    for work in works:
        work.status = WorkStatusType.Type.EXPIRED.value
        work.save()
    
    works_expireds = Work.objects.filter(status=WorkStatusType.Type.EXPIRED.value)
    works_expireds_serialized = WorkDetailSerializer(works_expireds, many=True).data
    send_email_to_expirated_works(works_expireds_serialized, ["jonatassilvaperaza@gmail.com"])
    
    return 'Trabalhos expirados com sucesso'

def send_email_to_expirated_works(works, to_emails):
    try:
        template_path = os.path.join(settings.BASE_DIR, 'templates', 'expirated_works.html')

        context = {
            "trabalhos_data": works
        }

        with open(template_path, 'r', encoding='utf-8') as template_file:
            template_code = template_file.read()

        html_string = engines['django'].from_string(template_code).render(context)

        pdf_file = BytesIO()
        HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(target=pdf_file)
        pdf_file.seek(0)

        for to_email in to_emails:
            email = EmailMessage(
            subject='Trabalhos Expirados - FabricaPainel',
            body='Olá, segue em anexo o PDF com todos os trabalhos expirados.',
            from_email=settings.EMAIL_HOST_USER,
            to=[to_email],
            )
            email.attach('trabalhos_expirados.pdf', pdf_file.read(), 'application/pdf')
            email.send()

        logger.info(f"E-mail com PDF enviado para {to_email}")
        return f"E-mail com PDF enviado para {to_email}"

    except Exception as e:
        logger.exception(f"Erro ao gerar ou enviar o PDF para {to_email}: {e}")
        return f"Erro: {e}"
