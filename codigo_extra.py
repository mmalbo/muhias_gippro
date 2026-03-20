""" path('envase_adquisicion/', EnvaseAdquisicionListView.as_view(), name='envase_adquisicion_list'),
    path('envase_adquisicion/<uuid:pk>/', EnvaseAdquisicionDetailView.as_view(), name='envase_adquisicion_detail'),
    #path('envase_adquisicion/create/', views.envaseAdquisicionCreateView, name='envase_adquisicion_create'),
    #path('envase_adquisicion/nuevo/', views.envases_add, name='envase_adquisicion_add'),
    path('envase_adquisicion/update/<uuid:pk>/', EnvaseAdquisicionUpdateView.as_view(),
         name='envase_adquisicion_update'),

    path('insumos_adquisicion/', InsumosAdquisicionListView.as_view(), name='insumos_adquisicion_list'),
    path('insumos_adquisicion/<uuid:pk>/', InsumosAdquisicionDetailView.as_view(), name='insumos_adquisicion_detail'),
    #path('insumos_adquisicion/create/', views.insumosAdquisicionCreateView, name='insumos_adquisicion_create'),
    #path('insumos_adquisicion/nuevo/', views.insumos_add, name='insumos_adquisicion_add'),
    path('insumos_adquisicion/update/<uuid:pk>/', InsumosAdquisicionUpdateView.as_view(),
         name='insumos_adquisicion_update'), """

         {% url 'envase_adquisicion_create' %}
         {% url 'envase_adquisicion_list' %}
         {% url 'insumos_adquisicion_create' %}
         {% url 'insumos_adquisicion_list' %}

         # def done(self, form_list, **kwargs):
    #     try:
    #         # Validación explícita de todos los formularios
    #         if not all(form.is_valid() for form in form_list):
    #             raise ValueError("Por favor corrige los errores en los formularios")

    #         # Acceso seguro a cleaned_data
    #         paso1_data = form_list[0].cleaned_data
    #         paso2_data = form_list[1].cleaned_data

    #         if not paso2_data.get('materia_prima'):
    #             raise ValueError("Debes seleccionar una materia prima")

    #         adquisicion = MateriaPrimaAdquisicion.objects.create(
    #             fecha_compra=paso1_data['fecha_compra'],
    #             factura=paso1_data.get('factura'),
    #             importada=paso1_data.get('importada', False),
    #             cantidad=paso1_data.get('cantidad', 1),
    #             materia_prima=paso2_data['materia_prima']
    #         )

    #         return redirect(reverse('adquisicion_detalle', kwargs={'pk': adquisicion.pk}))

    #     except Exception as e:
    #         messages.error(self.request, f"Error: {str(e)}")
    #         return self.render(self.get_form())

    class MateriaPrimaAdquisicionWizard(SessionWizardView):
    form_list = [PasoAdquisicionForm] #, PasoMateriaPrimaForm
    template_name = 'adquisicion/materia_prima/wizard/wizard_form.html'
    file_storage = FileSystemStorage()

    def get_form_list(self):
        form_list = [PasoAdquisicionForm]
        """ print("---")
        print("Dato del form list")
        print("---")
        if '0' in self.request.session.get('wizard_form_data', {}):#self.get_step_data('0')
            dato_limpio = self.get_cleaned_data_for_step('0')
            if dato_limpio:
                cantidad_elem = dato_limpio.get('cantidad_elem', 0)
                for i in range(cantidad_elem):
                    form_list.append(PasoMateriaPrimaForm)
        else:
            print("Fallo el self.request")

        #super().get_form_list()   """
        return form_list
    
    def get_form_initial(self, step): #
        initial = super().get_form_initial(step) or {}
        print("---inicial---")
        print(initial)
        print("-hasta aqui-")
        if step >= '0': #== '1' Esta condicional es para validad que son los forms MP
            if step == '0':
                print("Entro en el step=0")
                step_no = int(step) #Lossteps pasan como string, para usarlo numerivo hay q convertir.
                datos_adquisicion = self.get_cleaned_data_for_step('0')
                cantidad_elem_adq = datos_adquisicion.get('cantidad_elem_adq', 0)

            if 1<=step_no<=cantidad_elem_adq:
                materia_prima_i = step_no-1
                try:
                    materia_prima = MateriaPrimaAdquisicion.objects.filter(materia_prima__nombre=self.request.session.get('nombre', None), index=materia_prima_i)

                    if materia_prima:
                        initial = materia_prima.__dict__
                        initial.pop('_state', None)
                        initial.pop('id', None)
                        initial.pop('materia_prima', None)

                    pass # No encontre una materia prima como esa
                except Exception as e:
                    print(f"Ocurrió un error mientras buscaba si existe la materia prima: {e}")
        # Obtiene datos del paso 0 solo si el formulario es válido
        #form = self.get_form(step='0', data=self.storage.get_step_data(step))
        #if initial.is_valid():            
            #initial.update(form.cleaned_data)
        return initial

    def post(self, request, *args, **kwargs):
        if 'wizard_prev_step' in request.POST:
            # Guarda los datos del paso actual aunque no sean válidos
            form = self.get_form(data=request.POST, files=request.FILES)
            self.storage.set_step_data(self.steps.current, self.process_step(form))
            self.storage.current_step = self.steps.prev
            return self.render(self.get_form())
        return super().post(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        datos_adquisicion = form_list[0].cleaned_data
        datos_materia_prima = []

        for form in form_list[1:]:
            datos_materia_prima.append(form.cleaned_data)

        from .models import Adquisicion, MateriaPrimaAdquisicion
        from materia_prima.models import MateriaPrima

        #Creando la adquisición
        adquisicion, created = Adquisicion.objects.get_or_create(**datos_adquisicion)
        #obteniendo el id de la adquisición creada
        self.request.session['adquisicion_id'] = adquisicion.id

        for i, data in enumerate(datos_materia_prima):
            try:
                materia_prima = MateriaPrima.objects.get(nombre=datos_materia_prima[i].nombre, index=i)
                for key, value in data.items():
                    setattr(materia_prima, key, value)
                materia_prima.save()
            except MateriaPrima.DoesNotExist:
                MateriaPrima.objects.create(index=i, **data)        
        
        return redirect('materia_prima_adquisicion_list')

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        print("Context")
        print(context)
        context['step_number'] = self.steps.index
        return context
    # def done(self, form_list, **kwargs):
    #     try:
    #         # Validación explícita de todos los formularios
    #         if not all(form.is_valid() for form in form_list):
    #             raise ValueError("Por favor corrige los errores en los formularios")

    #         # Acceso seguro a cleaned_data
    #         paso1_data = form_list[0].cleaned_data
    #         paso2_data = form_list[1].cleaned_data

    #         if not paso2_data.get('materia_prima'):
    #             raise ValueError("Debes seleccionar una materia prima")

    #         adquisicion = MateriaPrimaAdquisicion.objects.create(
    #             fecha_compra=paso1_data['fecha_compra'],
    #             factura=paso1_data.get('factura'),
    #             importada=paso1_data.get('importada', False),
    #             cantidad=paso1_data.get('cantidad', 1),
    #             materia_prima=paso2_data['materia_prima']
    #         )

    #         return redirect(reverse('adquisicion_detalle', kwargs={'pk': adquisicion.pk}))

    #     except Exception as e:
    #         messages.error(self.request, f"Error: {str(e)}")
    #         return self.render(self.get_form())


<!--<li class="">
                                        <a href="{% url 'materia_prima_adquisicion_list' %}">
                                            <i class="las la-minus"></i><span>Listar</span>
                                        </a>
                                    </li>-->

                            <script>
        document.addEventListener('DOMContentLoaded', function () {
            const showAlmacenesLinks = document.querySelectorAll('.show_materias_primas');
            const modal = document.getElementById('materia_prima_modal');
            const closeButton = document.getElementsByClassName('close-button')[0];

            showAlmacenesLinks.forEach(function (link) {
                link.addEventListener('click', function (event) {
                    event.preventDefault();
                    const pk = this.dataset.pk;
                    fetch(`/materia_prima/materias_primas/${pk}/`)
                        .then(response => response.json())
                        .then(data => {
                            const almacenesList = document.getElementById('almacenes-list');
                            const modalCodigoMateriaPrima = document.getElementById('modalCodigoMateriaPrima');
                            modalCodigoMateriaPrima.innerHTML = '';
                            almacenesList.innerHTML = '';
                            const codigo = document.createElement('codigo');
                            if (data.length > 0) {
                                data.forEach(almacen => {
                                    const li = document.createElement('li');
                                    li.textContent = almacen.nombre;
                                    codigo.textContent = almacen.nombre_almacen;
                                    almacenesList.appendChild(li);
                                });
                                modalCodigoMateriaPrima.appendChild(codigo);
                            } else {
                                almacenesList.innerHTML = 'No hay materias primas asociadas';
                            }
                            modal.style.display = 'block';
                        });
                });
            });
            window.addEventListener('click', function (event) {
                if (event.target == modal) {
                    modal.style.display = 'none';
                }
            });
        });

        function closeModal() {
            var modal = document.getElementById("materia_prima_modal");
            modal.style.display = "none";
        }
    </script>

    <!-- Agrega este código en la sección donde quieras mostrar el modal -->
        <div id="materia_prima_modal" class="modal" style="text-align: left" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <span class="close-button">&times;</span>
                    <div class="modal-header">
                        <h2>Almacén: <strong><span id="modalCodigoMateriaPrima"></span></strong></h2>
                    </div>
                    <div style="margin-left: 1rem;">
                        <strong><p>Listado de materias primas asociadas:</p></strong>
                    </div>
                    <ul id="almacenes-list"></ul>
                    <div class="modal-footer">
                        <button type="button" onclick="closeModal()"
                                class="btn btn-secondary"
                                data-bs-dismiss="modal">
                            Cerrar
                        </button>
                    </div>
                </div>
            </div>
        </div>

        {% endif %}
                                {#                                 <td>#}
                                {#                                    <a href="#" class="show_materias_primas" data-pk="{{ almacen.pk }}">Ver#}
                                {#                                        materias primas</a>#}
                                {#                                </td> #}

                                 
                                <code class="ms-2">{{ valor }}</code>

<div class="mb-3">
                    {{ wizard.form.codigo.label_tag }}
                    {{ wizard.form.codigo }}
                </div>
                