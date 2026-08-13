from rest_framework import serializers

from core.edition.infra.edition_django_app.models import Edition
from core.edition.domain.validations import (
    validate_dates,
    validate_evaluation_criteria as validate_evaluation_criteria_config,
    validate_year,
)
from core.uploader.infra.uploader_django_app.models import Image


class ImageAttachmentKeyRelatedField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        "does_not_exist": "Imagem nao encontrada para a chave informada.",
        "incorrect_type": "Tipo incorreto. Esperava id ou attachment_key de imagem.",
    }

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                return self.get_queryset().get(attachment_key=data)
            except (TypeError, ValueError, Image.DoesNotExist):
                self.fail("does_not_exist")

        return super().to_internal_value(data)


class EditionDetailSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    is_open_for_submissions = serializers.BooleanField(read_only=True)
    is_open_for_advisors = serializers.BooleanField(read_only=True)
    is_open_for_evaluators = serializers.BooleanField(read_only=True)
    is_edition_running = serializers.BooleanField(read_only=True)

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
            "evaluation_criteria",
            "workload",
            "banner",
            "logo",
            "is_active",
            "is_open_for_submissions",
            "is_open_for_advisors",
            "is_open_for_evaluators",
            "is_edition_running",
        ]
        depth = 1


class EditionWriteSerializer(serializers.ModelSerializer):
    banner = ImageAttachmentKeyRelatedField(
        queryset=Image.objects.all(),
        required=False,
        allow_null=True,
    )
    logo = ImageAttachmentKeyRelatedField(
        queryset=Image.objects.all(),
        required=False,
        allow_null=True,
    )

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
            "evaluation_criteria",
            "workload",
            "banner",
            "logo",
        ]

    def validate_evaluation_criteria(self, value):
        try:
            return validate_evaluation_criteria_config(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.method == "POST":
            try:
                validate_dates(attrs)
                validate_year(attrs)
            except ValueError as e:
                raise serializers.ValidationError(str(e))
        return super().validate(attrs)
