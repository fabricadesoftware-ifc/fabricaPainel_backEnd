
from rest_framework import serializers

from core.work.infra.work_django_app.models import Work
from core.work.infra.work_django_app.models import Keyword
from core.work.infra.work_django_app.models import Team
from core.work.infra.work_django_app.models import Ods
from core.work.domain.validations import (validate_work_date_submission_is_valid, validate_work_team_members, 
                                          validate_work_max_and_min_members, validate_work_team_member_is_student)

class OdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ods
        fields: list[str] = [
            "id",
            "name",
        ]

class WorkDetailSerializer(serializers.ModelSerializer):
    evaluator = serializers.StringRelatedField(many=True)
    team = serializers.StringRelatedField()


    class Meta:
        model = Work
        fields: list[str] = [
            'id',
            'title',
            'abstract',
            'edition',
            'field',
            'evaluator',
            'cross_cutting_theme',
            'initial_submission_work_date',
            'final_submission_work_date',
            'verification_token',
            'team',
            'ods',
            'reject_submission_work_date',
            'status',
            'advisor',
        ]   
        depth = 1 

class WorkWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields: list[str] = [
            'title',
            'abstract',
            'edition',
            'field',
            'evaluator',
            'cross_cutting_theme',
            'team',
            'ods',

        ]

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.method == 'POST':
            if validate_work_date_submission_is_valid(attrs):
                raise serializers.ValidationError("Fora da data de submissão")
            if validate_work_team_members(attrs):
                raise serializers.ValidationError("Membro já associado a outro trabalho")
        return super().validate(attrs)
    
class KeywordDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields: list[str] = [
            'id',
            'name',
            'work'
        ]


class KeywordWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields: list[str] = [
            'name',
            'work',
        ]

class OdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ods
        fields: list[str] = [
            "id",
            "name",
        ]

class TeamDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields: list[str] = [
            'id',
            'team_members',
        ]

        

class TeamWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields: list[str] = [
            'team_members',
        ]
    # def validate(self, attrs):
    #     # print("Entrou na validação")  # Para ver se o método validate está sendo chamado
    #     # if validate_work_max_and_min_members(attrs):
    #     #     raise serializers.ValidationError("O time não pode ter mais do que 7 membros e menos que 4")
    #     # if validate_work_team_member_is_student(attrs):
    #     #     raise serializers.ValidationError("Um membro do time não é estudante")
    #     # return super().validate(attrs)