import datetime, re

from rest_framework.serializers import ValidationError

from reviews.constants import RESERVED_USERNAMES

INVALID_USERNAME_ERROR = '{} - недопустимый логин пользователя!'
INVALID_CHARS_ERROR = (
    'Нельзя использовать эти символы в логине: {} '
    'Разрешены только буквы, цифры и @/./+/-/_'
)


def username_validator(username):
    """Валидатор для проверки поля username."""
    if username in RESERVED_USERNAMES:
        raise ValidationError(INVALID_USERNAME_ERROR.format(username))
    if (invalid_chars := re.findall(r'[^\w.@+-]', username)):
        raise ValidationError(INVALID_CHARS_ERROR.format(
            ''.join(set(invalid_chars))
        ))
    return username


def validate_year(value):
    current_year = datetime.date.today().year
    if value > current_year:
        raise ValidationError(
            f'Год не может быть больше {current_year}.'
        )
    if value < 1:
        raise ValidationError('Год не может быть меньше 1.')
