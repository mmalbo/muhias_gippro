from django.contrib import admin
from .models import Formato

@admin.register(Formato)
class FormatoAdmin(admin.ModelAdmin):
    list_display = ('unidad_medida', 'capacidad')  # Campos que se mostrarán en la lista del admin
    search_fields = ('unidad_medida',)  # Campos que se pueden buscar
    list_filter = ('capacidad',)  # Permite filtrar por capacidad

    def get_queryset(self, request):
        # Puedes personalizar la consulta aquí si es necesario
        queryset = super().get_queryset(request)
        return queryset

    def save_model(self, request, obj, form, change):
        # Puedes realizar alguna acción adicional al guardar el modelo aquí
        super().save_model(request, obj, form, change)

    def clean(self):
        # Si necesitas una validación adicional, puedes incluirla aquí
        super().clean()