from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from core.user.domain.validations import (
    validate_user_collaborator_status, 
    validate_evaluator_creation,
    validate_user_advisor_status
)

from .models import User, Evaluator, Class, UserClass


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
            "is_collaborator"
        ]
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

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            user = User.objects.get(email=email)
            user.is_confirmed = True
            user.save()
            if not user:
                raise serializers.ValidationError('Invalid email or password')
        else:
            raise serializers.ValidationError('Must include "email" and "password"')

        return super().validate(attrs)
    
class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id", "name"]
        depth = 1

