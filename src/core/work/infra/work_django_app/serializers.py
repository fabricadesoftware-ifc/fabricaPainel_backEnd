from uuid import uuid4

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
    validate_work_collaborators,
    validate_work_evaluator_limits,
)
from core.user.infra.user_django_app.serializers import UserSerializer, EvaluatorSerializer, UserClassSerializer
from core.user.infra.user_django_app.models import User
from core.work.infra.work_django_app.models import WorkCollaborator
from core.work.domain.value_objects import WorkCollaboratorStatusType, WorkAdvisorStatusType
from core.work.infra.work_django_app.models import CrossCuttingTheme
from core.work.infra.work_django_app.models import Field
from core.user.infra.user_django_app.models import Evaluator


# str(ValidationError) devolve o repr da lista de ErrorDetail; o front mostra isso cru.
def _error_text(error: ValidationError) -> str:
    detail = error.detail
    return str(detail[0] if isinstance(detail, list) else detail)


class MinimalUserSerializer(serializers.ModelSerializer):
    user_classes = UserClassSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'user_classes']

class EvaluatorLightSerializer(serializers.ModelSerializer):
    user = MinimalUserSerializer(read_only=True)

    class Meta:
        model = Evaluator
        fields = ['id', 'user']

class TeamDetailSerializer(serializers.ModelSerializer):
    team_members = MinimalUserSerializer(many=True)
    
    class Meta:
        model = Team
        fields = ["id", "team_members"]

class WorkCollaboratorSerializer(serializers.ModelSerializer):
    collaborator = MinimalUserSerializer(read_only=True)
    verification_token = serializers.SerializerMethodField()

    def get_verification_token(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and obj.collaborator_id == user.id:
            return obj.verification_token
        return None
    
    class Meta:
        model = WorkCollaborator
        fields = ['id', 'collaborator', 'status', 'verification_token']

class OdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ods
        fields = [
            "id",
            "name",
        ]

class CrossCuttingThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrossCuttingTheme
        fields = ["id", "name"]

class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ["id", "name"]

class WorkListSerializer(serializers.ModelSerializer):
    work_collaborator = WorkCollaboratorSerializer(many=True, read_only=True)
    advisor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_advisor=True, user_type=User.TEACHER),
        required=False, allow_null=True
    )
    submitted_at = serializers.SerializerMethodField()

    def get_submitted_at(self, obj):
        first_record = obj.history.order_by("history_date").first()
        return first_record.history_date if first_record else None

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
            "submitted_at",
            "status",
            "advisor",
            "advisor_status",
            "integrated_project",
            "work_kind",
            "feedback",
            "work_collaborator",
        ]
        depth = 1
        # alterado para depth=1 para evitar vulnerabilidades em listagens grandes

