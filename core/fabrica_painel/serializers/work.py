from rest_framework import serializers

from core.fabrica_painel.models.work import Work

from core.fabrica_painel.models import Edition

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
            'ods',
            'reject_submission_work_date',
            'status'
        ]

def validate_work_date_submission_is_valid(attrs):
    edition = Edition.objects.get(id=attrs['edition'].id)
    print(edition, "AQUI AQUI AQUI AQUI AQUI")
    return attrs['initial_submission_work_date'] > edition.final_submission_date

        

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
            'team',
            'ods'
        ]
    
    def validate(self, attrs):
        if validate_work_date_submission_is_valid(attrs):
            raise serializers.ValidationError("Data de submissão inicial não pode ser maior que a data final da edição.")
        return super().validate(attrs)