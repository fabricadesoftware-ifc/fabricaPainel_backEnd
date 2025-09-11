from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from core.user.domain.validations import (
    validate_user_collaborator_status, 
    validate_evaluator_creation,
    validate_user_advisor_status
)

from .models import User, Evaluator, Class, UserClass, Specialty, Certificate


class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserClass
        fields = [
            "id",
            "class_name",
            "user",
            "year",
        ]
class UserClassSerializer(serializers.Serializer):
    class_name = serializers.CharField(source='class_name.name')
    year = serializers.IntegerField()
    


class UserRetrieveSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    name = serializers.CharField(read_only=True)
    user_type = serializers.CharField(read_only=True)
    

class UserSerializer(serializers.ModelSerializer):
    user_classes = UserClassSerializer(many=True, read_only=True)
    is_evaluator = serializers.SerializerMethodField()

    def get_is_evaluator(self, obj):
        return hasattr(obj, 'evaluator')

    def validate(self, attrs):
        # Usando validação do domínio para colaboradores
        user_type = attrs.get('user_type', getattr(self.instance, 'user_type', None))
        is_collaborator = attrs.get('is_collaborator', getattr(self.instance, 'is_collaborator', False))
        
        attrs_to_validate = {
            'user_type': user_type,
            'is_collaborator': is_collaborator
        }
        validate_user_collaborator_status(attrs_to_validate)
        
        # Usando validação do domínio para orientadores
        is_advisor = attrs.get('is_advisor', getattr(self.instance, 'is_advisor', False))
        
        attrs_to_validate = {
            'user_type': user_type,
            'is_advisor': is_advisor
        }
        validate_user_advisor_status(attrs_to_validate)
        
        return attrs

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "user_type",
            "user_classes",
            "team",
            "name_search",
            "registration",
            "is_evaluator",
            "is_advisor",
            "is_collaborator",
            "specialities"
        ]
        depth=2
    def Create(self, validated_data):
        return User.objects.create_user(**validated_data)

class EvaluatorUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "user_type",
        ]


class EvaluatorSerializer(serializers.ModelSerializer):
    user = EvaluatorUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.exclude(user_type=User.STUDENT),
        source='user',
        write_only=True
    )
    
    def validate_user_id(self, value):
        # Usando validação do domínio para avaliadores
        validate_evaluator_creation(value)
        return value
    
    class Meta:
        model = Evaluator
        fields = ["id", "user", "user_id"]

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('É necessário fornecer email e senha.')


        user = authenticate(request=self.context.get('request'), email=email, password=password)


        if not user:
            raise serializers.ValidationError('Email ou senha inválidos.')

        # Marcar confirmação na primeira autenticação bem-sucedida (evita reautenticar)
        if not user.is_confirmed:
            from django.db import transaction
            with transaction.atomic():
                User.objects.filter(id=user.id).update(is_confirmed=True)

        # Evita uma segunda chamada a authenticate feita por super().validate
        # Geramos os tokens diretamente
        self.user = user
        refresh = self.get_token(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return data
class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id", "name"]
        depth = 1

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name"]
        depth = 1
        
class CertificateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Certificate
        fields = ["id", "user_id", "work_id", "hash_validate", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
