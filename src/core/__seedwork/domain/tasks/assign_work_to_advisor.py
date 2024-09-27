from celery import shared_task
from django.db.models import Count
from core.work.infra.work_django_app.models import Work
from core.user.infra.user_django_app.models import User
from core.edition.infra.edition_django_app.models import Edition
from datetime import datetime
from core.work.domain.tasks.send_email_advisor.send_work_email_to_advisor import send_work_email_to_advisor

@shared_task(name="core.assign_work_to_advisor")
def assign_work_to_advisor():
    # Obtém as edições cuja data de submissão final foi ultrapassada
    print("Iniciando a associação de advisors aos trabalhos.")
    now = datetime.now().date()
    editions = Edition.objects.all()

    for edition in editions:
        print(edition, edition.is_open)
        if edition.is_open == True:
            if edition.final_submission_date < now:
                print(f"Edição {edition} com data de submissão final ultrapassada.")
                works = Work.objects.filter(edition__id=edition.id)
                print(f"Works para a edição {edition.id}: {works}")
                for work in works:
                    theme = work.cross_cutting_theme
                    print(f"Associando advisor ao trabalho: {work.title}")

                    if theme:
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
                                # Preparar os argumentos necessários para o envio do e-mail
                                work_id = work.id
                                email_subject = "Trabalho associado a um Advisor"
                                from_email = "no-reply@seusistema.com"  # Email de origem
                                email_recipient_list = [advisor.email]  # Email do advisor
                                accept_work_link = f"http://seusistema.com/accept_work/{work.id}"  # Link para aceitar o trabalho
                                reject_work_link = f"http://seusistema.com/reject_work/{work.id}"  # Link para rejeitar o trabalho
                                students_emails = [member.email for member in work.team.team_members.all()]  # Emails dos membros 

                                
                                send_work_email_to_advisor.delay(
                                    work_id,
                                    email_subject,
                                    from_email,
                                    email_recipient_list,
                                    accept_work_link,
                                    reject_work_link,
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
