
from rest_framework import serializers

from core.work.models import Work
from core.work.models import Keyword
from core.work.models import Team
from core.work.models import Ods
from core.edition.models import Edition

class OdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ods
        fields: list[str] = [
            "id",
            "name",
        ]

class WorkDetailSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Work
        fields: list[str] = [
            'id',
            'title',
            'abstract',
            'edition',
            'field',
            'evaluator',
            'advisor',
            'initial_submission_work_date',
            'final_submission_work_date',
            'verification_token',
            'team',
            'ods',
            'reject_submission_work_date',
            'status'
        ]
def validate_work_date_submission_is_valid(attrs):
    if 'edition' not in attrs:
        raise ValueError("A chave 'edition' não está presente em attrs")

    edition = Edition.objects.get(id=attrs['edition'].id)
    
    if attrs['initial_submission_work_date'] > edition.final_submission_date:
        return True  
    return False
        

class WorkWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields: list[str] = [
            'title',
            'abstract',
            'edition',
            'field',
            'evaluator',
            'advisor',
            'initial_submission_work_date',
            'team',
            'ods'
        ]
    
    def validate(self, attrs):
        if validate_work_date_submission_is_valid(attrs):
            raise serializers.ValidationError("Data de submissão inicial não pode ser maior que a data final da edição.")
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
