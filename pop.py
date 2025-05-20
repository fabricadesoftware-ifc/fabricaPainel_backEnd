# assign_users_to_classes.py

import os
import django
import random

# Configura o Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "src.django_project.settings"
)  # Altere 'seu_projeto' para o nome do seu projeto
django.setup()

from core.user.infra.user_django_app.models import User, Class, UserClass


def assign_students_to_classes(year=2025, total_classes=9):
    # Recupera as turmas cadastradas
    classes = list(Class.objects.all()[:total_classes])
    if len(classes) < total_classes:
        print(
            f"⚠️ Apenas {len(classes)} turmas encontradas. São necessárias {total_classes}."
        )
        return

    # Recupera os usuários do tipo STUDENT
    students = list(User.objects.filter(user_type=User.STUDENT))

    if not students:
        print("❌ Nenhum aluno encontrado.")
        return

    # Embaralha os alunos
    random.shuffle(students)

    # Limpa as associações anteriores para o mesmo ano (opcional)
    UserClass.objects.filter(year=year).delete()

    # Distribui os alunos entre as turmas
    for index, student in enumerate(students):
        assigned_class = classes[index % total_classes]
        UserClass.objects.create(user=student, class_name=assigned_class, year=year)

    print(
        f"✅ {len(students)} alunos foram distribuídos entre {total_classes} turmas para o ano de {year}."
    )


if __name__ == "__main__":
    assign_students_to_classes()
