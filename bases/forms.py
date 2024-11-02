from django import forms
from django.forms import Textarea


class ModeloBaseModelForm(forms.ModelForm):
    class Meta:
        fields = "__all__"


class ModeloBaseForm(forms.Form):
    pass


class ModeloDenegacionModelForm(ModeloBaseForm):
    causa = forms.CharField(label="Causa de denegacion", widget=Textarea())
