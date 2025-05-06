from core.field.infra.field_django_app.models import Field
from core.populate.infra.resources.data_field import fields

def populate_fields():
    if Field.objects.exists():
        return
    
    for field_data in fields:
        field = Field.objects.create(
            name = field_data["name"],
        )
        field.save()