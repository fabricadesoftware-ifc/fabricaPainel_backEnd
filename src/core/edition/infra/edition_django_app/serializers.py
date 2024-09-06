from rest_framework import serializers
from core.edition.infra.edition_django_app.models import Edition


class EditionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edition
        fields: list[str] = [
            "id",
            "year",
            "theme",
            "edition_name",
            "initil_submission_date",
            "final_submission_date",
            "initial_advisor_date",
            "final_advisor_date",
            "initial_evaluators_date",
            "final_evaluators_date",
            "banner",
            "logo",
            "workload",
        ]


class EditionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edition
        fields: list[str] = [
            "year",
            "theme",
            "edition_name",
            "initil_submission_date",
            "final_submission_date",
            "initial_advisor_date",
            "final_advisor_date",
            "initial_evaluators_date",
            "final_evaluators_date",
            "banner",
            "logo",
            "workload",
        ]