from django.db import models
from core.user.infra.user_django_app.models import Evaluator, User
from core.work.infra.work_django_app.models import Work

class Assessment(models.Model):
    registration =  models.ForeignKey(User,
        related_name="assessment",
        on_delete=models.PROTECT)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)
    grade = models.FloatField()
    evaluator = models.ForeignKey(
        Evaluator,
        on_delete=models.PROTECT,
        related_name="assessments_evaluator",
        )
    date_time = models.DateTimeField()
    student_feedback = models.TextField()
    committee_feedback = models.TextField()

    def __str__(self):
        return f"{self.registration} - {self.work}"
    
class Assessments(models.Model):
    registration =  models.ForeignKey(User,
        related_name="assessments",
        on_delete=models.PROTECT)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.registration} - {self.work}"