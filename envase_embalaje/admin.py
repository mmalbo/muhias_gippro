from django.contrib import admin
from envase_embalaje.models import EnvaseEmbalaje


# Register your models here.
@admin.register(EnvaseEmbalaje)
class EnvaseEmbalajeAdmin(admin.ModelAdmin):
    pass
