import asyncio
from django.core.mail import send_mail
from asgiref.sync import sync_to_async

async def send_work_delete_email_to_student(from_email, email_student_recipient_list, instance):
    print("Sending email to student")
    await asyncio.sleep(1)
    email_message = """
    Olá, estudante!
    Seu trabalho submetido foi deletado pelo seu orientador.
    """
    
    await sync_to_async(send_mail)(
        "trabalho submetido foi deletado pelo seu orientador.",
        email_message,
        from_email,
        email_student_recipient_list,
    )