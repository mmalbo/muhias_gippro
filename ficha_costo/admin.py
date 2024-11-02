from django.contrib import admin

from ficha_costo.models import FichaCosto


# Register your models here.
@admin.register(FichaCosto)
class FichaCostoAdmin(admin.ModelAdmin):
    pass