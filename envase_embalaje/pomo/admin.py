from django.contrib import admin

from envase_embalaje.pomo.models import Pomo


# Register your models here.
@admin.register(Pomo)
class PomoAdmin(admin.ModelAdmin):
    pass
