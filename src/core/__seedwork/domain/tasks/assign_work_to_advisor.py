from celery import shared_task
from django.db.models import Count
from core.work.infra.work_django_app.models import Work
from core.user.infra.user_django_app.models import User
from core.edition.infra.edition_django_app.models import Edition
from datetime import datetime

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
                            print(f"Advisor {advisor} associado ao trabalho: {work.title}")
                        else:
                            print(f"Nenhum advisor encontrado para o tema: {theme.name}")
                    else:
                        print(f"Nenhum tema associado ao trabalho: {work.title}")

            print("Todos os trabalhos foram associados a advisors.")
