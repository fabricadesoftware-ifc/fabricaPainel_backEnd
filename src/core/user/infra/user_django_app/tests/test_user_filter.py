from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.user.infra.user_django_app.models import User


class UserFilterTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher = User.objects.create_user(
            email="eduardo.teacher@test.local",
            password="password-123",
            name="Eduárdo Professor",
            registration=910001,
            user_type=User.TEACHER,
        )
        User.objects.create_user(
            email="eduardo.student@test.local",
            password="password-123",
            name="Eduardo Aluno",
            registration=910002,
            user_type=User.STUDENT,
        )

    def test_user_name_filter_does_not_require_database_unaccent_function(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get("/api/users/", {"name": "eduardo", "type": "TEACHER"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([user["id"] for user in response.json()], [self.teacher.id])
