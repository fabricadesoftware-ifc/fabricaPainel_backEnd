from rest_framework import serializers

from core.fabrica_painel.models.work import Work


class WorkDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields: list[str] = [
            'id',
            'title',
            'abstract',
            'edition',
            'field',
            'advisor',
            'initial_submission_work_date',
            'final_submission_work_date',
            'verification_token',
            'team',
            'ods'
        ]


class WorkWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields: list[str] = [
            'title',
            'abstract',
            'edition',
            'field',
            'advisor',
            'initial_submission_work_date',
            'final_submission_work_date',
            'team',
            'ods'
        ]
