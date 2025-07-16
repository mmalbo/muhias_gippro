from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_tables2 import tables, Column


class ModeloBaseTabla(tables.Table):
    acciones = Column(
        empty_values=(),
        exclude_from_export=True,
    )

    class Meta:
        exclude = [
            "id",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        sequence = [
            "...",
            "acciones",
        ]

    def render_acciones(self, record):
        button_group = f"""
        <div class="btn-group btn-group-sm me-2 mb-2" role="group" aria-label="Icons File group">
                  <a href="{record.actualizacion_url()}" class="btn ">
                    <i class="fa fa-fw fa-pen"></i>
                  </a>
                  <a href="{record.detalle_url()}" class="btn ">
                    <i class="fa fa-fw fa-eye"></i>
                  </a>
                </div>
        """
        return format_html(
            "{}",
            mark_safe(button_group),
        )
