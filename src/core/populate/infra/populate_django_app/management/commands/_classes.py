from core.user.infra.user_django_app.models import User, Class, UserClass
from core.populate.infra.resources.data_classes import classes
from core.populate.infra.resources.data_student_classes import student_classes
import random
import datetime


def populate_classes():
    if Class.objects.exists():
        print("classes")
        return

    for class_data in classes:
        class_instance = Class(**class_data)
        class_instance.save()

    print("Classes populadas com sucesso.")

def assign_students_to_classes():
    
    for class_data in student_classes:
        class_instance = Class.objects.get(
            name=class_data["class_name"]
        )
        student_instance = User.objects.get(
            registration=class_data["student"]
        )
        user_class = UserClass(
            user=student_instance,
            class_name=class_instance,
            year=datetime.datetime.now().year
        )
        
        user_class.save()
        
