import re
import datetime

from rest_framework.serializers import ValidationError


def username_validator(username):
    """Валидатор для проверок поля username."""
    if username == 'me':
        raise ValidationError('Недопустимое имя пользователя!')
    if not re.match(r'^[\w.@+-]+\Z', username):
        raise ValidationError(
            ('Имя пользователя может содержать латиницу, '
                'цифры и знаки @ / . / + / - / _')
        )
    return username


def validate_year(value):
    current_year = datetime.date.today().year
    if value > current_year:
        raise ValidationError(
            f'Год не может быть больше {current_year}.'
        )
    if value < 1:
        raise ValidationError('Год не может быть меньше 1.')
