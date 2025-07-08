from django.contrib import admin
from .models import MateriaPrimaAdquisicion#, EnvaseAdquisicion, InsumosAdquisicion


@admin.register(MateriaPrimaAdquisicion)
class MateriaPrimaAdquisicionAdmin(admin.ModelAdmin):
    list_display = ('id', 'materia_prima', 'adquisicion', 'cantidad')
    search_fields = ('materia_prima__nombre',)  # Suponiendo que MateriaPrima tiene un campo 'nombre'
    #list_filter = ('importada',)
    #ordering = ('fecha_compra',)

""" 
@admin.register(EnvaseAdquisicion)
class EnvaseAdquisicionAdmin(admin.ModelAdmin):
    list_display = ('id', 'envase', 'fecha_compra', 'importada', 'cantidad')
    search_fields = ('envase__nombre',)  # Suponiendo que EnvaseEmbalaje tiene un campo 'nombre'
    list_filter = ('importada',)
    ordering = ('fecha_compra',)


@admin.register(InsumosAdquisicion)
class InsumosAdquisicionAdmin(admin.ModelAdmin):
    list_display = ('id', 'insumo', 'fecha_compra', 'importada', 'cantidad')
    search_fields = ('insumo__nombre',)  # Suponiendo que InsumosOtros tiene un campo 'nombre'
    list_filter = ('importada',)
    ordering = ('fecha_compra',)
 """