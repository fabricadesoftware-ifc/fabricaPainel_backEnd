from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from core.work.infra.work_django_app.models import Work
from core.work.infra.work_django_app.models import Keyword
from core.work.infra.work_django_app.models import Team, Token
from core.work.infra.work_django_app.models import Ods
from core.work.domain.validations import (
    validate_work_date_submission_is_valid,
    validate_team_members,
    validate_work_max_and_min_members,
    validate_work_team_member_is_student,
    validate_work_advisor,
    validate_work_team_members,
)
from core.user.infra.user_django_app.serializers import UserSerializer, EvaluatorSerializer
from core.user.infra.user_django_app.models import User


class OdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ods
        fields: list[str] = [
            "id",
            "name",
        ]


class WorkDetailSerializer(serializers.ModelSerializer):
    # team = serializers.StringRelatedField()
    evaluator = serializers.ListSerializer(
        required = False,
        allow_null = True,
        child=EvaluatorSerializer()
    )

    class Meta:
        model = Work
        fields: list[str] = [
            "id",
            "title",
            "abstract",
            "edition",
            "field",
            "evaluator",
            "cross_cutting_theme",
            "verification_token",
            "team",
            "ods",
            "needs_changes_submission_work_date",
            "status",
            "advisor",
            "integrated_project",
            "feedback",
        ]
        depth = 2


class WorkWriteSerializer(serializers.ModelSerializer):
    advisor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Work
        fields: list[str] = [
            "title",
            "abstract",
            "edition",
            "field",
            "evaluator",
            "cross_cutting_theme",
            "team",
            "ods",
            "integrated_project",
            "feedback",
            "advisor",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.method == "POST":
            try:
                validate_work_date_submission_is_valid(attrs)
            except Exception as e:
                raise e
            try:
                validate_work_team_members(attrs)
            except Exception as e:
                raise e
        return super().validate(attrs)


class KeywordDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields: list[str] = ["id", "name", "work"]


class KeywordWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields: list[str] = [
            "name",
            "work",
        ]


class OdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ods
        fields: list[str] = [
            "id",
            "name",
        ]


class TokenSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    sender = UserSerializer()

    class Meta:
        model = Token
        fields: list[str] = ["id", "user", "sender", "token"]


class TeamDetailSerializer(serializers.ModelSerializer):
    team_members = UserSerializer(many=True)
    #tokens = TokenSerializer(many=True)
    #accept_tokens = TokenSerializer(many=True)
    #reject_tokens = TokenSerializer(many=True)

    class Meta:
        model = Team
        fields: list[str] = [
            "id",
            "team_members",
            "edition"
            #"tokens",
            #"accept_tokens",
            #"reject_tokens",
        ]
        depth = 1


class TeamWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Team
        fields: list[str] = [
            "id",
            "team_members",
            "edition",
            #"tokens",
            #"accept_tokens",
            #"reject_tokens",
        ]

    def validate(self, attrs):
        try:
            validate_work_max_and_min_members(attrs)
        except Exception as e:
            raise e
        try:
            validate_work_team_member_is_student(attrs)
        except Exception as e:
            raise e
        try:
            validate_team_members(attrs)
        except Exception as e:
            raise e
        return super().validate(attrs)
