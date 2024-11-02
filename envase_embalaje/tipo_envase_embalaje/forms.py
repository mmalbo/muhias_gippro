from django import forms
from .models import TipoEnvaseEmbalaje

class TipoEnvaseEmbalajeForm(forms.ModelForm):
    class Meta:
        model = TipoEnvaseEmbalaje
        fields = ['tipo_envase_embalaje']