import re

from django.conf import settings
from django.core.exceptions import ValidationError

INVALID_USERNAME_ERROR = '{} - недопустимый логин пользователя!'
INVALID_CHARS_ERROR = (
    'Нельзя использовать эти символы в логине: {} '
    'Разрешены только буквы, цифры и @/./+/-/_'
)


def username_validator(username):
    """Валидатор для проверки поля username."""
    if username in settings.PROFILE_RESERVED_SEGMENT:
        raise ValidationError(INVALID_USERNAME_ERROR.format(username))
    if (invalid_chars := re.findall(
        settings.USERNAME_INVALID_CHARS_REGEX,
        username
    )):
        raise ValidationError(INVALID_CHARS_ERROR.format(
            ''.join(set(invalid_chars))
        ))
    return username
