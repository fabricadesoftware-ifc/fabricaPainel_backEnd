from core.user.infra.user_django_app.models import User
from core.work.infra.work_django_app.models import Team
from core.populate.infra.resources.data_student import students
from core.populate.infra.resources.data_advisor import advisors
from core.populate.infra.resources.data_teams import student_team


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


def populate_users():
    if User.objects.exists():
        print("student")
        return

    __get_or_create_super_user()

    students_to_create = []
    advisors_to_create = []

    for student_data in students:
        print(student_data, "populando estudantes")
        user = User(
            email=student_data["email"],
            name=student_data["name"],
            registration=student_data["registration"],
            is_advisor=False,
            user_type=User.STUDENT,
            password='student123',
            # password=User.set_password(student_data["password"])
        )

        students_to_create.append(user)

    User.objects.bulk_create(students_to_create)

    for advisor_data in advisors:
        print(advisor_data, "populando professores")
        user = User(
            email=advisor_data["email"],
            name=advisor_data["name"],
            registration=advisor_data["registration"],
            is_advisor=True,
            user_type=User.TEACHER,
            password='advisor123',
            # password=User.set_password(advisor_data["password"]
        )

        advisors_to_create.append(user)

    User.objects.bulk_create(advisors_to_create)


def populate_team():
    if Team.objects.exists():
        return

    for team_data in student_team:
        print("populando times")
        team = Team.objects.create()

        if "team_members" in team_data and isinstance(team_data["team_members"], list):
            for student_id in team_data["team_members"]:
                try:
                    user = User.objects.get(id=student_id)

                    team.team_members.add(user)
                except User.DoesNotExist:
                    print(f"Usuário com ID {student_id} não encontrado. Ignorando.")

        team.save()

    print("Teams populados com sucesso.")
