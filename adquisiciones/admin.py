from django.contrib import admin
from adquisiciones.models import Adquisicion, DetallesAdquisicion, DetallesAdquisicionEnvase, DetallesAdquisicionInsumo

# Register your models here.
@admin.register(Adquisicion)
class AdquisicionAdmin(admin.ModelAdmin):
    pass

@admin.register(DetallesAdquisicion)
class DetallesAdquisicionAdmin(admin.ModelAdmin):
    pass

@admin.register(DetallesAdquisicionEnvase)
class DetallesAdquisicionEnvaseAdmin(admin.ModelAdmin):
    pass

@admin.register(DetallesAdquisicionInsumo)
class DetallesAdquisicionInsumoAdmin(admin.ModelAdmin):
    pass