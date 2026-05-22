import logging
from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework.throttling import UserRateThrottle
from django_project.settings import EMAIL_HOST_USER
from django_project.permissions import IsAdminOrManagement, IsWorkOwnerOrReadOnly
from rest_framework.response import Response
from rest_framework import status

from core.edition.infra.edition_django_app.models import Edition
from core.work.infra.work_django_app.models import Work, WorkCollaborator
from core.work.infra.work_django_app.serializers import (
    WorkDetailSerializer,
    WorkWriteSerializer,
    WorkListSerializer
)
from core.__seedwork.domain.actions.work_path import work_path, work_path_submission, work_collaborator_path
from core.work.infra.work_django_app.filters import WorkFilter
from core.work.domain.value_objects import WorkAdvisorStatusType, WorkCollaboratorStatusType, WorkStatusType
from core.work.domain.tasks.send_email_advisor.send_work_email_to_advisor import send_work_email_to_advisor
from core.work.domain.tasks.send_email_collaborator.send_work_email_to_collaborator import send_work_email_to_collaborator
from core.work.domain.tasks.send_email_advisor.send_work_update_to_advisor import notify_advisor_on_data_update

logger = logging.getLogger(__name__)


KANBAN_COLUMNS = [
    ("waiting_advisor", "Aguardando orientador"),
    ("advisor_rejected", "Orientador recusou"),
    ("needs_changes", "Precisa de ajustes"),
    ("ready", "Orientador aceitou"),
    ("approved", "Trabalho aprovado"),
    ("rejected", "Trabalho rejeitado/cancelado"),
    ("expired", "Expirado"),
]


def _choice_label(enum_cls, value):
    try:
        return enum_cls(value).label
    except ValueError:
        return "Nao informado"


def _serialize_user(user):
    if not user:
        return None

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


def _default_edition():
    editions = list(Edition.objects.order_by("-year", "-id"))
    if not editions:
        return None

    for edition in editions:
        if (
            edition.is_active
            or edition.is_open_for_submissions
            or edition.is_open_for_advisors
            or edition.is_open_for_evaluators
            or edition.is_edition_running
        ):
            return edition

    return editions[0]


def _kanban_column_for(work):
    if (
        work.status == WorkStatusType.Type.EXPIRED.value
        or work.advisor_status == WorkAdvisorStatusType.Type.EXPIRED.value
    ):
        return "expired"

    if work.status == WorkStatusType.Type.REJECTED.value:
        return "rejected"

    if work.status == WorkStatusType.Type.NEEDS_CHANGES.value:
        return "needs_changes"

    if work.status == WorkStatusType.Type.APPROVED.value:
        return "approved"

    if work.advisor_status == WorkAdvisorStatusType.Type.REJECTED.value:
        return "advisor_rejected"

    if work.advisor_status == WorkAdvisorStatusType.Type.APPROVED.value:
        return "ready"

    return "waiting_advisor"


def _history_actor(history_record):
    user = getattr(history_record, "history_user", None)
    if not user:
        return None

    return _serialize_user(user)


def _history_entry(history_record, *, source, fallback_label, collaborator=None):
    reason = getattr(history_record, "history_change_reason", None) or fallback_label
    entry = {
        "source": source,
        "event": reason,
        "history_type": history_record.history_type,
        "date": history_record.history_date.isoformat(),
        "actor": _history_actor(history_record),
    }

    if source == "work":
        entry["status"] = history_record.status
        entry["status_label"] = _choice_label(WorkStatusType.Type, history_record.status)
        entry["advisor_status"] = history_record.advisor_status
        entry["advisor_status_label"] = _choice_label(WorkAdvisorStatusType.Type, history_record.advisor_status)

    if source == "collaborator":
        entry["collaborator"] = _serialize_user(collaborator.collaborator if collaborator else None)
        entry["status"] = history_record.status
        entry["status_label"] = _choice_label(WorkCollaboratorStatusType.Type, history_record.status)

    return entry


def _timeline_for(work):
    entries = []

    for record in work.history.order_by("history_date"):
        fallback = {
            "+": "Trabalho criado",
            "~": "Trabalho atualizado",
            "-": "Trabalho removido",
        }.get(record.history_type, "Trabalho atualizado")
        entries.append(_history_entry(record, source="work", fallback_label=fallback))

    for collaborator in work.work_collaborator.all():
        for record in collaborator.history.order_by("history_date"):
            fallback = {
                "+": "Colaborador vinculado",
                "~": "Colaborador atualizado",
                "-": "Colaborador removido",
            }.get(record.history_type, "Colaborador atualizado")
            entries.append(
                _history_entry(
                    record,
                    source="collaborator",
                    fallback_label=fallback,
                    collaborator=collaborator,
                )
            )

    return sorted(entries, key=lambda item: item["date"])


