from django.contrib import admin

from movimientos.models import Vale_Movimiento_Almacen, Movimiento_MP, Movimiento_EE, Movimiento_Ins, Movimiento_Prod, Vale_Salida_Almacen_Produccion


# Register your models here.
@admin.register(Vale_Salida_Almacen_Produccion)
class Vale_Salida_Almacen_ProdAdmin(admin.ModelAdmin):
    pass

@admin.register(Movimiento_Prod)
class Movimiento_ProdAdmin(admin.ModelAdmin):
    pass

@admin.register(Movimiento_MP)
class Movimiento_MPAdmin(admin.ModelAdmin):
    pass

@admin.register(Movimiento_EE)
class Movimiento_EEAdmin(admin.ModelAdmin):
    pass

@admin.register(Movimiento_Ins)
class Movimiento_IAdmin(admin.ModelAdmin):
    pass

@admin.register(Vale_Movimiento_Almacen)
class Vale_Movimiento_AlmacenAdmin(admin.ModelAdmin):
    pass
