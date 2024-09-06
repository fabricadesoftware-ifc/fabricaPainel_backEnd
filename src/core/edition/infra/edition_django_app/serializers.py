from rest_framework import serializers

from core.edition.infra.edition_django_app.models import Edition
from core.edition.domain.validations import validate_dates, validate_year
class EditionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edition
        fields: list[str] = [
            "id",
            "year",
            "theme",
            "edition_name",
            "initial_submission_date",
            "final_submission_date",
            "initial_advisor_date",
            "final_advisor_date",
            "initial_evaluators_date",
            "final_evaluators_date",
            "initial_registration_theme_date",
            "final_registration_theme_date",
            "initial_registration_evaluator_date",
            "final_registration_evaluator_date",
            "banner",
            "logo",
            "workload",
            "is_open"
        ]


class EditionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edition
        fields: list[str] = [
            "year",
            "theme",
            "edition_name",
            "initial_registration_theme_date",
            "final_registration_theme_date",
            "initial_registration_evaluator_date",
            "final_registration_evaluator_date",
            "initial_submission_date",
            "final_submission_date",
            "initial_advisor_date",
            "final_advisor_date",
            "initial_evaluators_date",
            "final_evaluators_date",
            "banner",
            "logo",
            "workload",
            "is_open"
        ]

    def validate(self, attrs):
        request = self.context.get('request')   
        if request and request.method == 'POST':
            try:
                validate_dates(attrs)
                validate_year(attrs)
            except ValueError as e:
                raise serializers.ValidationError(str(e))
        return super().validate(attrs)