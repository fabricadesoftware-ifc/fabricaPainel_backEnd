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


class PasswordResetInputNormalizationTest(TestCase):
    """Celular manda o código com espaço sobrando ou a 1ª letra maiúscula."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="aluno.celular@test.local",
            password="old-password-123",
            name="Aluno Celular",
            registration=900002,
        )

    def _arm(self):
        self.user.password_reset_token = "a1b2c3d4"
        self.user.password_reset_token_created = timezone.now()
        self.user.save()

    def test_validate_and_reset_accept_sloppy_token_input(self):
        for sent in ("a1b2c3d4 ", " a1b2c3d4", "A1b2c3d4", "A1B2C3D4", "\ta1b2c3d4\n"):
            with self.subTest(sent=sent):
                self._arm()
                validate = self.client.post("/api/validate_password_token/", {"token": sent}, format="json")
                self.assertEqual(validate.status_code, status.HTTP_200_OK)

                self._arm()
                reset = self.client.post(
                    "/api/reset_password/", {"token": sent, "new_password": "novaSenha123"}, format="json"
                )
                self.assertEqual(reset.status_code, status.HTTP_200_OK)
                self.user.refresh_from_db()
                self.assertTrue(self.user.check_password("novaSenha123"))
                self.assertIsNone(self.user.password_reset_token)

    def test_wrong_token_is_still_rejected(self):
        self._arm()
        response = self.client.post("/api/validate_password_token/", {"token": "ffffffff"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_blank_or_non_string_token_is_a_bad_request(self):
        for sent in ("", "   ", None, 12345):
            with self.subTest(sent=sent):
                response = self.client.post("/api/validate_password_token/", {"token": sent}, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_forget_password_accepts_email_with_case_and_spaces(self):
        from unittest import mock

        for sent in ("aluno.celular@test.local", "Aluno.Celular@Test.local", "  aluno.celular@test.local "):
            with self.subTest(sent=sent):
                with mock.patch(
                    "core.user.infra.user_django_app.utils.forget_password.send_forget_password_email"
                ) as task:
                    response = self.client.post("/api/forget_password/", {"email": sent}, format="json")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # o e-mail sai para o endereço salvo, não para o texto digitado
                self.assertEqual(task.delay.call_args.args[0], "aluno.celular@test.local")

    def test_forget_password_unknown_or_missing_email_is_404(self):
        for sent in ("ninguem@test.local", "", None):
            with self.subTest(sent=sent):
                response = self.client.post("/api/forget_password/", {"email": sent}, format="json")
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
