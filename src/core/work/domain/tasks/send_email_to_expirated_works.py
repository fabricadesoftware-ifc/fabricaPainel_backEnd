import os
import logging
from io import BytesIO
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from weasyprint import HTML
from django.template.loader import render_to_string
from django.template import engines

logger = logging.getLogger(__name__)

trabalhos_data = [
    {
        "id": 1,
        "nome": "Sistema de Gestão Acadêmica",
        "descricao": "Desenvolvimento de um sistema completo para gestão de alunos, professores e disciplinas",
        "data_entrega": "2024-12-15",
        "status": "Em desenvolvimento",
        "materias_integradas": ["Português", "Matemática", "Informática", "Gestão"],
        "alunos": [
            "Ana Silva Santos",
            "Carlos Eduardo Oliveira",
            "Maria Fernanda Costa",
            "João Pedro Almeida"
        ]
    },
    {
        "id": 2,
        "nome": "Plataforma de E-commerce",
        "descricao": "Criação de uma plataforma para venda de produtos online com integração de pagamento",
        "data_entrega": "2023-11-30",
        "status": "Concluído",
        "materias_integradas": ["Economia", "Administração", "Programação Web"],
        "alunos": [
            "Lucas Pereira",
            "Fernanda Souza",
            "Gabriel Lima",
            "Juliana Alves"
        ]
    },
    {
        "id": 3,
        "nome": "Aplicativo de Saúde",
        "descricao": "Desenvolvimento de um aplicativo para monitoramento de saúde e bem-estar",
        "data_entrega": "2025-03-20",
        "status": "Planejado",
        "materias_integradas": ["Biologia", "Educação Física", "Programação Mobile"],
        "alunos": [
            "Rafael Mendes",
            "Beatriz Rocha",
            "Thiago Silva",
            "Camila Santos"
        ]
    },
    {
        "id": 4,
        "nome": "Sistema de Controle Financeiro",
        "descricao": "Sistema para gestão de finanças pessoais e empresariais",
        "data_entrega": "2024-06-10",
        "status": "Em desenvolvimento",
        "materias_integradas": ["Matemática Financeira", "Contabilidade", "Programação"],
        "alunos": [
            "Pedro Henrique",
            "Larissa Carvalho",
            "Marcos Vinícius",
            "Isabela Nogueira"
        ]
    },
    {
        "id": 5,
        "nome": "Plataforma de Ensino Online",
        "descricao": "Plataforma para cursos online com suporte a videoaulas e quizzes",
        "data_entrega": "2023-09-01",
        "status": "Concluído",
        "materias_integradas": ["Pedagogia", "Tecnologia Educacional", "Design de Interface"],
        "alunos": [
            "Eduardo Ramos",
            "Sofia Martins",
            "Renato Oliveira",
            "Carolina Dias"
        ]
    }
]

@shared_task
def send_email_to_expirated_works(to_email):
    try:
        template_path = os.path.join(settings.BASE_DIR, 'templates', 'expirated_works.html')

        context = {
            "trabalhos_data": trabalhos_data
        }

        with open(template_path, 'r', encoding='utf-8') as template_file:
            template_code = template_file.read()

        html_string = engines['django'].from_string(template_code).render(context)

        pdf_file = BytesIO()
        HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf(target=pdf_file)
        pdf_file.seek(0)

        email = EmailMessage(
            subject='Relatório em PDF - Celery Task',
            body='Olá, segue em anexo o PDF gerado a partir do template HTML.',
            from_email='anthonylocheifc@gmail.com',
            to=[to_email],
        )
        email.attach('relatorio.pdf', pdf_file.read(), 'application/pdf')
        email.send()

        logger.info(f"E-mail com PDF enviado para {to_email}")
        return f"E-mail com PDF enviado para {to_email}"

    except Exception as e:
        logger.exception(f"Erro ao gerar ou enviar o PDF para {to_email}: {e}")
        return f"Erro: {e}"