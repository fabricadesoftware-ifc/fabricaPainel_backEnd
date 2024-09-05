from django.core.mail import send_mail
from celery import shared_task
from core.work.models import Work



@shared_task
def send_work_cancel_email_to_student(work_id: str, from_email: str) -> None:
    """
    Sends an email to the student informing that the work was canceled.
    """
    work: object = Work.objects.get(id=work_id)
    students = work.team.students.all()
    students_emails = [student.email for student in students]
    

    subject: str = 'Trabalho cancelado com sucesso.'
    message : str = f'Olá {work.team}, o trabalho {work.title} foi cancelado com sucesso.'

    email_student_recipient_list: list = [students_emails]

    send_mail(subject, message, from_email, email_student_recipient_list)