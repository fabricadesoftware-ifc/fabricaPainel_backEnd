from core.user.infra.user_django_app.models import User
from core.work.infra.work_django_app.models import Team
from core.edition.infra.edition_django_app.models import Edition
from core.populate.infra.resources.data_student import students
from core.populate.infra.resources.data_classes import classes
from core.populate.infra.resources.data_advisor import advisors
from core.populate.infra.resources.data_teams import student_team
from core.populate.infra.resources.data_teachers import teachers
from collections import Counter
import unicodedata


def __get_or_create_super_user() -> None:
    super_user = User.objects.filter(is_superuser=True)

    if not super_user.exists():
        super_user = User.objects.create_superuser(
            email="admin@admin.com",
            password="admin",
        )


def get_user_by_email(email) -> User:
    user = User.objects.get(email=email)
    return user


def remove_accent(text):
    text_normal = unicodedata.normalize("NFKD", text)
    text_without_accent = "".join(
        c for c in text_normal if not unicodedata.combining(c)
    )
    return text_without_accent


def populate_users():
    # if User.objects.exists():
    #     print("student")
    #     return

    # __get_or_create_super_user()

    students_to_create = []
    for student_data in students:
        print(student_data, "populando alunos")

        student_data["email"] = student_data["email"].strip()

        name_search = remove_accent(student_data["name"].lower())

        user = User(
            **student_data,
            is_advisor=False,
            user_type=User.STUDENT,
            name_search=name_search,
            #password=User.set_password(student_data["password"])
        )

        students_to_create.append(user)

    User.objects.bulk_create(students_to_create)

def populate_team():
    if Team.objects.exists():
        return

    for team_data in student_team:
        try:
            edition_id = team_data.get("edition")
            edition = Edition.objects.get(id=edition_id)

            team = Team.objects.create(edition=edition)

            if "team_members" in team_data and isinstance(team_data["team_members"], list):
                for student_id in team_data["team_members"]:
                    try:
                        user = User.objects.get(id=student_id)
                        team.team_members.add(user)
                    except User.DoesNotExist:
                        print(f"Usuário com ID {student_id} não encontrado. Ignorando.")
            
            team.save()
            print(f"Time da edição {edition.id} populado com sucesso.")

        except Edition.DoesNotExist:
            print(f"Edição com ID {team_data.get('edition')} não encontrada. Ignorando time.")

    print("População de times concluída.")

def populate_teacher():
    if User.objects.filter(is_advisor=True).exists():
        return

    teachers_to_create = []

    for teacher_data in teachers:
        name_search = remove_accent(teacher_data["name"].lower())
        print(teacher_data, "populando professores")
        user = User(
            email=teacher_data["email"].strip(),
            name=teacher_data["name"],
            registration=teacher_data["registration"],
            is_advisor=True,
            user_type=User.TEACHER,
            password="teacher123",
            name_search=name_search,
            # password=User.set_password(teacher_data["password"])
        )

        teachers_to_create.append(user)

    User.objects.bulk_create(teachers_to_create)

    print("Professores populados com sucesso.")
    
def populate_teacher():
    if User.objects.filter(is_advisor=True).exists():
        return

    teachers_to_create = []

    for teacher_data in teachers:
        name_search = remove_accent(teacher_data["name"].lower())
        print(teacher_data, "populando professores")
        user = User(
            email=teacher_data["email"].strip(),
            name=teacher_data["name"],
            registration=teacher_data["registration"],
            is_advisor=True,
            user_type=User.TEACHER,
            password="teacher123",
            name_search=name_search,
            # password=User.set_password(teacher_data["password"])
        )

        teachers_to_create.append(user)

    User.objects.bulk_create(teachers_to_create)

    print("Professores populados com sucesso.")
