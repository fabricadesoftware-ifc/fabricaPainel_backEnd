from collections import defaultdict

from core.work.models import Work

def distribute_works_evenly():
    # 1. Obter todos os trabalhos que ainda não têm um orientador atribuído
    works = Work.objects.filter(evaluator__isnull=True)
    
    # 2. Criar um dicionário para armazenar a contagem de trabalhos de cada orientador
    advisor_work_count = defaultdict(int)
    
    # 3. Para cada trabalho, obter os orientadores disponíveis e contar seus trabalhos atuais
    for work in works:
        available_advisors = work.cross_cutting_theme.advisor.all()

        # Se houver orientadores disponíveis para o tema transversal do trabalho
        if available_advisors.exists():
            # Contar quantos trabalhos cada orientador já tem
            for advisor in available_advisors:
                advisor_work_count[advisor.id] = Work.objects.filter(
                    cross_cutting_theme__advisor=advisor
                ).count()
            
            # 4. Atribuir o orientador com menos trabalhos ao trabalho atual
            selected_advisor = min(available_advisors, key=lambda a: advisor_work_count[a.id])

            # 5. Atribuir o orientador ao trabalho
            work.evaluator.add(selected_advisor)
            work.save()

            # Incrementar a contagem de trabalhos do orientador
            advisor_work_count[selected_advisor.id] += 1