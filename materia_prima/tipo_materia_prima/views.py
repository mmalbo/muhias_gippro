from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView, CreateView
from tablib import Dataset
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect

from .forms import TipoMateriaPrimaForm
from .models import TipoMateriaPrima
from materia_prima.tipo_materia_prima.choices import CHOICE_TIPO
from materia_prima.filter import *


class ListaTiposMateriaPrimaView(ListView):
    model = TipoMateriaPrima
    template_name = 'tipo_materia_prima/lista.html'
    context_object_name = 'tipos_materias_primas'

    def get_queryset(self):
        consulta = super().get_queryset()
        self.filter = Filtro_Tipo(self.request.GET, queryset=consulta) #crea el objeto filtro
        if self.filter:
            nombre = self.request.GET.get('nombre')
            tip = self.request.GET.get('tipo')
            
            if nombre: 
                consulta = consulta.filter(nombre__icontains = nombre)
            if tip:
                consulta = consulta.filter(tipo = tip)
            
		#else:
		#	return self.filter.qs
        return consulta

    def get_context_data(self, **kwargs):
        # Llama al método de la clase base
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter

        # Agrega mensajes al contexto si existen
        if 'mensaje_error' in self.request.session:
            messages.error(self.request, self.request.session.pop('mensaje_error'))
        if 'mensaje_warning' in self.request.session:
            messages.warning(self.request, self.request.session.pop('mensaje_warning'))
        if 'mensaje_succes' in self.request.session:
            messages.success(self.request, self.request.session.pop('mensaje_succes'))
        return context


class CrearTipoMateriaPrimaView(CreateView):
    model = TipoMateriaPrima
    form_class = TipoMateriaPrimaForm
    template_name = 'tipo_materia_prima/form.html'
    success_url = reverse_lazy('tipo_materia_prima:lista')
    success_message = "Se ha creado correctamente el almacén."


class ActualizarTipoMateriaPrimaView(UpdateView):
    model = TipoMateriaPrima
    form_class = TipoMateriaPrimaForm
    template_name = 'tipo_materia_prima/form.html'
    success_url = reverse_lazy('tipo_materia_prima:lista')
    success_message = "Se ha modificado correctamente el almacén."


class EliminarTipoMateriaPrimaView(DeleteView):
    model = TipoMateriaPrima
    template_name = 'tipo_materia_prima/eliminar.html'
    success_url = '/tipos_materia_prima/'

class CreateImportView(CreateView):
    model = TipoMateriaPrima
    form_class = TipoMateriaPrimaForm
    template_name = 'tipo_materia_prima/import_form.html'
    success_url = '/tipo_materia_prima/'

def importarTipoMP(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')  # Cambia el nombre de la variable si es necesario
        tipoMP_existentes = []
        No_fila = 0

        # Validar el archivo
        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('tipo_materia_prima:importarTipoMP')

        """ tipo_mapeo = { 'bases':'Bases', 
                    'color': 'Color',
                    'conservantes': 'Conservantes',
                    'espesantes': 'Espesantes',
                    'fragancias': 'Fragancias',
                    'humectantes': 'Humectantes',
                    'otros': 'Otros',
                    'tensoactivos': 'Tensoactivos'} """
        # 2. Obtener las opciones válidas del campo tipo
        campo_tipo = TipoMateriaPrima._meta.get_field('tipo')
        opciones_validas = [opcion[0] for opcion in campo_tipo.choices]
        opciones_validas_lower = [opcion.lower() for opcion in opciones_validas]

        #try:
        with transaction.atomic():
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)

                for data in imported_data:

                    nombre = str(data[1]).strip() if data[1] is not None else None  # Col_Nombre
                    tipo_ex = str(data[2]).strip() if data[2] is not None else None  # Col_Color
                    ing_activo = str(data[3]).strip() if data[3] is not None else None  # Col_descripcion
                    tipo_frag = str(data[4]).strip() if data[4] is not None else None  # Col_descripcion
                    tipo_sust = str(data[5]).strip() if data[5] is not None else None  # Col_descripcion
                    tipo_col = str(data[6]).strip() if data[6] is not None else None  # Col_descripcion

                    """ if tipo_ex:
                        print(tipo_ex)
                        tipo_obj = tipo_mapeo.get(tipo_ex, None)
                        if tipo_obj is None:
                            messages.error(request, f"Fila {No_fila + 1}: El campo 'Tipo' es incorrecto.")
                            return redirect('tipo_materia_prima:importarTipoMP')
                    else:
                        messages.error(request, f"Fila {No_fila + 1}: El campo 'Tipo' en el excel no está incorrecto.")
                        return redirect('tipo_materia_prima:importarTipoMP') """

                    tipo_correcto = None
                    for opcion in opciones_validas:
                        if opcion == tipo_ex:
                            tipo_correcto = opcion
                            break
                        """ else:
                            print(tipo_ex + "=--=" + opcion)
                    print("---")
                    print(tipo_correcto) """

                    if not tipo_correcto:
                        raise ValidationError(f"Valor '{No_fila + 1}' no es un tipo válido. Opciones válidas: {', '.join(opciones_validas)}")
            
                    #codigo_base = generar_formato_codigo(descripcion, color.nombre)
                    
                    #ultimo = Tapa.objects.filter(codigo__icontains=codigo_base).first()
                    existe = TipoMateriaPrima.objects.filter(nombre=nombre,tipo=tipo_correcto).first()

                    if existe:
                        tipoMP_existentes.append(existe.nombre)
                        continue
                    #else:
                    #    codigo = generar_codigo(codigo_base,ultimo)
                    
                    # Validaciones de los datos
                    if not nombre or not tipo_correcto:
                        messages.error(request,
                                       f"Fila {No_fila + 1}: Los campos 'Tipo' y 'Nombre' son obligatorios."
                                    )
                        return redirect('tipo_materia_prima:importarTipoMP')
                    
                    try:
                        tipoMP = TipoMateriaPrima(
                            nombre=nombre,
                            tipo=tipo_correcto,
                            ingrediente_activo=ing_activo,
                            tipo_fragancia=tipo_frag,
                            tipo_sustancia=tipo_sust, 
                            tipo_color=tipo_col
                        )
                        
                        tipoMP.full_clean()  # Valida los datos antes de guardar
                        tipoMP.save()
                        No_fila += 1
                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {No_fila + 1}: {str(e)}")
                        return redirect('tipo_materia_prima:importarTipoMP')

                # Mensajes de resultado
                if No_fila > 0:
                    Total_filas = No_fila - len(tipoMP_existentes)
                    messages.success(request, f'Se han importado {Total_filas} satisfactoriamente.')
                    if tipoMP_existentes:
                        messages.warning(request, 'Los siguientes códigos ya se encontraban registrados: ' + ', '.join(
                            tipoMP_existentes))
                else:
                    if tipoMP_existentes:
                        messages.warning(request,
                                         'No se importó ningún tipo de materia prima pues se encontraban '
                                         'registrados: ' + ', '.join(
                                             tipoMP_existentes))
                    else:
                        messages.warning(request, "No se importó ningún tipo de materia prima.")

                return redirect('tipo_materia_prima:lista')

        #except Exception as e:
        #    messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
        #    return redirect('tapa:listar')

    return render(request, 'tipo_materia_prima/tipo_import_form.html')
