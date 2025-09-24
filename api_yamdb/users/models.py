from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MODERATOR = 'moderator'

ROLES = (
    (ROLE_USER, 'Пользователь'),
    (ROLE_ADMIN, 'Администратор'),
    (ROLE_MODERATOR, 'Модератор'),
)


class CustomUser(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        'Логин',
        max_length=150,
        unique=True,
        blank=False,
        null=False
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=254,
        unique=True,
        blank=False,
        null=False
    )
    first_name = models.CharField('Имя', max_length=150, blank=True)
    last_name = models.CharField('Фамилия', max_length=150, blank=True)
    bio = models.TextField('Биография', blank=True,)
    role = models.CharField(
        'Роль',
        max_length=20,
        choices=ROLES,
        default=ROLE_USER,
        blank=True
    )
    confirmation_code = models.CharField(
        verbose_name='Код подтверждения',
        max_length=255,
        null=True,
        blank=False
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def is_admin(self):
        """Метод для проверки, является ли пользователь администратором."""
        return (self.role == ROLE_ADMIN or self.is_staff or self.is_superuser)

    def is_moderator(self):
        """Метод для проверки, является ли пользователь модератором."""
        return (self.role == ROLE_MODERATOR
                or self.is_staff
                or self.is_superuser
                )

    def __str__(self):
        return self.username


User = get_user_model()
