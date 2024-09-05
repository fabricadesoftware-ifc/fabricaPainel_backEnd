
from rest_framework import serializers

from core.work.models import Work
from core.work.models import Keyword
from core.work.models import Team
from core.work.models import Ods
from core.__seedwork.validations.validate_work_date_submission import validate_work_date_submission_is_valid

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
            'cross_cutting_theme',
            'initial_submission_work_date',
            'final_submission_work_date',
            'verification_token',
            'team',
            'ods',
            'reject_submission_work_date',
            'status'
        ]    

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
            'initial_submission_work_date',
            'team',
            'ods'
        ]
    
    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.method == 'POST':
            if validate_work_date_submission_is_valid(attrs):
                raise serializers.ValidationError("Fora da data de submissão")
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
