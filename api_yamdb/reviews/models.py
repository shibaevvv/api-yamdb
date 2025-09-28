from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from reviews.validators import username_validator

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MODERATOR = 'moderator'

ROLES = (
    (ROLE_USER, 'Пользователь'),
    (ROLE_ADMIN, 'Администратор'),
    (ROLE_MODERATOR, 'Модератор'),
)


USERNAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 254
FIRST_NAME_MAX_LENGTH = 150
LAST_NAME_MAX_LENGTH = 150
CATEGORY_GENRE_NAME_MAX_LENGTH = 256
CATEGORY_GENRE_SLUG_MAX_LENGTH = 50
TITLE_NAME_MAX_LENGTH = 256

MIN_SCORE = 1
MAX_SCORE = 10


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
        return self.role == ROLE_ADMIN or self.is_staff

    def is_moderator(self):
        """Метод для проверки, является ли пользователь модератором."""
        return self.role == ROLE_MODERATOR

    def __str__(self):
        return self.username


class AbstractNameSlugModel(models.Model):
    """Абстрактная модель для Категории и Жанра."""
    name = models.CharField(
        max_length=CATEGORY_GENRE_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=CATEGORY_GENRE_SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

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


def get_current_year():
    return datetime.today().year


class Title(models.Model):
    """Произведения (фильмы, книги, музыка и т.д.)."""
    name = models.CharField(
        max_length=TITLE_NAME_MAX_LENGTH,
        verbose_name='Название'
    )
    year = models.IntegerField(
        validators=[MaxValueValidator(get_current_year),],
        help_text='Введите год публикации в формате YYYY (например, 2014)',
        verbose_name="Год публикации"
    )
    description = models.TextField('Описание', blank=True, null=True)

    genre = models.ManyToManyField(Genre, verbose_name='Жанры')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('-year', 'name')
        default_related_name = 'titles'

    def __str__(self):
        return self.name


class CreationByAuthorBaseModel(models.Model):
    """Абстрактная модель для отзывов и комментариев."""
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        abstract = True
        ordering = ('pub_date',)
        default_related_name = '%(class)ss'


class Review(CreationByAuthorBaseModel):
    """Отзывы к произведениям."""

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение',
    )
    score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_SCORE),
            MaxValueValidator(MAX_SCORE),
        ],
        verbose_name='Оценка',
    )

    class Meta(CreationByAuthorBaseModel.Meta):
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


class Comment(CreationByAuthorBaseModel):
    """Комментарии к отзывам."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        verbose_name='Отзыв',
    )

    class Meta(CreationByAuthorBaseModel.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий от {self.author} к отзыву {self.review}'
