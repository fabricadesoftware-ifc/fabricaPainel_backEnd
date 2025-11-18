import hashlib
import time
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# Ajuste o caminho de importação para seus modelos
from your_app.models import Work, StudentAssessment, Assessment, Certificate, User

class Command(BaseCommand):
    """
    Verifica trabalhos concluídos e cria registros de certificados para alunos
    aprovados. Esta tarefa é idempotente e projetada para ser executada
    periodicamente.
    """
    help = 'Cria registros de certificados para alunos elegíveis.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Iniciando a tarefa de verificação e criação de certificados..."))
        
        # Busca apenas trabalhos que já terminaram e que
        # ainda não tiveram seus certificados processados.
        today = date.today()
        works_to_process = Work.objects.filter(
            final_evaluators_date__lt=today,
            certificates_generated_at__isnull=True
        )

        if not works_to_process.exists():
            self.stdout.write(self.style.SUCCESS("Nenhum trabalho novo para processar."))
            return

        self.stdout.write(f"Encontrados {works_to_process.count()} trabalhos para processar.")
        total_certificates_created = 0

        # Loop principal: processa um trabalho de cada vez
        for work in works_to_process:
            self.stdout.write(self.style.NOTICE(f"\nProcessando trabalho: '{work.name}' (ID: {work.id})"))

            # ======================================================================
            # PARTE 1: VERIFICAÇÃO DOS REQUISITOS (VALIDAÇÃO)
            # ======================================================================
            # Confirma se as condições para gerar o certificado foram atendidas.

            #  1: O trabalho/grupo deve ter uma nota de avaliação válida.
            has_valid_work_grade = Assessment.objects.filter(
                work=work,
                grade__isnull=False,
                grade__gte=5.0  # Regra de negócio: Nota mínima de aprovação do grupo.
            ).exists()

            if not has_valid_work_grade:
                self.stdout.write(self.style.WARNING(f"  -> FALHA NA VERIFICAÇÃO: O trabalho não possui nota de grupo válida. Pulando."))
                continue # Pula para o próximo trabalho

            # 2: Deve haver alunos com nota individual suficiente.
            # Buscamos as avaliações que atendem ao critério.
            eligible_students_assessments = StudentAssessment.objects.filter(
                work=work,
                grade__isnull=False,
                grade__gte=5.0  
            ).select_related('user') # Otimização para já buscar os dados do aluno.

            if not eligible_students_assessments.exists():
                self.stdout.write(self.style.WARNING(f"  -> FALHA NA VERIFICAÇÃO: Nenhum aluno atingiu a nota mínima individual. Pulando."))
                continue # Pula para o próximo trabalho

            self.stdout.write(self.style.SUCCESS(f"  -> VERIFICAÇÃO OK: {eligible_students_assessments.count()} aluno(s) são elegíveis."))


            # 2: GERAÇÃO DOS REGISTROS DE CERTIFICADO (CRIAÇÃO)

            certificates_created_count = 0
            try:
                # Usar uma transação garante que ou todos os certificados de um
                # trabalho são criados, ou nenhum é, mantendo a consistência.
                with transaction.atomic():
                    for student_assessment in eligible_students_assessments:
                        student = student_assessment.user

                        # Gera um hash único para validação futura do certificado.
                        hash_input = f"{student.id}-{work.id}-{time.time()}"
                        hash_validate = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

                        # Ação de criação idempotente:
                        # O Django tenta buscar um certificado para este usuário e trabalho.
                        # Se não encontrar, ele cria um novo usando os valores de `defaults`.
                        # Se já encontrar, não faz nada.
                        certificate, created = Certificate.objects.get_or_create(
                            user=student,
                            work=work,
                            defaults={'hash_validate': hash_validate}
                        )

                        if created:
                            certificates_created_count += 1
                            self.stdout.write(f"    -> Registro de certificado CRIADO para o usuário: {student.username}")
                        else:
                            # Isso não deve acontecer se a lógica de `certificates_generated_at` estiver correta,
                            # mas é uma segurança extra.
                            self.stdout.write(f"    -> Registro para {student.username} já existia. Nenhuma ação tomada.")
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> ERRO na criação de certificados para o trabalho {work.id}: {e}"))
                continue # Pula para o próximo trabalho

            if certificates_created_count > 0:
                total_certificates_created += certificates_created_count
                self.stdout.write(self.style.SUCCESS(f"  -> {certificates_created_count} novos registros de certificado foram criados com sucesso."))

            # Marca o trabalho como processado para não ser verificado novamente no futuro.
            work.certificates_generated_at = timezone.now()
            work.save(update_fields=['certificates_generated_at'])

        self.stdout.write(self.style.SUCCESS(f"\n[ Tarefa Finalizada ] Total de {total_certificates_created} novos registros de certificado criados na execução."))