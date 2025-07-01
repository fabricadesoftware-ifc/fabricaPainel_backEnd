from rest_framework import serializers


def validate_grade_range(value):
    """
    Validates that the grade is between 0 and 10.
    """
    if not (0 <= value <= 10):
        raise serializers.ValidationError("A nota deve ser entre 0 e 10.")
    return value