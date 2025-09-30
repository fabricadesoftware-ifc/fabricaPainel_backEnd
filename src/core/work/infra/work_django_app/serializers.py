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
)
from core.user.infra.user_django_app.serializers import UserSerializer, EvaluatorSerializer
from core.user.infra.user_django_app.models import User
from core.work.infra.work_django_app.models import WorkCollaborator
from core.work.domain.value_objects import WorkCollaboratorStatusType
from core.work.infra.work_django_app.models import CrossCuttingTheme
from core.work.infra.work_django_app.models import Field
from core.user.infra.user_django_app.models import Evaluator

class MinimalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email']

class EvaluatorLightSerializer(serializers.ModelSerializer):
    user = MinimalUserSerializer(read_only=True, source='evaluator')

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
    
    class Meta:
        model = WorkCollaborator
        fields = ['id', 'collaborator', 'status']

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
            "advisor_status",
            "integrated_project",
            "feedback",
            "work_collaborator",
        ]
        depth = 1
        # alterado para depth=1 para evitar vulnerabilidades em listagens grandes

class WorkDetailSerializer(serializers.ModelSerializer):
    work_collaborator = WorkCollaboratorSerializer(many=True, read_only=True)
    advisor = MinimalUserSerializer(read_only=True)
    team = TeamDetailSerializer(read_only=True)
    evaluator = EvaluatorLightSerializer(many=True, read_only=True)
    ods = OdsSerializer(many=True, read_only=True)
    cross_cutting_theme = CrossCuttingThemeSerializer(read_only=True)
    field = FieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = Work
        fields = [
            "id",
            "title",
            "abstract",
            "status",
            "advisor_status",
            "integrated_project",
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
            "edition",
        ]


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
                    
        return super().update(instance, validated_data)

    def validate(self, attrs):
        request = self.context.get("request")
        
        if request and request.method in ["PATCH", "PUT"] and self.instance:
            self._validate_work_status_for_updates(attrs)
        
        if request and request.method == "POST":
            try:
                validate_work_date_submission_is_valid(attrs)
            except ValidationError as e:
                raise ValidationError({"date_submission": str(e)})
            
            try:
                validate_work_team_members(attrs)
            except ValidationError as e:
                raise ValidationError({"team_members": str(e)})
            
            if attrs.get('collaborators'):
                try:
                    validate_work_collaborators(attrs)
                except ValidationError as e:
                    raise ValidationError({"collaborators": str(e)})
                
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
 