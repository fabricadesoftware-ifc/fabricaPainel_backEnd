from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

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
    user = EvaluatorUserSerializer()
    class Meta:
        model = Evaluator
        fields = "__all__"
        depth = 1

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

