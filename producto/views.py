from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from tablib import Dataset

from ficha_tecnica.models import FichaTecnica
from nomencladores.almacen.models import Almacen
from .models import Producto
from .forms import ProductoForm


class ListaProductoView(ListView):
    model = Producto
    template_name = 'producto_final/lista_producto_final.html'
    context_object_name = 'productos_finales'

    def get_context_data(self, **kwargs):
        # Llama al método de la clase base
        context = super().get_context_data(**kwargs)

        # Agrega mensajes al contexto si existen
        if 'mensaje_error' in self.request.session:
            messages.error(self.request, self.request.session.pop('mensaje_error'))
        if 'mensaje_warning' in self.request.session:
            messages.warning(self.request, self.request.session.pop('mensaje_warning'))
        if 'mensaje_succes' in self.request.session:
            messages.success(self.request, self.request.session.pop('mensaje_succes'))
        return context


class CrearProductoView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_final/form.html'
    success_url = reverse_lazy('producto_final_list')


class ActualizarProductoView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_final/form.html'
    success_url = reverse_lazy('producto_final_list')


class EliminarProductoView(DeleteView):
    model = Producto
    template_name = 'producto_final/eliminar_producto_final.html'
    success_url = reverse_lazy('producto_final_list')


class DetalleProductoView(DetailView):
    model = Producto
    template_name = 'producto_final/detalle_producto_final.html'


class CreateImportView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_final/import_form.html'
    success_url = '/producto_final/'
    success_message = "Se ha importado correctamente la caja."


def importar(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')
        No_fila = 0
        producto_existentes = []

        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('importarProducto')

        try:
            with (transaction.atomic()):
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)
                Col_Coddigo = 0
                Col_Nombre = 1
                Col_FichaTecnica = 2
                Col_Almacen = 3
                Col_Cantidad = 4
                Col_Producto = 5
                i = 0
                while i <= len(imported_data):
                    data = imported_data[i]
                    codigo = str(data[Col_Coddigo]).strip() if data[Col_Coddigo] is not None else None

                    i += 1

                    nombre = str(data[Col_Nombre]).strip() if data[
                                                                  Col_Nombre] is not None else None  # Asegúrate de que sea un string
                    cantidad = str(data[Col_Cantidad]).strip() if data[Col_Cantidad] is not None else None
                    ficha_tecnica = str(data[Col_FichaTecnica]).strip() if data[
                                                                               Col_FichaTecnica] is not None else None
                    almacen = str(data[Col_Almacen]).strip() if data[Col_Almacen] is not None else None
                    es_final = str(data[Col_Producto]).strip().lower()  # Convertir a minúsculas
                    # Validar el campo 'propio'
                    if es_final not in ['si', 'no']:
                        messages.error(request,
                                       f'En la fila {No_fila + 2} el valor para "Producto final" debe ser "si" o "no". Valor '
                                       f'recibido: {data[5] if data[5] is not None else "Ninguno"}')
                        return redirect('importarProducto')

                    es_final = True if es_final == 'sí' or es_final=='si' else False
                    existe = Producto.objects.filter(codigo_producto__iexact=codigo, product_final=es_final).first()
                    if existe:
                        producto_existentes.append(codigo)
                        No_fila += 1  # Incrementa solo si se guarda correctamente
                        continue  # Si ya existe, saltamos a la siguiente fila

                    # Validaciones de los datos
                    if not all(
                            [codigo, nombre, cantidad, ficha_tecnica, almacen]):
                        messages.error(request, f"Fila {No_fila + 2}: Todos los campos son obligatorios.")
                        return redirect('importarProducto')

                    ficha_tecnica = FichaTecnica.objects.filter(nombre_quimico__iexact=ficha_tecnica).first()
                    if ficha_tecnica is None:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: No existe el nombre de la ficha técnica "
                                       f"'{str(data[Col_FichaTecnica]).strip()}' en el nomenclador")
                        return redirect('importarProducto')
                    ficha_tecnica_producto= Producto.objects.filter(ficha_tecnica_folio=ficha_tecnica).first()
                    if ficha_tecnica_producto:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: Ya existe un producto registrado con la ficha técnica "
                                       f"'{str(data[Col_FichaTecnica]).strip()}'.")
                        return redirect('importarProducto')
                    almacen = Almacen.objects.filter(nombre__iexact=almacen).first()
                    if almacen is None:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: No existe el almacén  '{str(data[Col_Almacen]).strip()}' en el nomenclador")
                        return redirect('importarProducto')

                    if len(nombre) > 255:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: El nombre de la materia prima no puede exceder 255 caracteres.")
                        return redirect('importarProducto')

                    if len(codigo) > 20:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: El código no puede exceder 20 caracteres.")
                        return redirect('importarProducto')

                    if not cantidad.isdigit() or int(cantidad) <= 0:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: 'Cantidad' debe ser un número entero mayor que cero.")
                        return redirect('importarProducto')

                    cantidad = int(cantidad)  # Convertimos a entero después de la validación

                    try:
                        producto = Producto(
                            codigo_producto=codigo,
                            nombre_comercial=nombre,
                            ficha_tecnica_folio=ficha_tecnica,
                            almacen=almacen,  # Asumiendo que este es el ID
                            cantidad_alm=cantidad,
                            product_final=es_final
                        )
                        producto.clean()  # Valida los datos antes de guardar
                        producto.save()
                        No_fila += 1  # Incrementa solo si se guarda correctamente

                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        return redirect('importarProducto')

                # Mensajes finales
                if No_fila > 0:
                    Total_filas = No_fila - len(producto_existentes)
                    messages.success(request, f'Se han importado {Total_filas} materias primas satisfactoriamente.')
                    if producto_existentes:
                        messages.warning(request,
                                         'Las siguientes materias primas ya se encontraban registradas: ' + ', '.join(
                                             producto_existentes))
                        return redirect('importarProducto')

                else:
                    if producto_existentes:
                        messages.warning(request,
                                         'Las siguientes materias primas ya se encontraban registradas: ' + ', '.join(
                                             producto_existentes))
                        return redirect('importarProducto')

                    else:
                        messages.warning(request, "No se importó ningún formato.")
                        return redirect('importarProducto')

                return redirect('producto_list')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('producto_list')
    return render(request, 'producto_final/import_form.html')
