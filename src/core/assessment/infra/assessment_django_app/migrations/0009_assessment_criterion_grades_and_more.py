from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assessment_django_app", "0008_remove_assessment_student_feedback_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="assessment",
            name="criterion_grades",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="studentassessments",
            name="criterion_grades",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
