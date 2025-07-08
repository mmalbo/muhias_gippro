from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from usuario.models import CustomUser

# Register your models here.
@admin.register(CustomUser)
class UsuariosAdmin(UserAdmin):
    passlist_display = ('username', 'email', 'is_staff')  # NO incluyas 'password'
    fieldsets = (
            (None, {'fields': ('username', 'password')}), #¡OJO! Esto requiere hashear la contraseña antes de guardar
            ('Información Personal', {'fields': ('email', 'first_name', 'last_name')}),
            ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
            ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
        )

#admin.site.register(CustomUser,UsuariosAdmin)