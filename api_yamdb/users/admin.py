from django.contrib import admin

from users.models import User

admin.site.empty_value_display = 'Не задано'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'role', 'is_staff',
    )
    search_fields = ('username', 'email',)
    ordering = ('username',)
    list_filter = ('role',)
