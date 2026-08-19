from core.user.infra.user_django_app.models import User
from core.user.domain.validations import validate_advisor_work_assignment
from .validate_advisor_work_limit import validate_advisor_work_limit
from rest_framework.exceptions import ValidationError

def validate_work_advisor(attrs, current_work_id=None):
    advisor = attrs.get('advisor')
    co_advisor = attrs.get('co_advisor')
    edition = attrs.get('edition')

    if advisor:
        validate_advisor_work_assignment(advisor)
        validate_advisor_work_limit(advisor, edition, current_work_id)

    if co_advisor:
        validate_advisor_work_assignment(co_advisor)
        validate_advisor_work_limit(co_advisor, edition, current_work_id)

    return attrs
