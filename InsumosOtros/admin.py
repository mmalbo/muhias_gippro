from django.contrib import admin
from InsumosOtros.models import InsumosOtros


# Register your models here.
@admin.register(InsumosOtros)
class InsumosOtrosAdmin(admin.ModelAdmin):
    pass
