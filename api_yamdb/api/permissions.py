from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOnlyPermission(BasePermission):
    """Доступ только с ролью администратора."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin()


class IsAdminOrReadOnly(IsAdminOnlyPermission):
    """Права для категорий / жанров / произведений."""
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS or (
                (request.user.is_authenticated and (
                    super().has_permission(request, view)
                )
                )
            )
        )


class IsAuthorOrModeratorOrAdmin(BasePermission):
    """
    Разрешает безопасные методы (GET/HEAD/OPTIONS) всем.
    Для небезопасных методов (PATCH/PUT/DELETE) — только автор отзыва,
    модератор (is_staff) или администратор (is_superuser).
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if obj.author == user or user.is_staff or user.is_superuser:
            return True
        return request.user.is_moderator() or request.user.is_admin()
