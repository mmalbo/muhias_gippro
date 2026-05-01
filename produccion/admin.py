from django.contrib import admin

from produccion.models import Produccion, PruebaQuimica, ParametroPrueba, DetallePruebaQuimica, Prod_Inv_MP, Prod_Inv_Producto
#, Sol_Mat_Primas, Sol_Prod_Base


# Register your models here.
@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):
    pass

@admin.register(Prod_Inv_MP)
class MP_ProdAdmin(admin.ModelAdmin):
    pass
@admin.register(Prod_Inv_Producto)
class PP_ProdAdmin(admin.ModelAdmin):
    pass

@admin.register(ParametroPrueba)
class ParametroPruebaAdmin(admin.ModelAdmin):
    pass

@admin.register(PruebaQuimica)
class PruebaQuimicaAdmin(admin.ModelAdmin):
    pass

@admin.register(DetallePruebaQuimica)
class DetallePruebaQuimicaAdmin(admin.ModelAdmin):
    pass


