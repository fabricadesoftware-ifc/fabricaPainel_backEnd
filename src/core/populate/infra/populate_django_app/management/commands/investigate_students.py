"""
Management command para investigar alunos existentes no banco de produção.
APENAS LEITURA - Não faz alterações.

Execute com: python manage.py investigate_students
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from core.user.infra.user_django_app.models import User, Class, UserClass
from collections import defaultdict


class Command(BaseCommand):
    help = 'Investiga alunos existentes no banco de produção (apenas leitura)'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("INVESTIGAÇÃO DO BANCO DE PRODUÇÃO - APENAS LEITURA")
        self.stdout.write("=" * 80)
        self.stdout.write("")

        # 1. Contar total de alunos
        total_students = User.objects.filter(user_type='student').count()
        self.stdout.write(f"📊 Total de alunos no sistema: {total_students}")
        self.stdout.write("")

        # 2. Contar alunos por ano no UserClass
        self.stdout.write("📅 Distribuição de alunos por ano:")
        years_distribution = UserClass.objects.values('year').annotate(
            count=Count('id')
        ).order_by('year')

        for item in years_distribution:
            year = item['year']
            count = item['count']
            self.stdout.write(f"  - Ano {year}: {count} registros")
        self.stdout.write("")

        # 3. Listar turmas existentes
        self.stdout.write("🏫 Turmas cadastradas:")
        classes = Class.objects.all().order_by('name')
        for cls in classes:
            self.stdout.write(f"  - {cls.name}")
        self.stdout.write(f"Total: {classes.count()} turmas")
        self.stdout.write("")

        # 4. Distribuição de alunos por turma e ano
        self.stdout.write("👥 Alunos por turma e ano:")
        user_classes = UserClass.objects.select_related('class_name', 'user').order_by('year', 'class_name__name')

        # Agrupar por ano e turma
        distribution = defaultdict(lambda: defaultdict(list))

        for uc in user_classes:
            if uc.user:  # Apenas se o user não for None
                year = uc.year
                class_name = uc.class_name.name
                distribution[year][class_name].append(uc.user.name)

        for year in sorted(distribution.keys()):
            self.stdout.write(f"\n  📆 ANO {year}:")
            for class_name in sorted(distribution[year].keys()):
                students = distribution[year][class_name]
                self.stdout.write(f"    {class_name}: {len(students)} alunos")
                # Mostrar alguns exemplos
                if len(students) > 0:
                    examples = ', '.join(students[:3])
                    self.stdout.write(f"      Exemplos: {examples}")
                    if len(students) > 3:
                        self.stdout.write(f"      ... e mais {len(students) - 3}")

        self.stdout.write("")

        # 5. Identificar alunos do 3º ano de 2024 (NÃO MEXER)
        self.stdout.write("⚠️  ALUNOS DO 3º ANO DE 2024 (NÃO MEXER):")
        third_year_2024 = UserClass.objects.filter(year=2024).select_related('class_name', 'user')
        third_year_count = third_year_2024.count()
        self.stdout.write(f"  Total: {third_year_count} registros")

        # Agrupar por turma
        third_year_classes = defaultdict(int)
        for uc in third_year_2024:
            third_year_classes[uc.class_name.name] += 1

        for class_name, count in sorted(third_year_classes.items()):
            self.stdout.write(f"    {class_name}: {count} alunos")

        self.stdout.write("")

        # 6. Análise de matrículas
        self.stdout.write("🔢 Análise de matrículas:")
        students_with_registration = User.objects.filter(
            user_type='student',
            registration__isnull=False
        ).order_by('registration')

        if students_with_registration.exists():
            first_registration = students_with_registration.first().registration
            last_registration = students_with_registration.last().registration
            self.stdout.write(f"  Primeira matrícula: {first_registration}")
            self.stdout.write(f"  Última matrícula: {last_registration}")

            # Contar por prefixo de ano
            registrations_2024 = User.objects.filter(
                user_type='student',
                registration__gte=2024000000,
                registration__lt=2025000000
            ).count()
            registrations_2025 = User.objects.filter(
                user_type='student',
                registration__gte=2025000000,
                registration__lt=2026000000
            ).count()
            registrations_2026 = User.objects.filter(
                user_type='student',
                registration__gte=2026000000,
                registration__lt=2027000000
            ).count()

            self.stdout.write(f"  Matrículas 2024*: {registrations_2024}")
            self.stdout.write(f"  Matrículas 2025*: {registrations_2025}")
            self.stdout.write(f"  Matrículas 2026*: {registrations_2026}")

        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ Investigação concluída!"))
        self.stdout.write("=" * 80)
