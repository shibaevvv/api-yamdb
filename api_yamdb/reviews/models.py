import datetime
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User  # Импорт кастомной модели пользователя


class Category(models.Model):
    """Категории произведений (Фильмы, Книги, Музыка и т.д.)."""
    name = models.CharField(max_length=100, unique=True,
                            verbose_name="Категория")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Слаг")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ('name',)

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Жанры произведений."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Жанр")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Слаг")

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"
        ordering = ('name',)

    def __str__(self):
        return self.name


class Title(models.Model):
    """Произведения (фильмы, книги, музыка и т.д.)."""
    name = models.CharField(max_length=200, verbose_name="Название")
    year = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(datetime.datetime.now().year)
        ],
        help_text='Введите год публикации в формате YYYY (например, 2014)',
        verbose_name="Год публикации"
    )
    rating = models.FloatField(
        null=True, blank=True,
        verbose_name="Рейтинг"
    )
    description = models.TextField('Описание', blank=True, null=True)
    genre = models.ManyToManyField(
        Genre,
        related_name="titles",
        verbose_name="Жанры"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="titles",
        verbose_name="Категория"
    )

    class Meta:
        verbose_name = "Произведение"
        verbose_name_plural = "Произведения"
        ordering = ('-year', 'name')

    def __str__(self):
        return self.name

class GenreTitle(models.Model):
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('title', 'genre'), name='unique_title_genre'
            )
        ]

class Review(models.Model):
    """Отзывы к произведениям."""
    text = models.TextField('Текст отзыва')

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение',
        related_name="reviews"
    )

    estimation = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Оценка'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор отзыва'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review'
            ),
        ]
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ('created_at',)

    def __str__(self):
        return f'Отзыв от {self.author} к произведению {self.title}'


class Comment(models.Model):
    """Комментарии к отзывам."""
    text = models.TextField('Текст комментария')

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария'
    )

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return f'Комментарий от {self.author} к отзыву {self.review.id}'
