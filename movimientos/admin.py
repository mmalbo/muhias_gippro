from django.contrib import admin

from movimientos.models import Vale_Movimiento_Almacen, Conduce


# Register your models here.
@admin.register(Vale_Movimiento_Almacen)
class Vale_Movimiento_AlmacenAdmin(admin.ModelAdmin):
    pass


# Register your models here.
@admin.register(Conduce)
class ConduceAdmin(admin.ModelAdmin):
    pass
