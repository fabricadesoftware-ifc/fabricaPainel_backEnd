from core.populate.infra.resources.data_works import works
from core.work.infra.work_django_app.models import Work, Team
from core.edition.infra.edition_django_app.models import Edition
from core.field.infra.field_django_app.models import Field
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme


def populate_works():
    if Work.objects.exists():
        print("work")
        return
    
    for work_data_item in works:
        try:
            edition = Edition.objects.get(id=work_data_item["edition"])
            team = Team.objects.get(id=work_data_item["team"])
            cross_cutting_theme = CrossCuttingTheme.objects.get(id=work_data_item["cross_cutting_theme"])

            work = Work.objects.create(
                title=work_data_item["title"],
                abstract=work_data_item["abstract"],
                edition=edition,
                cross_cutting_theme=cross_cutting_theme,
                initial_submission_work_date=work_data_item["initial_submission_work_date"],
                team = team,
                status=work_data_item["status"],
              
            )
            if 'field' in work_data_item:
                field_ids = work_data_item['field'] 
                fields = Field.objects.filter(id__in=field_ids) 
                work.field.set(fields)
            work.save()
            print(f"Trabalho '{work.title}' populado com sucesso.")
        
        except Edition.DoesNotExist:
            print(f"Edição com ID {work_data_item['edition']} não encontrada. Ignorando esse trabalho.")
        except Exception as e:
            print(f"Erro ao popular trabalho: {e}")

    print("População de trabalhos concluída.")