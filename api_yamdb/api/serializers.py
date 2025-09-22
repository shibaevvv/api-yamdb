from rest_framework import serializers
from reviews.models import Review, Title, User
# импортируем DRF-сериализаторы и модели (Review – отзыв, Title – произведение, User – пользователь)


class ReviewSerializer(serializers.ModelSerializer):
    # создаём сериализатор для модели Review
    # ModelSerializer автоматически строит поля на основе модели
    
    author = serializers.ReadOnlyField(source='author.username')
    # поле author будет только для чтения (ReadOnlyField)
    # вместо объекта User будет выводиться username автора
    # source='author.username' — указывает, что брать имя пользователя из связанного поля author

    class Meta:
        model = Review  # указываем, что сериализатор работает с моделью Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        # перечисляем поля, которые будут в JSON-ответе
        read_only_fields = ('id', 'author', 'pub_date')
        # эти поля будут только для чтения — нельзя изменять при создании/обновлении

    def validate_score(self, value):
        # кастомная валидация отдельного поля score (оценка)
        if not (1 <= value <= 10):
            # если оценка не попадает в диапазон 1–10
            raise serializers.ValidationError("Оценка должна быть в диапазоне от 1 до 10.")
        return value  # если всё ок, возвращаем значение

    def validate(self, attrs):
        """
        Проверка, что пользователь оставляет не более одного отзыва на одно Title.
        Проверка выполняется только при POST (создании).
        """
        request = self.context.get('request')
        # в context сериализатор получает request, view и др. (контекст задаётся во ViewSet)
        view = self.context.get('view')

        if request is None or view is None:
            # если контекста нет (например, сериализатор вызван вручную) — просто пропускаем проверку
            return attrs

        if request.method != 'POST':
            # проверку делаем только при создании отзыва (POST)
            return attrs

        user = request.user  # текущий пользователь
        title_id = view.kwargs.get('title_id')
        # достаём id произведения (title) из URL-параметров (например, /api/titles/5/reviews/)

        if title_id is None:
            return attrs  
            # если id нет — проверку не делаем (дальше во view скорее всего вернётся 404)
            # можно было бы и здесь бросить ValidationError, но автор кода решил мягко пропустить

        # проверим, есть ли уже отзыв этого пользователя на это произведение
        existing = Review.objects.filter(title_id=title_id, author=user).exists()
        if existing:
            # если такой отзыв уже существует — поднимаем ошибку
            raise serializers.ValidationError("Вы уже оставили отзыв на это произведение.")

        return attrs  # если всё прошло — возвращаем attrs без изменений
