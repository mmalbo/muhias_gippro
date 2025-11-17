class CrearProduccionView(View):
    template_name = 'produccion/crear_produccion.html'
    
    def get(self, request):
        produccion_form = ProduccionForm()
        materia_prima_form = MateriaPrimaForm()
        
        # Inicializar sesión si no existe
        if 'produccion_data' not in request.session:
            request.session['produccion_data'] = {}
        
        context = {
            'produccion_form': produccion_form,
            'materia_prima_form': materia_prima_form,
            'materias_primas_json': self.get_materias_primas_json(),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        step = request.POST.get('step')
        
        if step == '1':
            return self.procesar_paso_1(request)        
        elif step == '2':
            return self.procesar_paso_2(request)
        else:
            return JsonResponse({'success': False, 'errors': 'Paso no válido'})
    
    def procesar_paso_1(self, request):
        """Guardar solo los valores primitivos en sesión"""
        produccion_form = ProduccionForm(request.POST)
        if produccion_form.is_valid():
            print(request.POST.get('nuevo_producto_nombre'))
            print("---")
            print(Formato.objects.filter(capacidad=0).first())
            if request.POST.get('nuevo_producto_nombre'):
                # crear productoget_or_
                prod_catalog = Producto.objects.create(
                nombre_comercial=request.POST.get('nuevo_producto_nombre'),
                estado='produccion',
                formato=Formato.objects.filter(capacidad=0).first(),
                costo=request.POST.get('costo')
                )
            else:
                prod_catalog = request.POST.get('catalogo_producto')
            # Extraer solo datos primitivos para la sesión
            print("----")
            print(prod_catalog)
            print("---***----")
            session_data = {
                'lote': request.POST.get('lote'),
                'catalogo_producto': prod_catalog,
                'cantidad_estimada': request.POST.get('cantidad_estimada'),
                'costo': request.POST.get('costo'),
                'prod_result': request.POST.get('prod_result'),
                'planta_id': request.POST.get('planta'),  # Guardar el ID como string
            }            
            # Guardar en sesión
            request.session['produccion_data'] = session_data
            request.session.modified = True
            print("Datos sesion 1: ", request.session['produccion_data'])
            return JsonResponse({'success': True, 'step': 2})
        else:
            return JsonResponse({'success': False, 'errors': produccion_form.errors})
    
    def procesar_paso_2(self, request):
        # Recuperar datos del paso 1 de la sesión
        
        produccion_data = request.session.get('produccion_data', {})
        
        print("Datos en sesión 2:", produccion_data)  # Para debug
        
        if not produccion_data:
            return JsonResponse({
                'success': False, 
                'errors': 'Datos de producción no encontrados. Por favor, complete el paso 1 nuevamente.'
            })
            
        
        # Verificar que los datos mínimos estén presentes
        required_fields = ['lote', 'catalogo_producto', 'cantidad_estimada', 'costo', 'planta_id']
        missing_fields = [field for field in required_fields if not produccion_data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False, 
                'errors': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            })
        
        # Procesar materias primas
        materias_primas = self.procesar_materias_primas(request.POST)
        
        if not materias_primas:
            return JsonResponse({'success': False, 'errors': 'Debe agregar al menos una materia prima'})
        
        try:
            # Obtener la instancia de Planta
            from .models import Planta
            planta_instance = Planta.objects.get(id=produccion_data['planta_id'])

            if produccion_data['prod_result']: 
                product=True
            else:
                product=False
            
            # Guardar producción
            produccion = Produccion.objects.create(
                lote=produccion_data['lote'],
                catalogo_producto=produccion_data['catalogo_producto'],
                cantidad_estimada=produccion_data['cantidad_estimada'],
                costo=produccion_data['costo'],
                prod_result=product,
                planta=planta_instance,
                estado='Planificada'
            )
            
            # Guardar materias primas
            for mp_data in materias_primas:
                Inv_Mat_Prima.objects.create(
                    #produccion=produccion,
                    materia_prima=mp_data['materia_prima'],
                    almacen=mp_data['almacen'],
                    cantidad=mp_data['cantidad']
                )
            
            # Limpiar sesión
            if 'produccion_data' in request.session:
                del request.session['produccion_data']
                request.session.modified = True
            
            return JsonResponse({
                'success': True, 
                'message': 'Producción creada exitosamente', 
                'produccion_id': produccion.id,
                'redirect_url': reverse('produccion_list')  # Ajusta esta URL
            })
            
        except Planta.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'La planta seleccionada no existe'})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': f'Error al guardar: {str(e)}'})

    def get_materias_primas_json(self):
        materias_primas = MateriaPrima.objects.all().values(
            'id', 'nombre', 'tipo_materia_prima', 'conformacion', 'unidad_medida', 'concentracion', 'costo'
        )
        return list(materias_primas)
    
    def procesar_materias_primas(self, post_data):
        materias_primas = []
        i = 0
        
        while f'materias_primas[{i}][materia_prima]' in post_data:
            materia_prima_id = post_data.get(f'materias_primas[{i}][materia_prima]')
            cantidad = post_data.get(f'materias_primas[{i}][cantidad]')
            almacen_id = post_data.get(f'materias_primas[{i}][almacen]')
            
            if materia_prima_id and cantidad and almacen_id:
                try:
                    materia_prima = MateriaPrima.objects.get(id=materia_prima_id)
                    almacen = Almacen.objects.get(id=almacen_id)
                    
                    materias_primas.append({
                        'materia_prima': materia_prima,
                        'cantidad': cantidad,
                        'almacen': almacen
                    })
                except (MateriaPrima.DoesNotExist, Almacen.DoesNotExist):
                    pass
            
            i += 1
        
        return materias_primas