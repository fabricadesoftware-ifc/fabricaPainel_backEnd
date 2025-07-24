from rest_framework import serializers

from core.edition.infra.edition_django_app.models import Edition
from core.edition.domain.validations import validate_dates, validate_year


class EditionDetailSerializer(serializers.ModelSerializer):
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = Edition
        fields: list[str] = [
            "id",
            "year",
            "theme",
            "edition_name",
            "event_date",
            "final_event_date",
            "initial_submission_date",
            "final_submission_date",
            "initial_second_submission_date",
            "final_second_submission_date",
            "initial_advisor_acceptance",
            "final_advisor_acceptance",
            "initial_second_advisor_date",
            "final_second_advisor_date",
            "initial_evaluators_date",
            "final_evaluators_date",
            "members_min",
            "members_max",
            "collaborators_min",
            "collaborators_max",
            "subjects_min",
            "subjects_max",
            "evaluators_count",
            "works_per_evaluator_max",
            "works_per_collaborator_max",
            "works_per_advisor_max",
            "words_per_work_min",
            "words_per_work_max",
            "workload",
            "banner",
            "logo",
            "is_open",
        ]
        depth = 1


class EditionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edition
        fields: list[str] = [
            "year",
            "theme",
            "edition_name",
            "event_date",
            "final_event_date",
            "initial_submission_date",
            "final_submission_date",
            "initial_second_submission_date",
            "final_second_submission_date",
            "initial_advisor_acceptance",
            "final_advisor_acceptance",
            "initial_second_advisor_date",
            "final_second_advisor_date",
            "initial_evaluators_date",
            "final_evaluators_date",
            "members_min",
            "members_max",
            "collaborators_min",
            "collaborators_max",
            "subjects_min",
            "subjects_max",
            "evaluators_count",
            "works_per_evaluator_max",
            "works_per_collaborator_max",
            "works_per_advisor_max",
            "words_per_work_min",
            "words_per_work_max",
            "workload",
            "banner",
            "logo",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.method == "POST":
            try:
                validate_dates(attrs)
                validate_year(attrs)
            except ValueError as e:
                raise serializers.ValidationError(str(e))
        return super().validate(attrs)
