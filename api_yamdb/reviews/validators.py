import datetime

from rest_framework.serializers import ValidationError


def validate_year(value):
    current_year = datetime.date.today().year
    if value > current_year:
        raise ValidationError(
            f'Год не может быть больше {current_year}.'
        )
    if value < 1:
        raise ValidationError('Год не может быть меньше 1.')
