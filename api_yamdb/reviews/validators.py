import re

from rest_framework.serializers import ValidationError

from reviews.constants import RESERVED_USERNAMES

INVALID_USERNAME_ERROR = '{} - недопустимый логин пользователя!'
INVALID_CHARS_ERROR = (
    'Нельзя использовать эти символы в логине: {} '
    'Разрешены только буквы, цифры и @/./+/-/_'
)


def username_validator(username):
    """Валидатор для проверок поля username."""
    if username in RESERVED_USERNAMES:
        raise ValidationError(INVALID_USERNAME_ERROR.format(username))
    if (invalid_chars := re.findall(r'[^\w.@+-]', username)):
        raise ValidationError(INVALID_CHARS_ERROR.format(
            ''.join(set(invalid_chars))
        ))
    return username
