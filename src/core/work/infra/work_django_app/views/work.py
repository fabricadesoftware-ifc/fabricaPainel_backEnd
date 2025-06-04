from uuid import uuid4
import logging
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

    def get_serializer_class(self):
        if self.action in ["list"]:
            return WorkListSerializer
        if self.action in ["retrieve"]:
            return WorkDetailSerializer   
        return WorkWriteSerializer
    http_method_names = ["get", "post", "patch", "put", "delete"]
    
    def create(self, request, *args, **kwargs):
        collaborators_data = request.data.get("collaborators", [])
        
        response = super().create(request, *args, **kwargs)
        
        # Só processa emails se a criação foi bem-sucedida E retornou um ID
        if response.status_code == status.HTTP_201_CREATED and "id" in response.data:
            work_id = response.data["id"]
            
            # Usa transaction.on_commit para garantir que emails só sejam enviados após commit
            def send_emails():
                try:
                    work = Work.objects.get(id=work_id)
                    
                    # Enviar emails para colaboradores
                    if collaborators_data:
                        for collaborator_id in collaborators_data:
                            work_collaborator = WorkCollaborator.objects.filter(
                                work=work, 
                                collaborator_id=collaborator_id
                            ).first()
                            
                            if work_collaborator:
                                # Gera links únicos para este colaborador
                                accept_work_link, reject_work_link = work_collaborator_path(work_collaborator)
                                
                                email_subject = f"Convite para colaborar no trabalho: {work.title}"
                                from_email = EMAIL_HOST_USER
                                
                                send_work_email_to_collaborator.delay(
                                    work_collaborator.id,
                                    email_subject,
                                    from_email,
                                    accept_work_link,
                                    reject_work_link
                                )

                    # Enviar email para advisor (lógica já existente)
                    if work.advisor:
                        accept_work_advisor_link, reject_work_advisor_link, accept_work_collaborator_link, reject_work_collaborator_link = work_path(work)
                        
                        email_subject = f"Convite para orientar o trabalho: {work.title}"
                        email_recipient_list = [work.advisor.email]
                        students_emails = [member.email for member in work.team.team_members.all()]
                        from_email = EMAIL_HOST_USER

                        send_work_email_to_advisor.delay(
                            str(work.id),
                            email_subject,
                            from_email,
                            email_recipient_list,
                            accept_work_advisor_link,
                            reject_work_advisor_link,
                            students_emails
                        )
                except Work.DoesNotExist:
                    logger.error(f"Trabalho com ID {work_id} não encontrado para envio de emails")
                except Exception as e:
                    logger.error(f"Erro ao enviar emails na criação do trabalho: {e}")
            
            # Agenda o envio de emails para após o commit da transação
            transaction.on_commit(send_emails)

        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        collaborators_data = request.data.get("collaborators", [])
        
        # CORREÇÃO: Garantir que seja sempre uma lista de inteiros
        if isinstance(collaborators_data, (int, str)):
            collaborators_data = [int(collaborators_data)]
        elif isinstance(collaborators_data, list):
            collaborators_data = [int(c) for c in collaborators_data if c]
        else:
            collaborators_data = []
        
        # Armazena colaboradores atuais antes da atualização
        current_collaborators = set(instance.work_collaborator.values_list('collaborator_id', flat=True))
        old_work = Work.objects.get(id=instance.id)
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            instance_id = instance.id
            
            def send_update_emails(old_work):
                try:
                    # Recarrega a instância atualizada
                    updated_instance = Work.objects.get(id=instance_id)
                    
                    # Verifica colaboradores - agora processa TODOS os colaboradores pendentes
                    all_collaborators = WorkCollaborator.objects.filter(work=updated_instance)
                    
                    for work_collaborator in all_collaborators:
                        # Colaborador pendente - enviar lembrete
                        if work_collaborator.status == WorkCollaboratorStatusType.Type.PENDING.value:
                            email_subject = f"Lembrete: Convite para colaborar no trabalho: {updated_instance.title}"
                            
                            # Gera novos links únicos
                            accept_work_link, reject_work_link = work_collaborator_path(work_collaborator)
                            from_email = EMAIL_HOST_USER
                            
                            send_work_email_to_collaborator.delay(
                                work_collaborator.id,
                                email_subject,
                                from_email,
                                accept_work_link,
                                reject_work_link
                            )

                    # Lógica para advisor (já existente)
                    if updated_instance.advisor != old_work.advisor:
                        accept_work_advisor_link, reject_work_advisor_link, accept_work_collaborator_link, reject_work_collaborator_link = work_path(updated_instance)
                        
                        email_subject = f"Alteração no trabalho: {updated_instance.title}"
                        email_recipient_list = [updated_instance.advisor.email]
                        students_emails = [member.email for member in updated_instance.team.team_members.all()]
                        from_email = EMAIL_HOST_USER

                        send_work_email_to_advisor.delay(
                            str(updated_instance.id),
                            email_subject,
                            from_email,
                            email_recipient_list,
                            accept_work_advisor_link,
                            reject_work_advisor_link,
                            students_emails
                        )
                except Exception as e:
                    logger.error(f"Erro ao enviar emails no update: {e}")
            
            # Agenda o envio de emails para após o commit da transação
            transaction.on_commit(lambda: send_update_emails(old_work))

        return response
        
    def partial_update(self, request, *args, **kwargs):
        work = self.get_object()
        action = request.data.get('action')
        abstract = request.data.get('abstract')
        
        if abstract:
            work.abstract = abstract
            work.save()
            
        if action == 'submission':
            def send_submission_email():
                try:
                    updated_work = Work.objects.get(id=work.id)
                    accept_work_link, reject_work_link = work_path_submission(updated_work)
                    notify_advisor_on_data_update.delay(
                        str(updated_work.id),
                        accept_work_link,
                        reject_work_link
                    )
                except Exception as e:
                    logger.error(f"Erro ao enviar email de submissão: {e}")
            
            # Agenda o envio de email para após o commit da transação
            transaction.on_commit(send_submission_email)
            
            message = "Abstract enviado para o orientador"
            return Response(data={"message": message}, status=status.HTTP_200_OK)
            
        return Response(data={"message": "Atualização realizada"}, status=status.HTTP_200_OK)

        
    