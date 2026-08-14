"""
Management command para importar/atualizar alunos de 2026 a partir dos CSVs.

Execute com: python manage.py import_students_2026 [--dry-run]
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from core.user.infra.user_django_app.models import User, Class, UserClass
import unicodedata


def remove_accent(text):
    """Remove acentos de um texto"""
    if not text:
        return text
    text_normal = unicodedata.normalize('NFKD', text)
    text_without_accent = ''.join(c for c in text_normal if not unicodedata.combining(c))
    return text_without_accent


class Command(BaseCommand):
    help = 'Importa/atualiza alunos de 2026 a partir dos CSVs da pasta corrigidos'

    def _log(self, message, flush=True):
        """Helper para log com flush"""
        self.stdout.write(message)
        if flush:
            self.stdout.flush()
            sys.stdout.flush()

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem salvar no banco (apenas mostra o que seria feito)',
        )
        parser.add_argument(
            '--csv-dir',
            type=str,
            default='corrigidos',
            help='Diretório com os CSVs (padrão: corrigidos)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        csv_dir = options['csv_dir']

        # Determinar o caminho do diretório de CSVs
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent
        csv_path = base_dir / csv_dir

        if not csv_path.exists():
            self._log(self.style.ERROR(f"Diretório não encontrado: {csv_path}"))
            return

        self._log("=" * 80)
        if dry_run:
            self._log(self.style.WARNING("MODO DRY-RUN - Nenhuma alteração será salva"))
        else:
            self._log(self.style.WARNING("MODO PRODUÇÃO - Alterações serão salvas no banco"))
        self._log("=" * 80)
        self._log("")

        # Testar conexão com banco
        self._log("Testando conexão com banco de dados...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_name = connection.settings_dict.get('NAME', 'unknown')
                db_host = connection.settings_dict.get('HOST', 'localhost')
                db_port = connection.settings_dict.get('PORT', '5432')
            self._log(f"✓ Conexão estabelecida com sucesso!")
            self._log(f"  Banco: {db_name}")
            self._log(f"  Host: {db_host}:{db_port}")
            self._log("")
        except Exception as e:
            self._log(self.style.ERROR(f"✗ Erro ao conectar com banco: {e}"))
            return

        # Encontrar todos os CSVs
        csv_files = list(csv_path.glob('*.csv'))
        if not csv_files:
            self._log(self.style.ERROR(f"Nenhum CSV encontrado em: {csv_path}"))
            return

        self._log(f"Encontrados {len(csv_files)} arquivos CSV")
        self._log("")

        stats = {
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0,
        }

        # Processar cada CSV
        csv_count = 0
        for csv_file in sorted(csv_files):
            if csv_file.suffix.lower() != '.csv':
                continue

            csv_count += 1
            class_name = csv_file.stem  # Nome do arquivo sem extensão
            self._log(f"\n[{csv_count}/{len(csv_files)}] Processando: {class_name}.csv")

            try:
                result = self._process_csv(csv_file, class_name, dry_run)
                stats['created'] += result['created']
                stats['updated'] += result['updated']
                stats['errors'] += result['errors']
                stats['skipped'] += result['skipped']
            except Exception as e:
                self._log(self.style.ERROR(f"  ERRO ao processar: {e}"))
                stats['errors'] += 1

        # Resumo final
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("📊 RESUMO DA IMPORTAÇÃO"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"✅ Alunos criados: {stats['created']}")
        self.stdout.write(f"🔄 Alunos atualizados: {stats['updated']}")
        self.stdout.write(f"⏭️  Alunos ignorados: {stats['skipped']}")
        self.stdout.write(f"❌ Erros: {stats['errors']}")
        self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  DRY-RUN: Nenhuma alteração foi salva"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Importação concluída!"))

    def _process_csv(self, csv_file, class_name, dry_run):
        """Processa um único arquivo CSV"""
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        # Determinar o ano da turma (1º, 2º ou 3º)
        year_digit = class_name[0]
        if year_digit not in ['1', '2', '3']:
            self._log(self.style.WARNING(f"  Nome de turma inválido: {class_name}"))
            stats['errors'] += 1
            return stats

        # Criar ou obter a turma
        self._log(f"  Verificando turma {class_name}...")
        if not dry_run:
            class_obj, class_created = Class.objects.get_or_create(name=class_name)
            if class_created:
                self._log(f"  + Turma CRIADA: {class_name}")
            else:
                self._log(f"  = Turma já existe: {class_name}")
        else:
            class_obj = None
            self._log(f"  [DRY-RUN] Turma: {class_name}")

        # Ler o CSV
        self._log(f"  Lendo CSV...")
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')

                total_lines = sum(1 for line in open(csv_file, 'r', encoding='utf-8-sig')) - 1
                self._log(f"  Total de alunos no CSV: {total_lines}")
                self._log(f"  Processando...")

                for row_num, row in enumerate(reader, start=2):
                    try:
                        result = self._process_student(row, class_obj, class_name, dry_run, row_num, total_lines + 1)
                        if result == 'created':
                            stats['created'] += 1
                        elif result == 'updated':
                            stats['updated'] += 1
                        elif result == 'skipped':
                            stats['skipped'] += 1

                        # Log de progresso a cada 10 alunos
                        if row_num % 10 == 0:
                            self._log(f"    Progresso: {row_num - 1}/{total_lines} alunos processados")

                    except Exception as e:
                        self._log(self.style.ERROR(f"  ERRO na linha {row_num}: {e}"))
                        stats['errors'] += 1

        except Exception as e:
            self._log(self.style.ERROR(f"  ERRO ao ler CSV: {e}"))
            stats['errors'] += 1

        self._log(
            f"  RESUMO: {stats['created']} criados | "
            f"{stats['updated']} atualizados | "
            f"{stats['errors']} erros"
        )

        return stats

    def _process_student(self, row, class_obj, class_name, dry_run, row_num=None, total=None):
        """Processa um único aluno"""
        # Extrair dados do CSV
        matricula = row.get('matricula', '').strip()
        nome = row.get('nome', '').strip()

        if not matricula or not nome:
            raise ValueError("Matrícula ou nome ausente")

        try:
            registration = int(matricula)
        except ValueError:
            raise ValueError(f"Matrícula inválida: {matricula}")

        # Gerar email baseado na matrícula
        email = f"{registration}@aluno.ifc.edu.br"

        # Preparar dados do aluno
        name_search = remove_accent(nome.lower())

        # Verificar se o aluno já existe
        existing_user = User.objects.filter(registration=registration).first()

        if dry_run:
            if existing_user:
                return 'updated'
            else:
                return 'created'

        # Criar ou atualizar o usuário
        with transaction.atomic():
            if existing_user:
                # Atualizar dados do aluno existente
                existing_user.name = nome
                existing_user.name_search = name_search
                existing_user.email = email
                existing_user.user_type = User.STUDENT
                existing_user.save()

                user = existing_user
                action = 'updated'
            else:
                # Criar novo aluno
                user = User.objects.create(
                    registration=registration,
                    name=nome,
                    name_search=name_search,
                    email=email,
                    user_type=User.STUDENT,
                    is_confirmed=False,
                )
                # Definir senha padrão (pode ser alterada depois)
                user.set_password('ifc2026')
                user.save()

                action = 'created'

            # Criar ou atualizar UserClass para 2026
            user_class, uc_created = UserClass.objects.get_or_create(
                user=user,
                year=2026,
                defaults={'class_name': class_obj}
            )

            if not uc_created and user_class.class_name != class_obj:
                # Atualizar turma se mudou
                user_class.class_name = class_obj
                user_class.save()

        return action


    def _print_summary(self, context):
        """Imprime resumo da importação"""
        pass
