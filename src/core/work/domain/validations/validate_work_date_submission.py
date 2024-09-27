from core.edition.infra.edition_django_app.models import Edition

def validate_work_date_submission_is_valid(attrs):
    if 'edition' not in attrs:
        raise ValueError("A chave 'edition' não está presente em attrs")

    edition = Edition.objects.get(id=attrs['edition'].id)
    
    if edition.initial_submission_date > edition.final_submission_date:
        return True  
    return False