from django.contrib import admin
from hoja_seguridad.models import HojaSeguridad


# Register your models here.
@admin.register(HojaSeguridad)
class HojaSeguridadAdmin(admin.ModelAdmin):
    pass
