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


class CertificateSinglePageTest(SimpleTestCase):
    """Texto longo não pode empurrar o rodapé (QR/código) para uma 2ª página."""

    LONG_NAME = "Ana Beatriz de Oliveira Figueiredo Nascimento da Silva Pereira Santos"
    LONG_TITLE = (
        "Desenvolvimento de uma plataforma web integrada para gestão colaborativa de "
        "projetos de extensão tecnológica voltados à inclusão digital de comunidades "
        "ribeirinhas e quilombolas com análise de impacto social e ambiental regional"
    )

    def _pages(self, name, title):
        from weasyprint import HTML

        certificate = SimpleNamespace(id=1, hash_validate=HASH)
        work = SimpleNamespace(title=title, edition=SimpleNamespace(workload="40 horas"))
        html = generate_certificates.render_certificate_html(
            certificate, work, SimpleNamespace(name=name)
        )
        return len(HTML(string=html).render().pages)

    @override_settings(PAINEL_URL="https://painel.fabricadesoftware.ifc.edu.br")
    def test_short_and_long_texts_fit_one_page(self):
        self.assertEqual(self._pages("Ana Souza", "Projeto Curto"), 1)
        self.assertEqual(self._pages(self.LONG_NAME, self.LONG_TITLE), 1)
