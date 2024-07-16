
import asyncio
from django.core.mail import send_mail

async def send_work_email_to_advisor(instance, email_subject, from_email, email_recipient_list, accept_work_link):
        
        await asyncio.sleep(1)
        # Fallback to use when HTML message is not supported
        email_message: str = f"""
        Título do Trabalho submetido:
        {instance.title}
        Campo do Trabalho submetido:
        {instance.field}
        Resumo do Trabalho submetido:
        {instance.abstract}
        Para aceitar essa submissão, clique no seguinte link:
        {accept_work_link}
        """

        # Formatted message
        email_html_message: str = f"""
        <h2>Título do Trabalho submetido:</h2>
        <h3>{instance.title}</h3>
        <h2>Campo do Trabalho submetido:</h2>
        <h3>{instance.field}</h3>
        <h2>Resumo do Trabalho submetido:</h2>
        <h3>{instance.abstract}</h3>
        Clique <a href={accept_work_link}>aqui</a> para aceitar essa submissão
        """

        try:
            send_mail(
                email_subject,
                email_message,
                from_email,
                email_recipient_list,
                html_message=email_html_message,
                fail_silently=False,
            )

        except Exception as e:
            print(e)
