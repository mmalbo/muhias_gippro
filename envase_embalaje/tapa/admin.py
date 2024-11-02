from django.contrib import admin

from envase_embalaje.tapa.models import Tapa


# Register your models here.
@admin.register(Tapa)
class TapaAdmin(admin.ModelAdmin):
    pass
