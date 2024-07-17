import asyncio
from django.core.mail import send_mail
from asgiref.sync import sync_to_async

async def send_work_email_to_student(from_email, email_student_recipient_list):
    await asyncio.sleep(1)
    email_message = """
    Olá, estudante!
    Seu trabalho foi submetido com sucesso!
    """
    
    await sync_to_async(send_mail)(
        "Trabalho submetido com sucesso!",
        email_message,
        from_email,
        email_student_recipient_list,
    )