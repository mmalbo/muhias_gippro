from django.contrib import admin

from movimientos.models import Vale_Movimiento_Almacen, Conduce, Movimiento_MP


# Register your models here.
@admin.register(Movimiento_MP)
class Movimiento_MPAdmin(admin.ModelAdmin):
    pass

@admin.register(Vale_Movimiento_Almacen)
class Vale_Movimiento_AlmacenAdmin(admin.ModelAdmin):
    pass


# Register your models here.
@admin.register(Conduce)
class ConduceAdmin(admin.ModelAdmin):
    pass