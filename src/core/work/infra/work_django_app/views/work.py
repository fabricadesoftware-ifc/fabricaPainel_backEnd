from uuid import uuid4
from django.db import transaction
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework.throttling import UserRateThrottle
from django_project.settings import EMAIL_HOST_USER
from rest_framework.response import Response
from rest_framework import status

from core.work.infra.work_django_app.models import Work, WorkStatusType, WorkAdvisorStatusType, WorkCollaborator
from core.work.infra.work_django_app.serializers import (
    WorkDetailSerializer,
    WorkWriteSerializer,
    WorkListSerializer
)
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.__seedwork.domain.actions.work_path import work_path, work_path_submission
from core.work.infra.work_django_app.filters import WorkFilter
from core.work.domain.tasks import send_work_email_to_advisor
from core.work.domain.tasks.send_email_collaborator.send_work_email_to_collaborator import send_work_email_to_collaborator

from core.work.domain.tasks import notify_advisor_on_data_update


@extend_schema(tags=["work"])
class WorkViewSet(ModelViewSet):
    queryset = Work.objects.all()
    serializer_class = WorkDetailSerializer
    throttle_classes = [UserRateThrottle]
    filterset_class = WorkFilter

    def get_serializer_class(self):
        if self.action in ["list"]:
            return WorkListSerializer
        if self.action in ["retrieve"]:
            return WorkDetailSerializer   
        return WorkWriteSerializer
    http_method_names = ["get", "post", "patch", "put", "delete"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            work = serializer.save()

            if work.advisor:
                accept_work_advisor_link, reject_work_advisor_link, accept_work_collaborator_link, reject_work_collaborator_link = work_path(work)
                from_email = EMAIL_HOST_USER
                email_recipient_list = [work.advisor.email]
                email_subject = "Convite para orientação de trabalho"
                students_emails = [member.email for member in work.team.team_members.all()]

                send_work_email_to_advisor.delay(
                    str(work.id),
                    email_subject,
                    from_email,
                    email_recipient_list,
                    accept_work_advisor_link,
                    reject_work_advisor_link,
                    students_emails
                )

                work.advisor_status = WorkAdvisorStatusType.Type.PENDING.value
                work.save()
            
            # Enviar emails para colaboradores se existirem
            work_collaborators = WorkCollaborator.objects.filter(work=work)
            if work_collaborators.exists():
                for work_collaborator in work_collaborators:
                    accept_work_advisor_link, reject_work_advisor_link, accept_work_collaborator_link, reject_work_collaborator_link = work_path(work)
                    from_email = EMAIL_HOST_USER
                    email_recipient_list = [work_collaborator.collaborator.email]
                    email_subject = "Convite para colaboração em trabalho"
                    students_emails = [member.email for member in work.team.team_members.all()]
                    
                    # Adiciona o email do colaborador como parâmetro na URL
                    accept_work_collaborator_link += f"?collaborator_email={work_collaborator.collaborator.email}"
                    reject_work_collaborator_link += f"?collaborator_email={work_collaborator.collaborator.email}"
                    
                    send_work_email_to_collaborator.delay(
                        str(work.id),
                        email_subject,
                        from_email,
                        email_recipient_list,
                        accept_work_collaborator_link,
                        reject_work_collaborator_link,
                        students_emails
                    )

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            old_work = self.get_object()
            response = super().update(request, *args, **kwargs)
            work = self.get_object()

            # Se o orientador foi alterado, envia novo email
            if work.advisor and (not old_work.advisor or old_work.advisor.id != work.advisor.id):
                accept_work_advisor_link, reject_work_advisor_link, accept_work_collaborator_link, reject_work_collaborator_link = work_path(work)
                from_email = EMAIL_HOST_USER
                email_recipient_list = [work.advisor.email]
                email_subject = "Convite para orientação de trabalho"
                students_emails = [member.email for member in work.team.team_members.all()]

                send_work_email_to_advisor.delay(
                    str(work.id),
                    email_subject,
                    from_email,
                    email_recipient_list,
                    accept_work_advisor_link,
                    reject_work_advisor_link,
                    students_emails
                )

                work.advisor_status = WorkAdvisorStatusType.Type.PENDING.value
                work.save()

            # Verifica se os colaboradores foram alterados
            if 'collaborators' in request.data:
                # Enviar emails para novos colaboradores
                work_collaborators = request.data.getlist('collaborators', [])
                print("work_collaborators", work_collaborators)
                for work_collaborator in work_collaborators:
                    work_collaborator = WorkCollaborator.objects.get(collaborator=work_collaborator)
                    accept_work_advisor_link, reject_work_advisor_link, accept_work_collaborator_link, reject_work_collaborator_link = work_path(work)
                    from_email = EMAIL_HOST_USER
                    email_recipient_list = [work_collaborator.collaborator.email]
                    email_subject = "Convite para colaboração em trabalho"
                    students_emails = [member.email for member in work.team.team_members.all()]
                    
                    # Adiciona o email do colaborador como parâmetro na URL
                    accept_work_collaborator_link += f"?collaborator_email={work_collaborator.collaborator.email}"
                    reject_work_collaborator_link += f"?collaborator_email={work_collaborator.collaborator.email}"
                    print("accept_work_collaborator_link", accept_work_collaborator_link)
                    send_work_email_to_collaborator.delay(
                        str(work.id),
                        email_subject,
                        from_email,
                        email_recipient_list,
                        accept_work_collaborator_link,
                        reject_work_collaborator_link,
                        students_emails
                    )

            return response
        
    def partial_update(self, request, *args, **kwargs):
        work = self.get_object()
        action = request.data.get('action')
        abstract = request.data.get('abstract')
        work.abstract = abstract
        work.save()
        if action == 'submission':
            print("submission" + abstract)
            accept_work_link, reject_work_link = work_path_submission(work)
            notify_advisor_on_data_update.delay(
                str(work.id),
                accept_work_link,
                reject_work_link
            )
            message = "Abstract enviado para o orientador"
        return Response(data=message, status=status.HTTP_200_OK)

        
    