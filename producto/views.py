from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from tablib import Dataset
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404, HttpResponse
import decimal
from ficha_tecnica.models import FichaTecnica
from nomencladores.almacen.models import Almacen
from .models import Producto
from .forms import ProductoForm
from inventario.models import Inv_Producto
from envase_embalaje.formato.models import Formato
from datetime import date, datetime, timezone
import openpyxl
from openpyxl.styles import Font

@login_required
def exportar_productos_excel(request):
    # Crear el libro y la hoja
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Productos"

    # Definir los encabezados
    encabezados = ["Código", "Nombre", "Formato", "Cantidad", "Costo"]
    ws.append(encabezados)

    # Dar formato a los encabezados (negrita)
    for col in range(1, 6):
        celda = ws.cell(row=1, column=col)
        celda.font = Font(bold=True)

    # Obtener los datos (mismo queryset que usas en la tabla)
    productos = Producto.objects.all()  # Ajusta si hay filtros

    # Agregar los datos fila por fila
    for prod in productos:
        print(prod.formato)
        formato = str(prod.formato.capacidad) + ' ' + prod.formato.unidad_medida
        ws.append([
            prod.codigo_producto,
            prod.nombre_comercial,
            formato,
            prod.cantidad_total,
            prod.costo,
        ])

    # Ajustar ancho de columnas automáticamente (opcional)
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[col_letter].width = adjusted_width

    # Preparar la respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=productos.xlsx'
    wb.save(response)
    return response

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
    template_name = 'producto/form.html'
    success_url = reverse_lazy('producto_final_list')

class ActualizarProductoView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto/form.html'
    success_url = reverse_lazy('list_producto')

class EliminarProductoView(DeleteView):
    model = Producto
    template_name = 'producto/eliminar_producto_final.html'
    success_url = reverse_lazy('producto_final_list')

class DetalleProductoView(DetailView):
    model = Producto
    template_name = 'producto/detalle_producto_final.html'

class CreateImportView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto/import_form.html'
    success_url = '/producto/'
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
                Col_3l = 2
                Col_Almacen = 3
                Col_Cantidad = 4
                Col_Formato = 5
                Col_Costo = 6
                i = 0
                print(f"Entrando al ciclo:{len(imported_data)}")
                for data in imported_data:
                    codigo = str(data[Col_Codigo]).strip() if data[Col_Codigo] is not None else None
                    nombre = str(data[Col_Nombre]).strip() if data[Col_Nombre] is not None else None  # Asegúrate de que sea un string
                    codigo_3l = str(data[Col_3l]).strip() if data[Col_3l] is not None else None
                    cantidad = str(data[Col_Cantidad]).strip() if data[Col_Cantidad] is not None else None
                    almacen = str(data[Col_Almacen]).strip() if data[Col_Almacen] is not None else None
                    formato = str(data[Col_Formato]).strip() if data[Col_Formato] is not None else None  # Convertir a minúsculas
                    costo = str(data[Col_Costo]).strip() if data[Col_Costo] is not None else None
                    
                    # Validaciones de los datos
                    if not all(
                            [codigo, nombre, codigo_3l, cantidad, almacen, formato, costo]):
                        print(f"Fila {i}: Todos los campos son obligatorios.")
                        messages.error(request, f"Fila {i}: Todos los campos son obligatorios.")
                        return redirect('importarProducto')

                    almacen_obj = Almacen.objects.filter(nombre__iexact=almacen).first()
                    if almacen_obj is None:
                        print("No existe el almacen")
                        messages.error(request,
                                       f"Fila {i}: No existe el almacén  '{str(data[Col_Almacen]).strip()}' en el nomenclador")
                        return redirect('importarProducto')
                    else:
                        print(f"Almacen {almacen_obj.nombre}")

                    if len(nombre) > 255:
                        messages.error(request,
                                       f"Fila {i}: El nombre del producto no puede exceder 255 caracteres.")
                        return redirect('importarProducto')

                    if len(codigo) > 20:
                        messages.error(request,
                                       f"Fila {i}: El código no puede exceder 20 caracteres.")
                        return redirect('importarProducto')

                    if len(codigo_3l) > 3:
                        messages.error(request,
                                       f"Fila {i}: El código corto solo debe tener 3 letras.")
                        return redirect('importarProducto')

                    if not cantidad.isdigit() or int(cantidad) < 0:
                        messages.error(request,
                                       f"Fila {i}: 'Cantidad' debe ser un número entero.")
                        return redirect('importarProducto')
                    
                    print(f"Validaciones OK")
                    
                    cap_str = ''          
                    for j in formato:
                        try:
                            if int(j) or j == '0':
                                cap_str = cap_str + j
                            else:
                                break
                        except:
                            break
                    if cap_str == '':
                        capacidad = 0
                    else:
                        capacidad = int(cap_str)
                    if 'kg' in formato.lower():
                        um = 'KG'
                    elif 'ml' in formato.lower():
                        um = 'ML'
                    elif 'l' in formato.lower():
                        um = 'L'
                    elif 'granel' in formato.lower():
                        capacidad = 0
                        um = 'L'
                    else:
                        um = 'U'

                    print(f"UM: {um} capacidad: {capacidad}")


                    formato_o = Formato.objects.filter(unidad_medida=um, capacidad=capacidad).first()
                    if not formato_o:
                        formato_o = Formato.objects.create(unidad_medida=um, capacidad=capacidad)


                    print(f"Formato: {formato_o}")

                    #cantidad_dig = int(cantidad)  # Convertimos a entero después de la validación
                    
                    try:
                        producto, created_prod = Producto.objects.update_or_create(                    
                            nombre_comercial=nombre,
                            formato=formato_o,
                            defaults={
                            'codigo_producto' : codigo,
                            'costo' : costo,
                            'codigo_3l' : codigo_3l
                            }
                        )

                        if created_prod:
                            print(f"Creado producto {producto.nombre_comercial}")
                        else:
                            print(f"No creado el producto {producto.nombre_comercial}")

                        producto.clean()  
                        producto.save()

                        #Ahora a actualizar inventario
                        inventario_prod, created_inv = Inv_Producto.objects.get_or_create(
                            producto=producto, almacen=almacen_obj)
                        if created_inv:
                            print('Creado inventario')
                            fecha_actual = datetime.now()
                            fecha_codigo = fecha_actual.strftime('%y%m%d')
                            lote = f"{fecha_codigo}-{producto.codigo_3l}-0000-{str(producto.formato)}"
                            inventario_prod.lote = lote
                        else:
                            print('No fue ceado el inventario')
                            print(inventario_prod.almacen)
                        inventario_prod.cantidad = decimal.Decimal(cantidad)
                        inventario_prod.save()

                        No_fila += 1   #Incrementa solo si se guarda correctamente

                    except Exception as e:
                        print(f"Error al procesar la fila {i + 1}: {str(e)}")
                        messages.error(request, f"Error al procesar la fila {i + 1}: {str(e)}")
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
    return render(request, 'producto/import_form.html')
