from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Inv_Mat_Prima, Inv_Insumos, Inv_Envase


# Register your models here.
@admin.register(Inv_Mat_Prima)
class Inv_Mat_PrimaAdmin(admin.ModelAdmin):
    pass

@admin.register(Inv_Envase)
class Inv_EnvaseAdmin(admin.ModelAdmin):
    pass

@admin.register(Inv_Insumos)
class Inv_InsumosAdmin(admin.ModelAdmin):
    pass