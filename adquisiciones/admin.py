from django.contrib import admin

from adquisiciones.models import Adquisicion


# Register your models here.
@admin.register(Adquisicion)
class AdquisicionAdmin(admin.ModelAdmin):
    pass
