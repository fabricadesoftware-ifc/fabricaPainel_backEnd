
import asyncio
from django.core.mail import send_mail
from asgiref.sync import sync_to_async

async def send_work_new_status_approve_email_to_student(from_email, email_student_recipient_list):
    await asyncio.sleep(1)
    email_message = """
    Olá, estudante!
    Seu trabalho teve o status mudado para aceito!
    """
    
    await sync_to_async(send_mail)(
        "Seu trabalho que tinha sido rejeitado pelo seu orientador, mas agora o status foi alterado para aceito pelo Orientador.!",
        email_message,
        from_email,
        email_student_recipient_list,
    )














