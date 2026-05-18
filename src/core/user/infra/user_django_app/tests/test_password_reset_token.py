from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.user.infra.user_django_app.models import User


@override_settings(TOKEN_EXPIRATION_SECONDS=1200)
class PasswordResetTokenFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="student.token@test.local",
            password="old-password-123",
            name="Student Token",
            registration=900001,
        )

    def _set_reset_token(self, token, created_at):
        self.user.password_reset_token = token
        self.user.password_reset_token_created = created_at
        self.user.save(update_fields=["password_reset_token", "password_reset_token_created"])

    def test_validate_password_token_accepts_unexpired_token(self):
        self._set_reset_token("valid-token", timezone.now() - timedelta(minutes=5))

        response = self.client.post(
            "/api/validate_password_token/",
            {"token": "valid-token"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validate_password_token_expires_old_token(self):
        self._set_reset_token("expired-token", timezone.now() - timedelta(minutes=30))

        response = self.client.post(
            "/api/validate_password_token/",
            {"token": "expired-token"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.password_reset_token)
        self.assertIsNone(self.user.password_reset_token_created)

    def test_validate_password_token_rejects_token_without_creation_date(self):
        self._set_reset_token("missing-created-at-token", None)

        response = self.client.post(
            "/api/validate_password_token/",
            {"token": "missing-created-at-token"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.password_reset_token)

    def test_reset_password_accepts_unexpired_token_and_clears_it(self):
        self._set_reset_token("reset-token", timezone.now() - timedelta(minutes=5))

        response = self.client.post(
            "/api/reset_password/",
            {"token": "reset-token", "new_password": "new-password-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-password-123"))
        self.assertIsNone(self.user.password_reset_token)
        self.assertIsNone(self.user.password_reset_token_created)
