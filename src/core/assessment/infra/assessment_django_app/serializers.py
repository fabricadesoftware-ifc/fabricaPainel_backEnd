from rest_framework import serializers
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from core.assessment.domain.validations import validate_grade_range, validate_assessment_creator, validate_assessment_evaluator, validate_assessment_date
from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments


def _decimal_grade(value):
    try:
        grade = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise serializers.ValidationError("A nota do criterio deve ser numerica.")

    validate_grade_range(grade)
    return grade


def _evaluation_group(work, target):
    criteria_groups = work.edition.evaluation_criteria or []
    for group in criteria_groups:
        if group.get("target") == target:
            return group
    return None


def _normalize_criterion_grades(work, target, value):
    if value in (None, "", []):
        return None

    if not isinstance(value, list):
        raise serializers.ValidationError("As notas dos criterios devem ser uma lista.")

    group = _evaluation_group(work, target)
    if not group:
        raise serializers.ValidationError("Nao existem criterios configurados para esta avaliacao.")

    criteria = group.get("criteria") or []
    expected_by_key = {criterion.get("key"): criterion for criterion in criteria}
    submitted_by_key = {}

    for item in value:
        if not isinstance(item, dict):
            raise serializers.ValidationError("Cada nota de criterio deve ser um objeto.")

        key = str(item.get("key") or "").strip()
        if not key:
            raise serializers.ValidationError("Cada nota de criterio precisa de um identificador.")

        if key in submitted_by_key:
            raise serializers.ValidationError(f"O criterio '{key}' foi informado mais de uma vez.")

        if key not in expected_by_key:
            raise serializers.ValidationError(f"O criterio '{key}' nao pertence a esta avaliacao.")

        submitted_by_key[key] = _decimal_grade(item.get("grade"))

    missing_keys = [key for key in expected_by_key if key not in submitted_by_key]
    if missing_keys:
        raise serializers.ValidationError("Todos os criterios configurados precisam receber nota.")

    total = Decimal("0")
    normalized = []
    for criterion in criteria:
        key = criterion["key"]
        weight = Decimal(str(criterion["weight"]))
        grade = submitted_by_key[key]
        total += grade * weight / Decimal("100")
        normalized.append(
            {
                "key": key,
                "label": criterion.get("label", key),
                "description": criterion.get("description", ""),
                "weight": float(weight),
                "grade": float(grade),
            }
        )

    final_grade = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return normalized, final_grade


def _apply_criterion_grades(attrs, target):
    normalized = _normalize_criterion_grades(
        attrs.get("work"),
        target,
        attrs.get("criterion_grades"),
    )

    if normalized:
        criterion_grades, final_grade = normalized
        attrs["criterion_grades"] = criterion_grades
        attrs["grade"] = final_grade
        return

    if "grade" not in attrs:
        raise serializers.ValidationError({"grade": "Informe a nota final ou as notas por criterio."})
    attrs.setdefault("criterion_grades", [])


class AssessmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields: list[str] = [
            "id",
            "evaluator",
            "work",
            "grade",
            "criterion_grades",
            "date_time",
            "committee_feedback",
        ]

class AssessmentWriteSerializer(serializers.ModelSerializer):
    grade = serializers.DecimalField(
        max_digits=4, decimal_places=2, validators=[validate_grade_range], required=False
    )
    criterion_grades = serializers.JSONField(required=False)

    class Meta:
        model = Assessment
        fields: list[str] = [
            "evaluator",
            "work",
            "grade",
            "criterion_grades",
            "date_time",
            "committee_feedback",
        ]

    def validate(self, attrs):
        _apply_criterion_grades(attrs, "work")

        try:
            validate_assessment_date(attrs.get("work"), "work")
            validate_assessment_evaluator(self.context["request"].user, attrs)
        except serializers.ValidationError as e:
            raise serializers.ValidationError({"detail": str(e)})

        return attrs

class StudentAssessmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAssessments
        fields: list[str] = [
            "id",
            "grade",
            "criterion_grades",
            "work",
            "date_time",
            "student",
        ]

class StudentAssessmentsWriteSerializer(serializers.ModelSerializer):
    grade = serializers.DecimalField(
        max_digits=4, decimal_places=2, validators=[validate_grade_range], required=False
    )
    criterion_grades = serializers.JSONField(required=False)

    class Meta:
        model = StudentAssessments
        fields: list[str] = [
            "grade",
            "criterion_grades",
            "work",
            "date_time",
            "student",
        ]

    def validate(self, attrs):
        _apply_criterion_grades(attrs, "student")

        try:
            validate_assessment_date(attrs.get("work"), "student")
            validate_assessment_creator(self.context["request"].user, attrs)

        except serializers.ValidationError as e:
            raise serializers.ValidationError({"detail": str(e)})

        return attrs
