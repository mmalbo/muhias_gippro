from django.contrib import admin

from produccion.models import Produccion, Sol_Mat_Primas, Sol_Prod_Base


# Register your models here.
@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):
    pass


@admin.register(Sol_Mat_Primas)
class Sol_Mat_PrimasAdmin(admin.ModelAdmin):
    pass


@admin.register(Sol_Prod_Base)
class Sol_Prod_BaseAdmin(admin.ModelAdmin):
    pass
