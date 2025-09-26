import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from reviews.constants import (USERNAME_MAX_LENGTH, ROLE_USER, ROLE_ADMIN,
                               ROLE_MODERATOR, ROLES, EMAIL_MAX_LENGTH,
                               FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH)
from reviews.validators import username_validator, validate_year


MIN_SCORE = 1
MAX_SCORE = 10
MIN_YEAR = 1


class User(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        'Логин',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(username_validator,)
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        'Имя',
        max_length=FIRST_NAME_MAX_LENGTH,
        blank=True
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=LAST_NAME_MAX_LENGTH,
        blank=True
    )
    bio = models.TextField('О себе', blank=True,)
    role = models.CharField(
        'Роль',
        max_length=max(len(role) for role, _ in ROLES),
        choices=ROLES,
        default=ROLE_USER,
        blank=True
    )
    confirmation_code = models.CharField(
        'Код подтверждения',
        max_length=settings.CONFIRMATION_CODE_LENGTH,
        null=True,
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


class AbstractNameSlugModel(models.Model):
    """Абстрактная модель для Категории и Жанра."""
    name = models.CharField(max_length=256, unique=True,
                            verbose_name='Название')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='Слаг')

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name


class Category(AbstractNameSlugModel):
    """Категории произведений (Фильмы, Книги, Музыка и т.д.)."""

    class Meta(AbstractNameSlugModel.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(AbstractNameSlugModel):
    """Жанры произведений."""

    class Meta(AbstractNameSlugModel.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    year = models.IntegerField(
        validators=[validate_year],
        help_text='Введите год публикации в формате YYYY (например, 2014)',
        verbose_name='Год публикации',
    )
    description = models.TextField('Описание', blank=True, null=True)

    genre = models.ManyToManyField(
        Genre,
        related_name='titles',
        verbose_name='Жанры',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='titles',
        verbose_name='Категория',
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('-year', 'name')

    def __str__(self):
        return self.name


class AbstractTextModel(models.Model):
    """Абстрактная модель для отзывов и комментариев."""
    text = models.TextField('Текст')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Добавлено')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)ss',  # автоматическое related_name
        verbose_name='Автор',
    )

    class Meta:
        abstract = True
        ordering = ('created_at',)


class Review(AbstractTextModel):
    """Отзывы к произведениям."""

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение',
        related_name='reviews',
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            MIN_SCORE), MaxValueValidator(MAX_SCORE)],
        verbose_name='Оценка',
    )

    class Meta(AbstractTextModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review',
            ),
        ]
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'Отзыв от {self.author} к произведению {self.title}'


class Comment(AbstractTextModel):
    """Комментарии к отзывам."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв',
    )

    class Meta(AbstractTextModel.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий от {self.author} к отзыву {self.review.id}'
