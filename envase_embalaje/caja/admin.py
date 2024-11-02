from django.contrib import admin
from envase_embalaje.caja.models import Caja

@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tamanno', 'material', 'codigo')  # Añade 'codigo' aquí
    search_fields = ('nombre', 'tamanno', 'codigo')  # Permite buscar por 'codigo'

    def codigo(self, obj):
        return obj.codigo  # Devuelve el código del TipoEnvaseEmbalaje
    codigo.admin_order_field = 'codigo'  # Permite ordenar por este campo
    codigo.short_description = 'Código'  # Nombre que se mostrará en el admin