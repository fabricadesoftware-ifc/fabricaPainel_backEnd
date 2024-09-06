from rest_framework.viewsets import ModelViewSet

from .models import User, Evaluator
from .serializers import UserSerializer, EvaluatorSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class EvaluatorViewSet(ModelViewSet):
    queryset = Evaluator.objects.all()
    serializer_class = EvaluatorSerializer