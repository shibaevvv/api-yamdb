from django.contrib import admin
from django.contrib.auth import get_user_model

from reviews.models import Category, Genre, GenreTitle, Title, User

admin.site.empty_value_display = 'Не задано'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'role', 'is_staff',
    )
    search_fields = ('username', 'email',)
    ordering = ('username',)
    list_filter = ('role',)


admin.site.register(Category)
admin.site.register(Genre)
admin.site.register(Title)
admin.site.register(GenreTitle)
