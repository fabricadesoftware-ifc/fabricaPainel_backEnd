from core.user.infra.user_django_app.models import User, Class, UserClass
from core.populate.infra.resources.data_classes import classes
import random


def populate_classes():
    if Class.objects.exists():
        print("classes")
        return

    for class_data in classes:
        class_instance = Class(**class_data)
        class_instance.save()

    print("Classes populadas com sucesso.")

def assign_students_to_classes():
    classes = list(Class.objects.all())
    students = list(User.objects.filter(user_type=User.STUDENT))
    year = 2025

    if UserClass.objects.filter(year=year).exists():
        print(f"❌ Alunos já atribuídos às turmas para o ano de {year}.")
        return

    if not students:
        print("❌ Nenhum aluno encontrado.")
        return

    random.shuffle(students)

    for index, student in enumerate(students):
        assigned_class = classes[index % len(classes)]
        UserClass.objects.create(user=student, class_name=assigned_class, year=year)

    print(
        f"✅ {len(students)} alunos foram distribuídos entre {len(classes)} turmas para o ano de {year}."
    )
