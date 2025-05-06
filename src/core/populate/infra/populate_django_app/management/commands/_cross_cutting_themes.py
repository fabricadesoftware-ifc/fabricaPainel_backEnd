from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from django.contrib.auth import get_user_model
from core.populate.infra.resources.data_cross_cutting_themes import cross_cutting_themes

User = get_user_model()

def populate_cross_cutting_themes():
    if CrossCuttingTheme.objects.exists():
        print("Temas transversais já estão populados.")
        return

    for cross_cutting_theme_data in cross_cutting_themes:
        try:
            # Cria o tema transversal
            cross_cutting_theme = CrossCuttingTheme.objects.create(name=cross_cutting_theme_data["name"],
            description=cross_cutting_theme_data["description"])

            # Verifica se os advisors existem e os associa ao tema transversal
            advisor_ids = cross_cutting_theme_data.get("advisor", [])
            advisors = User.objects.filter(id__in=advisor_ids)

            if advisors.exists():
                cross_cutting_theme.advisor.set(advisors)  # Associa os advisors
                print(f"Tema '{cross_cutting_theme.name}' populado com advisors {[advisor.id for advisor in advisors]}.")
            else:
                print(f"Erro: Nenhum advisor encontrado para o tema '{cross_cutting_theme.name}'. IDs fornecidos: {advisor_ids}")

            cross_cutting_theme.save()

        except Exception as e:
            print(f"Erro ao popular tema transversal '{cross_cutting_theme_data['name']}': {e}")

    print("População de temas transversais concluída.")