def _serialize_work_for_kanban(work):
    collaborators = [
        {
            "id": link.id,
            "status": link.status,
            "status_label": _choice_label(WorkCollaboratorStatusType.Type, link.status),
            "collaborator": _serialize_user(link.collaborator),
        }
        for link in work.work_collaborator.all()
    ]
    timeline = _timeline_for(work)

    return {
        "id": str(work.id),
        "title": work.title,
        "abstract": work.abstract,
        "status": work.status,
        "status_label": _choice_label(WorkStatusType.Type, work.status),
        "advisor_status": work.advisor_status,
        "advisor_status_label": _choice_label(WorkAdvisorStatusType.Type, work.advisor_status),
        "feedback": work.feedback,
        "needs_changes_submission_work_date": work.needs_changes_submission_work_date,
        "integrated_project": work.integrated_project,
        "edition": {
            "id": work.edition_id,
            "year": work.edition.year,
            "edition_name": work.edition.edition_name,
        },
        "advisor": _serialize_user(work.advisor),
        "team_members": [_serialize_user(member) for member in work.team.team_members.all()],
        "collaborators": collaborators,
        "has_collaborators": bool(collaborators),
        "timeline": timeline,
        "last_event": timeline[-1] if timeline else None,
    }

@extend_schema(tags=["work"])
class WorkViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = Work.objects.select_related(
            'cross_cutting_theme',
            'advisor',
            'team',
            'edition',
        )
        
        if self.action == 'retrieve':
            # Otimiza prefetch apenas para detail view
            return queryset.prefetch_related(
                'field',
                'ods',
                'evaluator',
                'team__team_members',
                Prefetch(
                    'work_collaborator',
                    queryset=WorkCollaborator.objects.select_related('collaborator')
                )
            )
        
        # Lista não precisa de tantos relacionamentos
        return queryset.prefetch_related('field', 'ods')
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

    @action(
        detail=False,
        methods=["get"],
        url_path="admin-kanban",
        permission_classes=[IsAdminOrManagement],
    )
    def admin_kanban(self, request):
        edition_id = request.query_params.get("edition")
        search = (request.query_params.get("search") or "").strip()

        if edition_id:
            try:
                edition = Edition.objects.get(id=edition_id)
            except Edition.DoesNotExist:
                return Response(
                    {"error": "Edicao nao encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            edition = _default_edition()

        columns = [
            {"key": key, "title": title, "count": 0, "items": []}
            for key, title in KANBAN_COLUMNS
        ]

        if not edition:
            return Response(
                {
                    "edition": None,
                    "summary": [],
                    "columns": columns,
                }
            )

        queryset = (
            Work.objects.filter(edition=edition)
            .select_related("advisor", "team", "edition", "cross_cutting_theme")
            .prefetch_related(
                "team__team_members",
                Prefetch(
                    "work_collaborator",
                    queryset=WorkCollaborator.objects.select_related("collaborator"),
                ),
            )
        )

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(team__team_members__name__icontains=search)
                | Q(team__team_members__email__icontains=search)
                | Q(advisor__name__icontains=search)
                | Q(advisor__email__icontains=search)
                | Q(work_collaborator__collaborator__name__icontains=search)
                | Q(work_collaborator__collaborator__email__icontains=search)
                | Q(
                    team__team_members__user_classes__class_name__name__icontains=search,
                    team__team_members__user_classes__year=edition.year,
                )
            ).distinct()

        column_map = {column["key"]: column for column in columns}
        for work in queryset:
            column = column_map[_kanban_column_for(work)]
            column["items"].append(_serialize_work_for_kanban(work))

        for column in columns:
            column["count"] = len(column["items"])

        return Response(
            {
                "edition": {
                    "id": edition.id,
                    "year": edition.year,
                    "edition_name": edition.edition_name,
                },
                "summary": [
                    {"key": column["key"], "title": column["title"], "count": column["count"]}
                    for column in columns
                ],
                "columns": columns,
            }
        )

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
        work._change_reason = "Trabalho rejeitado/cancelado"
        work.save()
        
        WorkCollaborator.objects.filter(work=work).update(verification_token=None)
        
        return Response(
            {"message": "Trabalho removido com sucesso. O registro foi mantido no histórico."},
            status=status.HTTP_200_OK
        )
    