class WorkDetailSerializer(serializers.ModelSerializer):
    work_collaborator = WorkCollaboratorSerializer(many=True, read_only=True)
    verification_token = serializers.SerializerMethodField()
    advisor = MinimalUserSerializer(read_only=True)
    team = TeamDetailSerializer(read_only=True)
    evaluator = EvaluatorLightSerializer(many=True, read_only=True)
    ods = OdsSerializer(many=True, read_only=True)
    cross_cutting_theme = CrossCuttingThemeSerializer(read_only=True)
    field = FieldSerializer(many=True, read_only=True)
    edition_year = serializers.ReadOnlyField(source='edition.year')
    edition_evaluation_criteria = serializers.ReadOnlyField(source='edition.evaluation_criteria')
    edition_initial_evaluators_date = serializers.ReadOnlyField(source='edition.initial_evaluators_date')
    edition_final_evaluators_date = serializers.ReadOnlyField(source='edition.final_evaluators_date')
    edition_final_second_submission_date = serializers.ReadOnlyField(source='edition.final_second_submission_date')
    edition_evaluator_window = serializers.SerializerMethodField()

    def get_edition_evaluator_window(self, obj):
        status = obj.edition.evaluator_window_status()
        if status is None:
            return None

        return {
            "is_open_now": status["is_open_now"],
            "next_open_at": status["next_open_at"].isoformat() if status["next_open_at"] else None,
        }

    class Meta:
        model = Work
        fields = [
            "id",
            "title",
            "abstract",
            "verification_token",
            "status",
            "advisor_status",
            "integrated_project",
            "work_kind",
            "feedback",
            "needs_changes_submission_work_date",
            # Relacionamentos com serializers específicos
            "advisor",
            "team",
            "work_collaborator",
            "evaluator",
            "ods",
            "cross_cutting_theme",
            "field",
            # Relacionamentos simples (id, name)
            "edition_year",
            "edition_evaluation_criteria",
            "edition_initial_evaluators_date",
            "edition_final_evaluators_date",
            "edition_final_second_submission_date",
            "edition_evaluator_window",
            "edition",
        ]

    def get_verification_token(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and obj.advisor_id == user.id:
            return obj.verification_token
        return None


class WorkWriteSerializer(serializers.ModelSerializer):
    advisor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_advisor=True, user_type=User.TEACHER),
        required=False, allow_null=True
    )
    
    collaborators = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(is_collaborator=True).exclude(user_type=User.STUDENT),
        write_only=True,
        required=False,
    )
    
    def _validate_work_status_for_updates(self, attrs):
        """Valida se o trabalho pode ser alterado baseado no seu status atual."""
        if not self.instance:
            return
            
        if self.instance.status == 4:  # REJECTED
            raise ValidationError({
                "non_field_errors": ["Este trabalho foi rejeitado e não pode mais ser alterado."]
            })
        
        if self.instance.status != 1:  # Não é PENDING
            if 'advisor' in attrs:
                raise ValidationError({
                    "advisor": ["Não é possível alterar o orientador após o trabalho sair do status pendente."]
                })
            
            if 'collaborators' in attrs:
                raise ValidationError({
                    "collaborators": ["Não é possível alterar colaboradores após o trabalho sair do status pendente."]
                })

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
            "team",
            "ods",
            "integrated_project",
            "feedback",
            "advisor",
            "advisor_status",
            "collaborators",
        ]

    def create(self, validated_data):
        collaborators = validated_data.pop("collaborators", [])
        work = super().create(validated_data)
        
        for user in collaborators:
            WorkCollaborator.objects.create(work=work, collaborator=user)
            
        return work

    def update(self, instance, validated_data):
        collaborators = validated_data.pop("collaborators", None)
        if collaborators is not None:
            for user in collaborators:
                existing_collaborator = WorkCollaborator.objects.filter(work=instance, collaborator=user).first()

                if not existing_collaborator:
                    WorkCollaborator.objects.create(work=instance, collaborator=user)

        # Troca de orientador reabre a decisão, senão herdava o advisor_status do anterior.
        if "advisor" in validated_data and validated_data["advisor"] != instance.advisor:
            validated_data["advisor_status"] = WorkAdvisorStatusType.Type.PENDING.value
            # Token novo: o link do orientador anterior deixa de valer.
            validated_data["verification_token"] = str(uuid4())

        return super().update(instance, validated_data)

    def validate(self, attrs):
        request = self.context.get("request")
        
        if request and request.method in ["PATCH", "PUT"] and self.instance:
            self._validate_work_status_for_updates(attrs)
            new_advisor = attrs.get("advisor")
            if (
                new_advisor
                and self.instance.advisor_status == WorkAdvisorStatusType.Type.REJECTED.value
                and new_advisor == self.instance.advisor
            ):
                raise ValidationError({
                    "advisor": ["Escolha outro orientador: este já recusou o trabalho."]
                })

        if request and request.method == "POST":
            try:
                validate_work_date_submission_is_valid(attrs)
            except ValidationError as e:
                raise ValidationError({"date_submission": _error_text(e)})
            
            try:
                validate_work_team_members(attrs)
            except ValidationError as e:
                raise ValidationError({"team_members": _error_text(e)})
            
            if attrs.get('collaborators'):
                try:
                    validate_work_collaborators(attrs)
                except ValidationError as e:
                    raise ValidationError({"collaborators": _error_text(e)})

        if attrs.get('evaluator'):
            edition = attrs.get('edition') or (self.instance.edition if self.instance else None)
            current_work_id = self.instance.id if self.instance else None
            try:
                validate_work_evaluator_limits(edition, attrs.get('evaluator'), current_work_id)
            except ValidationError as e:
                raise ValidationError({"evaluator": _error_text(e)})

        # Vale tanto na criação quanto na troca de orientador via PATCH. É só uma
        # antecipação do erro: a vaga só é de fato ocupada no aceite, então quem
        # garante o limite é a checagem em accept_advisor_work.
        if attrs.get('advisor'):
            edition = attrs.get('edition') or (self.instance.edition if self.instance else None)
            current_work_id = self.instance.id if self.instance else None
            try:
                validate_work_advisor(
                    {**attrs, 'edition': edition},
                    current_work_id=current_work_id,
                )
            except ValidationError as e:
                raise ValidationError({"advisor": _error_text(e)})

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
    team_members = MinimalUserSerializer(many=True)
    
    class Meta:
        model = Team
        fields = ["id", "team_members"]


class TeamWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Team
        fields: list[str] = [
            "id",
            "team_members",
            "edition",
        ]

    def validate(self, attrs):
        if self.instance and hasattr(self.instance, 'work'):
            if self.instance.work.status == 4:  # REJECTED
                raise ValidationError({
                    "non_field_errors": ["Este time está associado a um trabalho rejeitado e não pode ser alterado."]
                })
        
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
 
