from rest_framework.exceptions import ValidationError
from core.work.infra.work_django_app.models import Work, Team
from core.user.infra.user_django_app.models import UserClass


def validate_work_team_members(attrs):
    team: Team = attrs.get("team")
    if not team:
        raise ValidationError({"team": "O campo 'team' é obrigatório."})

    members = list(team.team_members.all())
    if not members:
        raise ValidationError({"team": "O time deve ter pelo menos um membro."})

    for user in members:
        if Work.objects.filter(team__team_members=user).exists():
            raise ValidationError(
                {
                    "team": f"O usuário {user.name or user.email} já está em outro trabalho."
                }
            )

    if attrs.get("integrated_project"):
        edition = attrs.get("edition")
        if not edition:
            raise ValidationError(
                {"edition": "Não foi possível determinar o ano da edição."}
            )

        ano_edicao = edition.year
        uc0 = UserClass.objects.filter(user=members[0], year=ano_edicao).first()
        if not uc0:
            raise ValidationError(
                {
                    "integrated_project": (
                        f"O usuário {members[0].name} não tem turma cadastrada para o ano {ano_edicao}."
                    )
                }
            )
        turma_base_id = uc0.class_name_id

        for user in members[1:]:
            uc = UserClass.objects.filter(user=user, year=ano_edicao).first()
            if not uc:
                raise ValidationError(
                    {
                        "integrated_project": (
                            f"O usuário {user.name} não tem turma cadastrada para o ano {ano_edicao}."
                        )
                    }
                )
            if uc.class_name_id != turma_base_id:
                raise ValidationError(
                    {
                        "integrated_project": (
                            "Todos os membros devem pertencer à mesma turma "
                            f"(esperado turma id={turma_base_id}, encontrado id={uc.class_name_id})."
                        )
                    }
                )

    return False