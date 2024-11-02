from django.contrib import admin

from ficha_tecnica.models import FichaTecnica


# Register your models here.
@admin.register(FichaTecnica)
class FichaTecnicaAdmin(admin.ModelAdmin):
    pass