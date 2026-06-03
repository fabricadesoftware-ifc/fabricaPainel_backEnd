from django.test import TestCase

from core.user.domain.value_objects import UserType
from core.user.infra.user_django_app.models import Evaluator, User
from core.user.infra.user_django_app.serializers import EvaluatorSerializer, UserSerializer


class UserRoleValidationTest(TestCase):
    def create_user(self, email, user_type, **flags):
        user = User.objects.create_user(
            email=email,
            password="test-password-123",
            name=email.split("@")[0],
            registration=2026003000 + User.objects.count(),
        )
        user.user_type = user_type
        for field, value in flags.items():
            setattr(user, field, value)
        user.save()
        return user

    def test_student_cannot_be_marked_as_advisor(self):
        serializer = UserSerializer(
            data={
                "email": "student.advisor@test.local",
                "name": "Student Advisor",
                "registration": 2026003101,
                "user_type": UserType.Type.STUDENT.value,
                "is_advisor": True,
                "is_collaborator": False,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("is_advisor", str(serializer.errors))

    def test_student_cannot_be_marked_as_collaborator(self):
        serializer = UserSerializer(
            data={
                "email": "student.collaborator@test.local",
                "name": "Student Collaborator",
                "registration": 2026003102,
                "user_type": UserType.Type.STUDENT.value,
                "is_advisor": False,
                "is_collaborator": True,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("is_collaborator", str(serializer.errors))

    def test_student_cannot_be_created_as_evaluator(self):
        student = self.create_user("student.evaluator@test.local", UserType.Type.STUDENT.value)
        serializer = EvaluatorSerializer(data={"user_id": student.id})

        self.assertFalse(serializer.is_valid())
        self.assertIn("Pk inválido", str(serializer.errors))

    def test_user_cannot_be_created_as_evaluator_twice(self):
        teacher = self.create_user("teacher.evaluator@test.local", UserType.Type.TEACHER.value)
        Evaluator.objects.create(user=teacher)
        serializer = EvaluatorSerializer(data={"user_id": teacher.id})

        self.assertFalse(serializer.is_valid())
        self.assertIn("já é um avaliador", str(serializer.errors))
