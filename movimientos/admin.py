from django.contrib import admin

from movimientos.models import Vale_Salida_Almacen, Conduce


# Register your models here.
@admin.register(Vale_Salida_Almacen)
class Vale_Salida_AlmacenAdmin(admin.ModelAdmin):
    pass


# Register your models here.
@admin.register(Conduce)
class ConduceAdmin(admin.ModelAdmin):
    pass
