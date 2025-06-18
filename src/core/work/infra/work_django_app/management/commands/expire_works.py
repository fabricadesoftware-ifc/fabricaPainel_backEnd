from django.core.management.base import BaseCommand
from core.work.domain.tasks.expire_works import expire_pending_works


class Command(BaseCommand):
    help = 'Expira trabalhos pendentes cujas datas de submissão passaram'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem fazer alterações no banco de dados',
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('Executando em modo DRY-RUN - nenhuma alteração será feita')
            )
            # Para dry-run, você poderia criar uma versão da função que apenas conta
            # Por agora, apenas mostra a mensagem
            self.stdout.write('Use a tarefa Celery ou remova --dry-run para executar de verdade')
        else:
            self.stdout.write('Iniciando processo de expiração de trabalhos...')
            result = expire_pending_works()
            self.stdout.write(
                self.style.SUCCESS(f'Processo concluído: {result}')
            ) 