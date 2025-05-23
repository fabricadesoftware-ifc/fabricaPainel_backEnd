from core.populate.infra.resources.data_works import works
from core.work.infra.work_django_app.models import Work, Team, Keyword
from core.edition.infra.edition_django_app.models import Edition
from core.field.infra.field_django_app.models import Field
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.work.infra.work_django_app.models import Ods, Evaluator


def populate_works():
    if Work.objects.exists():
        print("Trabalhos já existentes. Abortando população.")
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
                team=team,
                status=work_data_item["status"],
            )

            if "field" in work_data_item:
                field_ids = work_data_item["field"]
                fields = Field.objects.filter(id__in=field_ids)
                work.field.set(fields)

            if "ods" in work_data_item:
                ods_ids = work_data_item["ods"]
                ods_list = Ods.objects.filter(id__in=ods_ids)
                work.ods.set(ods_list)

            if "evaluators" in work_data_item:
                evaluator_ids = work_data_item["evaluators"]
                evaluators = Evaluator.objects.filter(id__in=evaluator_ids)
                work.evaluator.set(evaluators)

            work.save()

            print(f"Trabalho '{work.title}' populado com sucesso.")

        except Edition.DoesNotExist:
            print(f"Edição com ID {work_data_item['edition']} não encontrada. Ignorando esse trabalho.")
        except Team.DoesNotExist:
            print(f"Equipe com ID {work_data_item['team']} não encontrada. Ignorando esse trabalho.")
        except CrossCuttingTheme.DoesNotExist:
            print(f"Tema transversal com ID {work_data_item['cross_cutting_theme']} não encontrado. Ignorando esse trabalho.")
        except Exception as e:
            print(f"Erro ao popular trabalho '{work_data_item.get('title', 'sem título')}': {e}")

    print("População de trabalhos concluída.")
