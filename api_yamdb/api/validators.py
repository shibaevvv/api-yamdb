import re

from rest_framework import serializers


def username_validator(username):
    if username == 'me':
        raise serializers.ValidationError(
            'Недопустимое имя пользователя!'
        )
    if not re.match(r'^[\w.@+-]+\Z', username):
        raise serializers.ValidationError(
            ('Имя пользователя может содержать латиницу, '
                'цифры и знаки @ / . / + / - / _')
        )
    return username
