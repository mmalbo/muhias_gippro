from django.contrib import admin
from materia_prima.models import MateriaPrima


# Register your models here.
@admin.register(MateriaPrima)
class MateriaPrimaAdmin(admin.ModelAdmin):
    pass
