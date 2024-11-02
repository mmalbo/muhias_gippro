import django_filters


class ModeloBaseFilterSet(django_filters.FilterSet):
    class Meta:
        fields = "__all__"
        exclude = [
            "id",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
