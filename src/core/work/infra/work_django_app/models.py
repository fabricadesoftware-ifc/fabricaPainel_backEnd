from django.db import models
from typing import TYPE_CHECKING
from uuid import UUID, uuid4


from simple_history.models import HistoricalRecords

from core.edition.infra.edition_django_app.models import Edition
from core.user.infra.user_django_app.models import User, Evaluator
from core.field.infra.field_django_app.models import Field
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.work.domain.value_objects import WorkStatusType, WorkAdvisorStatusType, WorkCollaboratorStatusType

class WorkKind(models.TextChoices):
    REGULAR = "regular", "Trabalho regular"
    TERRITORIOS = "territorios", "Módulo Territórios"
    COMUNICACAO = "comunicacao", "Módulo Comunicação"


class Token(models.Model):
    if TYPE_CHECKING:
        id: int
        user_id: int
        sender_id: int | None

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender", blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
class Team(models.Model):
    if TYPE_CHECKING:
        id: int
        edition_id: int

    team_members = models.ManyToManyField(User, related_name="team", blank=True)
    edition = models.ForeignKey(Edition, on_delete=models.PROTECT, related_name="team", blank=True)
    #tokens = models.ManyToManyField(Token, related_name="tokens", blank=True)
    #accept_tokens = models.ManyToManyField(Token, related_name="accept_tokens", blank=True)
    #reject_tokens = models.ManyToManyField(Token, related_name="reject_tokens", blank=True)

    # def generate_token(self):
    #     """
    #     Gera um token único (UUID) que será utilizado para validação de membros.
    #     """
    #     return str(uuid4())


    def __str__(self) -> str:
        members = ", ".join([user.name if user.name else "Unknown" for user in self.team_members.all()])
        return f"Team Members: {members}"
    


class Ods(models.Model):
    if TYPE_CHECKING:
        id: int

    name = models.CharField(max_length=255, verbose_name="Sustainable Goal", unique=True)

    def __str__(self) -> str:
        return self.name

class Work(models.Model):
    if TYPE_CHECKING:
        id: UUID
        edition_id: int
        cross_cutting_theme_id: int
        team_id: int
        advisor_id: int

    PENDING = WorkStatusType.Type.PENDING.value
    APPROVED = WorkStatusType.Type.APPROVED.value
    NEEDS_CHANGES = WorkStatusType.Type.NEEDS_CHANGES.value
    REJECTED = WorkStatusType.Type.REJECTED.value
    EXPIRED = WorkStatusType.Type.EXPIRED.value
    
    PENDING_ADVISOR = WorkAdvisorStatusType.Type.PENDING.value
    APPROVED_ADVISOR = WorkAdvisorStatusType.Type.APPROVED.value
    REJECTED_ADVISOR = WorkAdvisorStatusType.Type.REJECTED.value
    EXPIRED_ADVISOR = WorkAdvisorStatusType.Type.EXPIRED.value
    
    WORK_TYPE_STATUS_CHOICE = (
        (PENDING, WorkStatusType.Type.PENDING.label),
        (APPROVED, WorkStatusType.Type.APPROVED.label),
        (NEEDS_CHANGES, WorkStatusType.Type.NEEDS_CHANGES.label),
        (REJECTED, WorkStatusType.Type.REJECTED.label),
        (EXPIRED, WorkStatusType.Type.EXPIRED.label),
    )
    
    WORK_ADVISOR_STATUS_CHOICE = (
        (PENDING_ADVISOR, WorkAdvisorStatusType.Type.PENDING.label),
        (APPROVED_ADVISOR, WorkAdvisorStatusType.Type.APPROVED.label),
        (REJECTED_ADVISOR, WorkAdvisorStatusType.Type.REJECTED.label),
        (EXPIRED_ADVISOR, WorkAdvisorStatusType.Type.EXPIRED.label),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Título", blank=True)
    abstract = models.TextField(blank=True, null=True)
    edition = models.ForeignKey(Edition, on_delete=models.PROTECT)
    field = models.ManyToManyField(Field, default=None, blank=True)
    evaluator = models.ManyToManyField(Evaluator, related_name="evaluator", default=None, blank=True)
    cross_cutting_theme = models.ForeignKey(CrossCuttingTheme, on_delete=models.PROTECT)
    #initial_submission_work_date = models.DateTimeField(blank=True, null=True)
    #final_submission_work_date = models.DateTimeField(blank=True, null=True)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    needs_changes_submission_work_date = models.DateTimeField(blank=True, null=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    ods = models.ManyToManyField(Ods, related_name="SustainableGoals", default=None)
    status = models.PositiveSmallIntegerField(choices=WORK_TYPE_STATUS_CHOICE, default=PENDING)
    advisor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="advisor", limit_choices_to={"is_advisor": True}, default=None)
    advisor_status = models.PositiveSmallIntegerField(choices=WORK_ADVISOR_STATUS_CHOICE, default=PENDING_ADVISOR)
    feedback = models.TextField(blank=True, null=True)
    integrated_project = models.BooleanField(default=False)
    work_kind = models.CharField(
        "Tipo do trabalho",
        max_length=20,
        choices=WorkKind.choices,
        default=WorkKind.REGULAR,
        help_text=(
            "Territórios e Comunicação são módulos de evento com nota física: "
            "a nota final de cada aluno é a nota lançada para ele, sem média com a banca."
        ),
    )
    history = HistoricalRecords()
    
    @property
    def is_module(self) -> bool:
        return self.work_kind != WorkKind.REGULAR

    def __str__(self) -> str:
        return f"{self.title} - {self.team} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Trabalho"
        verbose_name_plural = "Trabalhos"
        ordering = ["-title"]

class Keyword(models.Model):
    if TYPE_CHECKING:
        id: int
        work_id: UUID

    name = models.CharField(max_length=255)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Palavra-chave"
        verbose_name_plural = "Palavras-chave"
        ordering = ["-name"]
        
        
class WorkCollaborator(models.Model):
    if TYPE_CHECKING:
        id: int
        work_id: UUID
        collaborator_id: int

    PENDING = WorkCollaboratorStatusType.Type.PENDING.value
    APPROVED = WorkCollaboratorStatusType.Type.APPROVED.value
    REJECTED = WorkCollaboratorStatusType.Type.REJECTED.value
    EXPIRED = WorkCollaboratorStatusType.Type.EXPIRED.value
    
    WORK_COLLABORATOR_STATUS_CHOICE = (
        (PENDING, WorkCollaboratorStatusType.Type.PENDING.label),
        (APPROVED, WorkCollaboratorStatusType.Type.APPROVED.label),
        (REJECTED, WorkCollaboratorStatusType.Type.REJECTED.label),
        (EXPIRED, WorkCollaboratorStatusType.Type.EXPIRED.label),
    )
    
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name="work_collaborator")
    collaborator = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={"is_collaborator": True}, related_name="work_collaborator")
    status = models.PositiveSmallIntegerField(choices=WORK_COLLABORATOR_STATUS_CHOICE, default=PENDING)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    history = HistoricalRecords()
    
    
    def __str__(self):
        return f"{self.work} - {self.collaborator}"
    
    
