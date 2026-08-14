"""
Management command para importar/atualizar os alunos calouros (1º ano) de 2026
a partir do CSV consolidado corrigidos/alunos_calouros.csv.

Diferente do import_students_2026 (que sintetiza o email como
"{matricula}@aluno.ifc.edu.br" a partir de arquivos por turma sem coluna de
email), este comando lê o email real de cada aluno diretamente do CSV — foi
por falta desse email real que os calouros ficaram de fora da primeira
importação.

O CSV tem um único arquivo para todas as turmas de 1º ano, com colunas:
Matricula;Nome;Email;Turma (separado por ";")

Execute com: python manage.py import_freshman_students_2026 [--dry-run]
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from core.user.infra.user_django_app.models import User, Class, UserClass
from django_project.settings import BASE_DIR
import unicodedata


def remove_accent(text):
    """Remove acentos de um texto"""
    if not text:
        return text
    text_normal = unicodedata.normalize('NFKD', text)
    text_without_accent = ''.join(c for c in text_normal if not unicodedata.combining(c))
    return text_without_accent


def resolve_email(row):
    """
    Retorna (email, usou_fallback). Alunos sem email real no CSV (campo vazio
    ou placeholder "sememail@...") recebem "{matricula}@ifc.edu.br" no lugar,
    a pedido explícito da fábrica de software.
    """
    raw_email = (row.get('Email') or '').strip().lower()
    matricula = (row.get('Matricula') or '').strip()
    local_part = raw_email.split('@', 1)[0] if '@' in raw_email else raw_email

    if not raw_email or local_part == 'sememail':
        return f"{matricula}@ifc.edu.br", True
    return raw_email, False


class Command(BaseCommand):
    help = 'Importa/atualiza alunos calouros (1º ano) de 2026 a partir de corrigidos/alunos_calouros.csv'

    def _log(self, message, flush=True):
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
            '--csv-file',
            type=str,
            default='corrigidos/alunos_calouros.csv',
            help='Caminho do CSV consolidado (padrão: corrigidos/alunos_calouros.csv)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # BASE_DIR (settings.py) já aponta para a pasta "src"; a pasta "corrigidos"
        # fica um nível acima, na raiz do backend.
        base_dir = Path(BASE_DIR).parent
        csv_path = base_dir / options['csv_file']

        if not csv_path.exists():
            self._log(self.style.ERROR(f"Arquivo não encontrado: {csv_path}"))
            return

        self._log("=" * 80)
        self._log(
            self.style.WARNING("MODO DRY-RUN - Nenhuma alteração será salva")
            if dry_run else
            self.style.WARNING("MODO PRODUÇÃO - Alterações serão salvas no banco")
        )
        self._log("=" * 80)
        self._log("")

        self._log("Testando conexão com banco de dados...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_name = connection.settings_dict.get('NAME', 'unknown')
            self._log(f"✓ Conexão estabelecida com sucesso! Banco: {db_name}")
            self._log("")
        except Exception as e:
            self._log(self.style.ERROR(f"✗ Erro ao conectar com banco: {e}"))
            return

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = [row for row in reader if any((row.get(k) or '').strip() for k in row)]

        self._log(f"Lidas {len(rows)} linhas de {csv_path.name}")
        self._log("")

        rows, conflicts = self._filter_conflicting_rows(rows)

        if conflicts:
            self._log(self.style.WARNING(f"⚠️  {len(conflicts)} linha(s) IGNORADA(S) por conflito de dados:"))
            for reason, row in conflicts:
                self._log(
                    f"    - {reason}: matrícula {row.get('Matricula')} | "
                    f"{row.get('Nome')} | {row.get('Email')} | turma {row.get('Turma')}"
                )
            self._log("")

        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
        class_cache = {}

        for row_num, row in enumerate(rows, start=2):
            try:
                result = self._process_student(row, class_cache, dry_run)
                stats[result] = stats.get(result, 0) + 1
            except Exception as e:
                self._log(self.style.ERROR(
                    f"  ERRO na linha {row_num} (matrícula {row.get('Matricula')}): {e}"
                ))
                stats['errors'] += 1

        self._log("")
        self._log("=" * 80)
        self._log(self.style.SUCCESS("📊 RESUMO DA IMPORTAÇÃO"))
        self._log("=" * 80)
        self._log(f"✅ Alunos criados: {stats['created']}")
        self._log(f"🔄 Alunos atualizados: {stats['updated']}")
        self._log(f"⏭️  Ignorados por conflito: {len(conflicts)}")
        self._log(f"❌ Erros: {stats['errors']}")
        self._log("")

        if dry_run:
            self._log(self.style.WARNING("⚠️  DRY-RUN: Nenhuma alteração foi salva"))
        else:
            self._log(self.style.SUCCESS("✅ Importação concluída!"))

    def _filter_conflicting_rows(self, rows):
        """
        Detecta e separa linhas que não podem ser importadas com segurança:
          - o mesmo email (já resolvido, com fallback matricula@ifc.edu.br
            aplicado) aparecendo em matrículas diferentes — email é único no banco
          - a mesma matrícula aparecendo mais de uma vez com dados diferentes
        Alunos sem email real (campo vazio ou "sememail@...") NÃO são
        considerados conflito: recebem o fallback e seguem para a importação.
        Retorna (linhas_validas, [(motivo, linha), ...]).
        """
        by_email = defaultdict(list)
        by_matricula = defaultdict(list)

        for row in rows:
            email, _ = resolve_email(row)
            matricula = (row.get('Matricula') or '').strip()
            if email:
                by_email[email].append(row)
            if matricula:
                by_matricula[matricula].append(row)

        conflicting_ids = set()
        conflicts = []

        for email, dup_rows in by_email.items():
            matriculas = {(r.get('Matricula') or '').strip() for r in dup_rows}
            if len(dup_rows) > 1 and len(matriculas) > 1:
                for row in dup_rows:
                    if id(row) not in conflicting_ids:
                        conflicts.append((f"email '{email}' duplicado em outra matrícula", row))
                        conflicting_ids.add(id(row))

        for matricula, dup_rows in by_matricula.items():
            if len(dup_rows) > 1:
                # mesma matricula com turma/email diferentes entre as linhas = conflito real
                signatures = {(r.get('Turma', '').strip(), resolve_email(r)[0]) for r in dup_rows}
                if len(signatures) > 1:
                    for row in dup_rows:
                        if id(row) not in conflicting_ids:
                            conflicts.append((f"matrícula '{matricula}' com dados divergentes entre linhas", row))
                            conflicting_ids.add(id(row))

        valid_rows = [row for row in rows if id(row) not in conflicting_ids]
        return valid_rows, conflicts

    def _process_student(self, row, class_cache, dry_run):
        matricula = (row.get('Matricula') or '').strip()
        nome = (row.get('Nome') or '').strip()
        email, used_fallback_email = resolve_email(row)
        turma = (row.get('Turma') or '').strip()

        if not matricula or not nome or not turma:
            raise ValueError("Matrícula, nome ou turma ausente")

        try:
            registration = int(matricula)
        except ValueError:
            raise ValueError(f"Matrícula inválida: {matricula}")

        name_search = remove_accent(nome.lower())

        if used_fallback_email:
            self._log(f"    ℹ️  {nome} (matrícula {matricula}) sem email real no CSV — usando {email}")

        if dry_run:
            return 'updated' if User.objects.filter(registration=registration).exists() else 'created'

        with transaction.atomic():
            class_obj = class_cache.get(turma)
            if class_obj is None:
                class_obj, _ = Class.objects.get_or_create(name=turma)
                class_cache[turma] = class_obj

            existing_by_registration = User.objects.filter(registration=registration).first()
            email_owner = User.objects.filter(email=email).exclude(registration=registration).first()
            if email_owner:
                raise ValueError(
                    f"email '{email}' já pertence a outro usuário (matrícula {email_owner.registration})"
                )

            if existing_by_registration:
                existing_by_registration.name = nome
                existing_by_registration.name_search = name_search
                existing_by_registration.email = email
                existing_by_registration.user_type = User.STUDENT
                existing_by_registration.save()
                user = existing_by_registration
                action = 'updated'
            else:
                user = User.objects.create(
                    registration=registration,
                    name=nome,
                    name_search=name_search,
                    email=email,
                    user_type=User.STUDENT,
                    is_confirmed=False,
                )
                user.set_password('ifc2026')
                user.save()
                action = 'created'

            user_class, uc_created = UserClass.objects.get_or_create(
                user=user,
                year=2026,
                defaults={'class_name': class_obj},
            )
            if not uc_created and user_class.class_name != class_obj:
                user_class.class_name = class_obj
                user_class.save()

        return action
