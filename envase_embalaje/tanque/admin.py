from django.contrib import admin

from envase_embalaje.tanque.models import Tanque


# Register your models here.
@admin.register(Tanque)
class TanqueAdmin(admin.ModelAdmin):
    pass
