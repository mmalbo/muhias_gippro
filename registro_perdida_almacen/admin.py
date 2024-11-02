from django.contrib import admin

from registro_perdida_almacen.models import MateriaPrimaAlmacen


# Register your models here.
@admin.register(MateriaPrimaAlmacen)
class MateriaPrimaAlmacenAdmin(admin.ModelAdmin):
    pass
