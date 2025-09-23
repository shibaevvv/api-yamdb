import re

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
