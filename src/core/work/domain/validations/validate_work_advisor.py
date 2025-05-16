from core.user.infra.user_django_app.models import User
from rest_framework.exceptions import ValidationError

def validate_work_advisor(attrs):
    advisor = attrs.get('advisor')
    co_advisor = attrs.get('co_advisor')

    if advisor:
        if advisor.user_type != User.TEACHER:
            raise ValidationError(f"O orientador {advisor} deve ser um professor")
        
    if co_advisor:
        if co_advisor.user_type != User.TEACHER:
            raise ValidationError(f"O co-orientador {co_advisor} deve ser um professor")

    return attrs
