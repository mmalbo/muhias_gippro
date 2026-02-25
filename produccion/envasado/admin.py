from django.contrib import admin

from produccion.envasado.models import *


# Register your models here.
@admin.register(SolicitudEnvasado)
class EnvasadoAdmin(admin.ModelAdmin):
    pass

# Register your models here.
@admin.register(DetalleEnvasado)
class EnvaseUsadoAdmin(admin.ModelAdmin):
    pass

# Register your models here.
@admin.register(ConsumoInsumoEnvasado)
class InsumoUsadoAdmin(admin.ModelAdmin):
    pass