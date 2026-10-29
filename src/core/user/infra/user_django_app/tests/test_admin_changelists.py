from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdminChangelistTest(TestCase):
    """Toda tela de listagem do admin abre (monta filtros) e aceita busca."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            email="admin@example.com", password="x", name="Admin"
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_changelists_open_with_search_and_filters(self):
        for model, model_admin in admin.site._registry.items():
            opts = model._meta
            url = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
            with self.subTest(model=opts.label):
                self.assertEqual(self.client.get(url).status_code, 200)
                if model_admin.search_fields:
                    self.assertEqual(self.client.get(url, {"q": "a"}).status_code, 200)

    def test_assessments_has_readable_plural(self):
        from core.assessment.infra.assessment_django_app.models import Assessments

        self.assertNotIn("Assessmentss", str(Assessments._meta.verbose_name_plural))
