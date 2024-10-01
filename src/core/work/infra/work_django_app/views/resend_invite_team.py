from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import UserRateThrottle
from core.user.infra.user_django_app.models import User
from core.work.infra.work_django_app.models import Team, Token
from core.work.domain.tasks.send_email_student.send_email_to_member import send_email_to_member
from rest_framework.response import Response
from rest_framework import status

@api_view(["POST"])
@throttle_classes([UserRateThrottle])
def resend_invite_team(request, *args, **kwargs):
    user_id = request.data.get("user_id")
    token = request.data.get("token")
    team_id = request.data.get("team_id")
    
    print(user_id, token, team_id)
    
    try:
        user: User = User.objects.get(id=user_id)
        team: Team = Team.objects.get(id=team_id)
        token: Token = Token.objects.get(token=token)
        
        print(user, team, token)
        
        team.reject_tokens.remove(token)
        team.tokens.add(token)
        team.save()
        
        send_email_to_member(user, token.token, team_id)
        return Response(
            {"message": "Convite reenviado com sucesso."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(e)
        return Response(
            {"error": "Erro ao reenviar convite. aaaaaaaaa"},
            status=status.HTTP_400_BAD_REQUEST,
        )