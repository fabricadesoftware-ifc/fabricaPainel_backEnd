from rest_framework import serializers

from .models import User, Evaluator


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class EvaluatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluator
        fields = "__all__"