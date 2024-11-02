from django.contrib import admin

from produccion.envasado.models import Envasado


# Register your models here.
@admin.register(Envasado)
class EnvasadoAdmin(admin.ModelAdmin):
    pass
