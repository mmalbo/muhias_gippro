from django.contrib import admin

from materia_prima.tipo_materia_prima.models import TipoMateriaPrima


# Register your models here.
@admin.register(TipoMateriaPrima)
class TipoMateriaPrimaAdmin(admin.ModelAdmin):
    pass
