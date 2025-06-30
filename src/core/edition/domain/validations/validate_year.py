import datetime
from core.edition.infra.edition_django_app.models import Edition

def validate_year(attrs):
    field = 'year'
    
    if field not in attrs:
        raise ValueError(f"O campo '{field}' não está presente em attrs")
        
    current_year = datetime.datetime.now().year
    if attrs['year'] < current_year:
        raise ValueError("O ano não pode ser menor que o ano atual")
    
    if Edition.objects.filter(year=attrs['year']).exists():
        raise ValueError("Já existe uma edição para este ano")

    return False
