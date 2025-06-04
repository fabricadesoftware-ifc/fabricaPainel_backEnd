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
from core.__seedwork.domain.actions.work_path import work_collaborator_path
from core.work.domain.tasks.send_email_collaborator.send_work_email_to_collaborator import send_work_email_to_collaborator
from django_project.settings import EMAIL_HOST_USER


class WorkCollaboratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCollaborator
        fields: list[str] = ["id", "collaborator", "status"]

class OdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ods
        fields: list[str] = [
            "id",
            "name",
        ]

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
        depth = 2


class WorkDetailSerializer(serializers.ModelSerializer):
    # team = serializers.StringRelatedField()
    advisor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_advisor=True, user_type=User.TEACHER),
        required=False, allow_null=True
    )
    work_collaborator = WorkCollaboratorSerializer(many=True, read_only=True)

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
        depth = 2


class WorkWriteSerializer(serializers.ModelSerializer):
    advisor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_advisor=True, user_type=User.TEACHER),
        required=False, allow_null=True
    )
    
    # campo de escrita para colaboradores (lista de IDs) - apenas não-estudantes
    collaborators = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(is_collaborator=True).exclude(user_type=User.STUDENT),
        write_only=True,
        required=False,
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
            "advisor_status",
            "collaborators",  # <- apenas escrita
        ]

    def create(self, validated_data):
        collaborators = validated_data.pop("collaborators", [])
        work = super().create(validated_data)
        
        # Cria WorkCollaborator e envia emails com tokens únicos
        for user in collaborators:
            work_collaborator = WorkCollaborator.objects.create(work=work, collaborator=user)
            
            # Gera links únicos para este colaborador específico
            accept_work_link, reject_work_link = work_collaborator_path(work_collaborator)
            
            # Envia email para este colaborador
            email_subject = f"Convite para colaborar no trabalho: {work.title}"
            from_email = EMAIL_HOST_USER
            
            send_work_email_to_collaborator.delay(
                work_collaborator.id,
                email_subject,
                from_email,
                accept_work_link,
                reject_work_link
            )
            
        return work

    def update(self, instance, validated_data):
        collaborators = validated_data.pop("collaborators", None)
        if collaborators is not None:
            for user in collaborators:
                existing_collaborator = WorkCollaborator.objects.filter(work=instance, collaborator=user).first()
                
                if not existing_collaborator:
                    # Cria novo WorkCollaborator se não existe
                    work_collaborator = WorkCollaborator.objects.create(work=instance, collaborator=user)
                    
                    # Gera links únicos para este novo colaborador
                    accept_work_link, reject_work_link = work_collaborator_path(work_collaborator)
                    
                    # Envia email para este colaborador
                    email_subject = f"Convite para colaborar no trabalho: {instance.title}"
                    from_email = EMAIL_HOST_USER
                    
                    send_work_email_to_collaborator.delay(
                        work_collaborator.id,
                        email_subject,
                        from_email,
                        accept_work_link,
                        reject_work_link
                    )
                    
                elif existing_collaborator.status == WorkCollaboratorStatusType.Type.PENDING.value:
                    # Se existe mas está pendente, reenvia email com novo token
                    accept_work_link, reject_work_link = work_collaborator_path(existing_collaborator)
                    
                    # Reenvia email para este colaborador
                    email_subject = f"Lembrete: Convite para colaborar no trabalho: {instance.title}"
                    from_email = EMAIL_HOST_USER
                    
                    send_work_email_to_collaborator.delay(
                        existing_collaborator.id,
                        email_subject,
                        from_email,
                        accept_work_link,
                        reject_work_link
                    )
                    
        return super().update(instance, validated_data)

    def validate(self, attrs):
        request = self.context.get("request")
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
