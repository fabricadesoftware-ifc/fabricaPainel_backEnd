from core.work.infra.work_django_app.models import Ods
from core.populate.infra.resources.data_ods import ods_data

def populate_ods():
    if Ods.objects.exists():
        return
    
    for ods_datas in ods_data:
        ods = Ods.objects.create(
            name = ods_datas["name"],
        )
        ods.save()