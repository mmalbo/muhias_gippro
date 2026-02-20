from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from tablib import Dataset
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404

from ficha_tecnica.models import FichaTecnica
from nomencladores.almacen.models import Almacen
from .models import Producto
from .forms import ProductoForm
from inventario.models import Inv_Producto

@login_required
def listProductos(request):
    almacen_id = request.GET.get('almacen')
    producto_id = request.GET.get('producto')
    
    almacen = None
    if request.user.groups.filter(name='Almaceneros').exists():
        almacen = Almacen.objects.filter(responsable=request.user).first()

    inv_productos = Inv_Producto.objects.select_related('producto', 'almacen')
    
    if request.user.groups.filter(name='Presidencia-Admin').exists() or request.user.is_staff:
        if almacen_id and almacen_id != 'todos':
            inv_productos = inv_productos.filter(almacen=almacen_id)
    else:
        if almacen:
            inv_productos = inv_productos.filter(almacen=almacen)
        else:
            inv_productos = Inv_Producto.objects.none()

    if producto_id:
        inv_productos = inv_productos.filter(producto=producto_id)

    inv_productos = inv_productos.order_by('producto__nombre_comercial', 'almacen__nombre')
    almacenes = Almacen.objects.all()
    productos = Producto.objects.all()
    total_productos = productos.count()

    context = {
        'inv_productos':inv_productos,
        'almacenes':almacenes,
        'productos':productos,
        'almacen_id':almacen_id,
        'producto_id':producto_id,
        'almacen':almacen,
        'total_productos':total_productos,
        'es_admin': request.user.groups.filter(name='Presidencia-Admin').exists(),
        'es_almacenero': request.user.groups.filter(name='Almaceneros').exists(),
    }

    return render(request, 'producto/producto_list.html', context)

def get_productos(request, pk):
    try:
        almacen = Almacen.objects.get(pk=pk)
        productos = almacen.inventarios_prod.all()
        productos_data = [{'nombre': producto.nombre_comercial, 'nombre_almacen': almacen.nombre} for producto in
                                productos]

        return JsonResponse(productos_data, safe=False)
    except Almacen.DoesNotExist:
        raise Http404("Producto no encontrado")
    
class ListaProductoView(ListView):
    model = Producto
    template_name = 'producto/producto_cat.html'
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
    template_name = 'producto/form.html'
    success_url = reverse_lazy('list_producto')

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
    success_message = "Se ha importado correctamente."

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
                Col_Codigo = 0
                Col_Nombre = 1
                Col_Almacen = 2
                Col_Cantidad = 3
                Col_Formato = 4
                Col_Costo = 5
                i = 0
                print("Entrando al ciclo:")
                while i <= len(imported_data):
                    data = imported_data[i]
                    codigo = str(data[Col_Codigo]).strip() if data[Col_Codigo] is not None else None
                    nombre = str(data[Col_Nombre]).strip() if data[Col_Nombre] is not None else None  # Asegúrate de que sea un string
                    cantidad = str(data[Col_Cantidad]).strip() if data[Col_Cantidad] is not None else None
                    almacen = str(data[Col_Almacen]).strip() if data[Col_Almacen] is not None else None
                    formato = str(data[Col_Formato]).strip() if data[Col_Almacen] is not None else None  # Convertir a minúsculas
                    costo = str(data[Col_Costo]).strip() if data[Col_Almacen] is not None else None

                    print(codigo)
                    print(formato)
                    
                    existe = Producto.objects.filter(codigo_producto__iexact=codigo)
                    if existe:
                        print("Ya existe "+nombre)
                        producto_existentes.append(codigo)
                        i += 1  # Incrementa solo si se guarda correctamente
                        continue  # Si ya existe, saltamos a la siguiente fila

                    # Validaciones de los datos
                    if not all(
                            [codigo, nombre, cantidad, almacen, formato, costo]):
                        print("Falta algo")
                        messages.error(request, f"Fila {i}: Todos los campos son obligatorios.")
                        return redirect('importarProducto')

                    almacen_obj = Almacen.objects.filter(nombre__iexact=almacen).first()
                    print(almacen_obj)
                    if almacen_obj is None:
                        print("No existe el almacen")
                        messages.error(request,
                                       f"Fila {i}: No existe el almacén  '{str(data[Col_Almacen]).strip()}' en el nomenclador")
                        return redirect('importarProducto')

                    """if len(nombre) > 255:
                        messages.error(request,
                                       f"Fila {i}: El nombre del producto no puede exceder 255 caracteres.")
                        return redirect('importarProducto')

                    if len(codigo) > 20:
                        messages.error(request,
                                       f"Fila {i}: El código no puede exceder 20 caracteres.")
                        return redirect('importarProducto')

                    if not cantidad.isdigit() or int(cantidad) < 0:
                        messages.error(request,
                                       f"Fila {i}: 'Cantidad' debe ser un número entero.")
                        return redirect('importarProducto')"""

                    cantidad_dig = int(cantidad)  # Convertimos a entero después de la validación

                    try:
                        producto = Producto(
                            codigo_producto=codigo,
                            nombre_comercial=nombre,
                            costo = costo,
                            formato = formato                                                        
                        )
                        #producto.clean()  # Valida los datos antes de guardar
                        producto.save()
                        print(producto)
                        
                        #almacen=almacen,  # Asumiendo que este es el ID
                        #cantidad_alm=cantidad,
                        
                        No_fila += 1   #Incrementa solo si se guarda correctamente

                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {No_fila + 1}: {str(e)}")
                        return redirect('importarProducto')

                    i += 1

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
