from core.edition.infra.edition_django_app.models import Edition
from core.populate.infra.resources.data_edition import editions

def populate_editions():
    if Edition.objects.exists():
        return
    
    for edition_data in editions:
        edition = Edition.objects.create(
            year = edition_data["year"],
            theme = edition_data["theme"],
            edition_name = edition_data["edition_name"],
            initial_registration_theme_date = edition_data["initial_registration_theme_date"],
            final_registration_theme_date = edition_data["final_registration_theme_date"],
            initial_registration_evaluator_date = edition_data["initial_registration_evaluator_date"],
            final_registration_evaluator_date = edition_data["final_registration_evaluator_date"],
            initial_submission_date = edition_data["initial_submission_date"],
            final_submission_date = edition_data["final_submission_date"],
            initial_advisor_date = edition_data["initial_advisor_date"],
            final_advisor_date = edition_data["final_advisor_date"],
            initial_evaluators_date = edition_data["initial_evaluators_date"],
            final_evaluators_date = edition_data["final_evaluators_date"],
            workload = edition_data["workload"],
            is_open = edition_data["is_open"],
            banner = edition_data["banner"],
            logo = edition_data["logo"],
        )
        edition.save()