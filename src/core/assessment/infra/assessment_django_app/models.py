from django.db import models
from typing import TYPE_CHECKING

from core.user.infra.user_django_app.models import Evaluator, User
from core.work.infra.work_django_app.models import Work

class Assessment(models.Model):
    if TYPE_CHECKING:
        id: int
        work_id: str
        evaluator_id: int

    work = models.ForeignKey(Work, on_delete=models.PROTECT)
    grade = models.DecimalField(max_digits=4, decimal_places=2)
    evaluator = models.ForeignKey(
        Evaluator,
        on_delete=models.PROTECT,
        related_name="assessments_evaluator",
        )
    date_time = models.DateTimeField()
    committee_feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.evaluator} - {self.work.title} - {self.grade}"
    
class Assessments(models.Model):
    if TYPE_CHECKING:
        id: int
        evaluator_id: int
        work_id: str

    evaluator =  models.ForeignKey(Evaluator,
        related_name="assessments",
        on_delete=models.PROTECT)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.evaluator} - {self.work.title}"
    

class StudentAssessments(models.Model):
    if TYPE_CHECKING:
        id: int
        work_id: str
        student_id: int

    grade = models.DecimalField(max_digits=4, decimal_places=2)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)
    date_time = models.DateTimeField()
    student = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        limit_choices_to={'user_type': 'STUDENT'}
    )

    def __str__(self):
        return f"{self.student} - {self.work.title} - {self.grade}"
