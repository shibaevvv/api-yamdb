from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Права для категорий / жанров / произведений."""
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS or
            (request.user and request.user.is_authenticated and
             (request.user.role == 'admin' or request.user.is_superuser))
        )


class IsAuthorOrModeratorOrAdmin(BasePermission):
    """
    Разрешает безопасные методы (GET/HEAD/OPTIONS) всем.
    Для небезопасных методов (PATCH/PUT/DELETE) — только автор отзыва,
    модератор (is_staff) или администратор (is_superuser).
    """

    def has_object_permission(self, request, view, obj):
        # чтение доступно всем
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        # требуем аутентификацию для небезопасных методов
        if not user or not user.is_authenticated:
            return False

        # автору (ForeignKey) — доступ
        try:
            author = obj.author
        except AttributeError:
            return False

        if author == user:
            return True

        # модератор или суперюзер
        if user.is_staff or user.is_superuser:
            return True

        return False
