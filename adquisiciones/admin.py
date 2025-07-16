from django.contrib import admin
from adquisiciones.models import Adquisicion, DetallesAdquisicion

# Register your models here.
@admin.register(Adquisicion)
class AdquisicionAdmin(admin.ModelAdmin):
    pass

@admin.register(DetallesAdquisicion)
class DetallesAdquisicionAdmin(admin.ModelAdmin):
    pass