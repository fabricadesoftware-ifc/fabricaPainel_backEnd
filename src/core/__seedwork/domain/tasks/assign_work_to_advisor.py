from celery import shared_task
from django.db.models import Count
from django_project.settings import EMAIL_HOST_USER
from datetime import datetime

from core.work.infra.work_django_app.models import Work
from core.user.infra.user_django_app.models import User
from core.edition.infra.edition_django_app.models import Edition
from core.work.domain.tasks.send_email_advisor.send_work_email_to_advisor import send_work_email_to_advisor
from ..actions.work_path import work_path

@shared_task(name="core.assign_work_to_advisor")
def assign_work_to_advisor():
    print("Iniciando a associação de advisors aos trabalhos.")
    now = datetime.now().date()
    editions = Edition.objects.all()

    for edition in editions:
        print(f"Verificando a edição: {edition.year} - {edition.is_open}")
        if edition.year == 2025:
            print(f"Edição {edition.year} está aberta. Verificando a data de submissão final.")
            print(f"Data de submissão final: {edition.final_submission_date} - {now} - {edition.final_submission_date < now}")

            if edition.final_submission_date < now:
                print(f"Data de submissão final {edition.final_submission_date} é anterior a hoje ({now}).")
                works = Work.objects.filter(edition__id=edition.id)
                print(f"Encontrados {works.count()} trabalhos para a edição {edition.year}.")
                for work in works:
                    print(f"Processando trabalho: {work.title}")
                    theme = work.cross_cutting_theme
                   
                    if work.advisor is not None:
                        print(f"Trabalho {work.title} já possui um advisor associado: {work.advisor.email}")
                        if theme:

                            work_id = work.id
                            print(f"Trabalho {work.title} já possui um advisor associado.")
                            email_subject = "Trabalho associado a um orientador"
                            from_email = EMAIL_HOST_USER 
                            email_recipient_list = [work.advisor.email]
                            
                            accept_work_link = work_path(work)
                            students_emails = [member.email for member in work.team.team_members.all()]
                            send_work_email_to_advisor.delay(
                                work_id,
                                email_subject,
                                from_email,
                                email_recipient_list,
                                accept_work_link,
                                students_emails
                            )
                            print("Enviou o email")                                

                    elif theme:
                        advisors = User.objects.filter(
                            is_advisor=True,
                            crosscuttingtheme__id=theme.id
                        ).annotate(work_count=Count('advisor')).order_by('work_count')

                        if advisors.exists():
                            advisor = advisors.first()
                            print(f"Advisor {advisor} associado ao trabalho: {work.title}")
                            work.advisor = advisor
                            work.save()

                            try:
                                work_id = work.id
                                email_subject = "Trabalho associado a um orientador"
                                from_email = EMAIL_HOST_USER 
                                email_recipient_list = [advisor.email]
                          
                                accept_work_link = work_path(work)

                                students_emails = [member.email for member in work.team.team_members.all()]  # 

                                send_work_email_to_advisor.delay(
                                    work_id,
                                    email_subject,
                                    from_email,
                                    email_recipient_list,
                                    accept_work_link,
                                    students_emails
                                )
                                print("Enviou o email")
                            except Exception as e:
                                print(f"Erro nessa bomba de email: {e}")

                            print(f"Advisor {advisor} associado ao trabalho: {work.title}")
                        else:
                            print(f"Nenhum advisor encontrado para o tema: {theme.name}")
                    else:
                        print(f"Nenhum tema associado ao trabalho: {work.title}")

            print("Todos os trabalhos foram associados a advisors.")
