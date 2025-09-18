from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User  # Импорт кастомной модели пользователя


class Reviews(models.Model):
    """Модель для хранения отзывов на произведения."""

    text = models.TextField('Текст отзыва')  # Основной текст отзыва

    titles = models.ForeignKey(
        Titles,  # Ссылка на произведение
        # При удалении произведения — удаляются и отзывы
        on_delete=models.CASCADE,
        verbose_name='Произведение'  # Название поля в админке
    )

    estimation = models.PositiveSmallIntegerField(
        # Ограничение от 1 до 10
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Оценка'  # Поле для числовой оценки произведения
    )

    created_at = models.DateTimeField(
        auto_now_add=True,  # Автоматическая установка даты при создании
        verbose_name='Добавлено'  # Человекочитаемое имя в админке
    )

    author = models.ForeignKey(
        User,  # Автор отзыва
        # При удалении пользователя удаляются и его отзывы
        on_delete=models.CASCADE,
        verbose_name='Автор отзыва'  # Отображение в админке
    )

    class Meta:
        verbose_name = 'Отзыв'  # Название модели в единственном числе
        # Название модели во множественном числе
        verbose_name_plural = 'Отзывы'
        # Обратное имя для related_name в ForeignKey
        default_related_name = 'reviews'
        ordering = ('created_at',)  # Сортировка по дате создания

    def __str__(self):
        """Возвращает строковое представление отзыва."""
        return f'Отзыв от {self.author} к произведению {self.titles}'


class Comment(models.Model):
    """Модель для хранения комментариев к отзывам."""

    text = models.TextField('Текст комментария')  # Основной текст комментария

    created_at = models.DateTimeField(
        auto_now_add=True,  # Автоматическая установка даты при создании
        verbose_name='Добавлено'  # Название поля в админке
    )

    author = models.ForeignKey(
        User,  # Автор комментария
        # При удалении пользователя удаляются и его комментарии
        on_delete=models.CASCADE,
        verbose_name='Автор комментария'  # Отображение в админке
    )

    review = models.ForeignKey(
        Reviews,  # Ссылка на отзыв
        # При удалении отзыва удаляются все связанные комментарии
        on_delete=models.CASCADE,
        related_name='comments',  # Обратное имя: review.comments.all()
        verbose_name='Отзыв'  # Отображение в админке
    )

    class Meta:
        verbose_name = 'Комментарий'  # Название модели в единственном числе
        # Название модели во множественном числе
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'  # Обратное имя по умолчанию
        ordering = ('created_at',)  # Сортировка по дате создания

    def __str__(self):
        """Возвращает строковое представление комментария."""
        return f'Комментарий от {self.author} к отзыву {self.review.id}'
