import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from core.user.domain.tasks import generate_certificates
from core.user.domain.tasks.generate_certificates import build_validation_url

HASH = "a1" * 32


class CertificateValidationLinkTest(SimpleTestCase):
    @override_settings(PAINEL_URL="https://painel.exemplo.br/")
    def test_validation_url_points_to_public_page(self):
        self.assertEqual(
            build_validation_url(HASH),
            f"https://painel.exemplo.br/validar-certificado/{HASH}",
        )

    @override_settings(PAINEL_URL="https://painel.exemplo.br")
    def test_pdf_html_has_qr_link_and_escaped_values(self):
        captured = {}

        class FakeHTML:
            def __init__(self, string):
                captured["html"] = string

            def write_pdf(self, path):
                captured["path"] = path

        certificate = SimpleNamespace(id=1, hash_validate=HASH)
        work = SimpleNamespace(
            title="Robô <script>x</script>", edition=SimpleNamespace(workload="40 horas")
        )
        user = SimpleNamespace(name="Ana & Bia")

        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            with patch.object(generate_certificates, "HTML", FakeHTML):
                path = generate_certificates.generate_certificate_pdf(certificate, work, user)

        html = captured["html"]
        self.assertEqual(os.path.basename(path), "certificate_1.pdf")
        self.assertIn(f"https://painel.exemplo.br/validar-certificado/{HASH}", html)
        self.assertIn("data:image/svg+xml", html)
        self.assertIn("Ana &amp; Bia", html)
        self.assertNotIn("<script>", html)
        # Nenhum marcador do template pode sobrar sem substituição.
        self.assertNotIn("{{", html)
        # Classes e CSS do template não podem ser trocadas pelo hash.
        self.assertIn('class="hash"', html)
