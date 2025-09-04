import logging
from django.db import transaction
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework.throttling import UserRateThrottle
from django_project.settings import EMAIL_HOST_USER
from django_project.permissions import IsWorkOwnerOrReadOnly
from rest_framework.response import Response
from rest_framework import status

from core.work.infra.work_django_app.models import Work, WorkCollaborator
from core.work.infra.work_django_app.serializers import (
    WorkDetailSerializer,
    WorkWriteSerializer,
    WorkListSerializer
)
from core.__seedwork.domain.actions.work_path import work_path, work_path_submission, work_collaborator_path
from core.work.infra.work_django_app.filters import WorkFilter
from core.work.domain.value_objects import WorkCollaboratorStatusType
from core.work.domain.tasks.send_email_advisor.send_work_email_to_advisor import send_work_email_to_advisor
from core.work.domain.tasks.send_email_collaborator.send_work_email_to_collaborator import send_work_email_to_collaborator
from core.work.domain.tasks.send_email_advisor.send_work_update_to_advisor import notify_advisor_on_data_update

logger = logging.getLogger(__name__)

@extend_schema(tags=["work"])
class WorkViewSet(ModelViewSet):
    queryset = Work.objects.all()
    serializer_class = WorkDetailSerializer
    throttle_classes = [UserRateThrottle]
    filterset_class = WorkFilter
    http_method_names = ["get", "post", "patch", "put", "delete"]
    permission_classes = [IsWorkOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return WorkListSerializer
        elif self.action == "retrieve":
            return WorkDetailSerializer
        return WorkWriteSerializer

    def _normalize_collaborators_data(self, collaborators_data):
        """Normaliza dados de colaboradores para sempre retornar uma lista de inteiros"""
        if isinstance(collaborators_data, (int, str)):
            return [int(collaborators_data)]
        elif isinstance(collaborators_data, list):
            return [int(c) for c in collaborators_data if c]
        return []

    def _send_collaborator_emails(self, work, collaborators_data):
        """Envia emails para novos colaboradores"""
        if not collaborators_data:
            return

        for collaborator_id in collaborators_data:
            work_collaborator = WorkCollaborator.objects.filter(
                work=work, collaborator_id=collaborator_id
            ).first()
            
            if work_collaborator:
                accept_work_link, reject_work_link = work_collaborator_path(work_collaborator)
                email_subject = f"Convite para colaborar no trabalho: {work.title}"
                
                send_work_email_to_collaborator.delay(
                    work_collaborator.id,
                    email_subject,
                    EMAIL_HOST_USER,
                    accept_work_link,
                    reject_work_link
                )

    def _send_advisor_email(self, work, email_subject_prefix="Convite para orientar o trabalho"):
        """Envia email para o advisor"""
        if not work.advisor:
            return

        accept_link, reject_link, _, _ = work_path(work)
        email_subject = f"{email_subject_prefix}: {work.title}"
        email_recipient_list = [work.advisor.email]
        students_emails = [member.email for member in work.team.team_members.all()]

        send_work_email_to_advisor.delay(
            str(work.id),
            email_subject,
            EMAIL_HOST_USER,
            email_recipient_list,
            accept_link,
            reject_link,
            students_emails
        )

    def _send_pending_collaborator_reminders(self, work):
        """Envia lembretes para colaboradores pendentes"""
        pending_collaborators = WorkCollaborator.objects.filter(
            work=work, 
            status=WorkCollaboratorStatusType.Type.PENDING.value
        )
        
        for work_collaborator in pending_collaborators:
            accept_link, reject_link = work_collaborator_path(work_collaborator)
            email_subject = f"Lembrete: Convite para colaborar no trabalho: {work.title}"
            
            send_work_email_to_collaborator.delay(
                work_collaborator.id,
                email_subject,
                EMAIL_HOST_USER,
                accept_link,
                reject_link
            )

    def create(self, request, *args, **kwargs):
        collaborators_data = self._normalize_collaborators_data(
            request.data.get("collaborators", [])
        )
        
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_201_CREATED and "id" in response.data:
            work_id = response.data["id"]
            
            def send_creation_emails():
                try:
                    work = Work.objects.get(id=work_id)
                    self._send_collaborator_emails(work, collaborators_data)
                    self._send_advisor_email(work)
                except Work.DoesNotExist:
                    logger.error(f"Trabalho com ID {work_id} não encontrado para envio de emails")
                except Exception as e:
                    logger.error(f"Erro ao enviar emails na criação do trabalho: {e}")
            
            transaction.on_commit(send_creation_emails)
            
        logger.info(f"Work created with ID: {response.data.get('id')}")
        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_advisor = instance.advisor
        
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            def send_update_emails():
                try:
                    updated_work = Work.objects.get(id=instance.id)
                    
                    self._send_pending_collaborator_reminders(updated_work)
                    
                    if updated_work.advisor != old_advisor:
                        self._send_advisor_email(updated_work, "Alteração no trabalho")
                        
                except Exception as e:
                    logger.error(f"Erro ao enviar emails no update: {e}")
            
            transaction.on_commit(send_update_emails)

        return response

    def partial_update(self, request, *args, **kwargs):
        work = self.get_object()
        
        if work.status == 4:  # REJECTED
            return Response(
                {"error": "Este trabalho foi rejeitado e não pode mais ser alterado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action')
        abstract = request.data.get('abstract')
        
        if abstract:
            work.abstract = abstract
            work.save()
            
        if action == 'submission':
            def send_submission_email():
                try:
                    updated_work = Work.objects.get(id=work.id)
                    accept_link, reject_link = work_path_submission(updated_work)
                    notify_advisor_on_data_update.delay(
                        str(updated_work.id),
                        accept_link,
                        reject_link
                    )
                except Exception as e:
                    logger.error(f"Erro ao enviar email de submissão: {e}")
            
            transaction.on_commit(send_submission_email)
            return Response(
                {"message": "Abstract enviado para o orientador"}, 
                status=status.HTTP_200_OK
            )
            
        return Response(
            {"message": "Atualização realizada"}, 
            status=status.HTTP_200_OK
        )
        
    def destroy(self, request, *args, **kwargs):
        from core.work.domain.value_objects import WorkStatusType
        
        work = self.get_object()
        
        work.status = WorkStatusType.Type.REJECTED.value
        work.verification_token = None
        work.save()
        
        WorkCollaborator.objects.filter(work=work).update(verification_token=None)
        
        return Response(
            {"message": "Trabalho removido com sucesso. O registro foi mantido no histórico."},
            status=status.HTTP_200_OK
        )
    