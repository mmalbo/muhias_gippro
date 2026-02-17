from formtools.wizard.views import SessionWizardView
from django.core.files.storage import FileSystemStorage
from .forms import PasoAdquisicionForm, PasoMateriaPrimaForm

class MateriaPrimaAdquisicionWizard(SessionWizardView):
    form_list = [PasoAdquisicionForm]  # Solo el primer paso al principio
    template_name = 'adquisicion/materia_prima/wizard/wizard_form.html'
    file_storage = FileSystemStorage()

    def get_form_list(self):
        """
        Dynamically builds the form list based on data from the first step.
        """
        form_list = [PasoAdquisicionForm]  # Always include the first form

        # Check if the first step has been completed and data is available
        if self.get_step_data('0'):  # '0' is the step number for the first form
            cleaned_data = self.get_cleaned_data_for_step('0')
            if cleaned_data:
                cantidad_materia_prima = cleaned_data.get('cantidad_materia_prima', 0)  # Or whatever field in PasoAdquisicionForm determines the number of repetitions

                # Add the second form (PasoMateriaPrimaForm) the required number of times
                for i in range(cantidad_materia_prima):
                    form_list.append(PasoMateriaPrimaForm)

        return form_list

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        # Add any context needed for the forms themselves
        # You might want to add the current step number as context to the form
        context['step_number'] = self.steps.index

        return context


    def done(self, form_list, **kwargs):
        """
        Handles the completion of the wizard. Processes the data from all forms.
        """
        # Process the data from all forms in form_list
        # Example: save the data to the database

        adquisicion_data = form_list[0].cleaned_data  # Data from PasoAdquisicionForm
        materia_prima_data = []

        # Iterate through the PasoMateriaPrimaForms and extract their data
        for form in form_list[1:]:  # Skip the first form (PasoAdquisicionForm)
            materia_prima_data.append(form.cleaned_data)

        # Now you have all the data. You can save it to the database, etc.
        # Example:

        # from .models import Adquisicion, MateriaPrima  # Import your models

        # # Create an Adquisicion instance
        # adquisicion = Adquisicion.objects.create(**adquisicion_data)

        # # Create MateriaPrima instances for each form
        # for data in materia_prima_data:
        #     MateriaPrima.objects.create(adquisicion=adquisicion, **data)

        # Redirect to a success page or return a HttpResponse
        return redirect('adquisicion_success')  # Replace 'adquisicion_success' with your URL name

from formtools.wizard.views import SessionWizardView
from django.core.files.storage import FileSystemStorage
from .forms import PasoAdquisicionForm, PasoMateriaPrimaForm
from .models import MateriaPrima  # Import your MateriaPrima model

class MateriaPrimaAdquisicionWizard(SessionWizardView):
    form_list = [PasoAdquisicionForm]  # Only the first step initially
    template_name = 'adquisicion/materia_prima/wizard/wizard_form.html'
    file_storage = FileSystemStorage()

    def get_form_list(self):
        """
        Dynamically builds the form list based on data from the first step.
        """
        form_list = [PasoAdquisicionForm]  # Always include the first form

        if self.get_step_data('0'):
            cleaned_data = self.get_cleaned_data_for_step('0')
            if cleaned_data:
                cantidad_materia_prima = cleaned_data.get('cantidad_materia_prima', 0)

                for i in range(cantidad_materia_prima):
                    form_list.append(PasoMateriaPrimaForm)

        return form_list

    def get_form_initial(self, step):
        """
        Populates the MateriaPrimaForm with existing data if available.
        """
        initial = super().get_form_initial(step)

        if step != '0':  # Only apply to MateriaPrimaForm steps
            step_number = int(step)  # Step is passed as a string
            adquisicion_data = self.get_cleaned_data_for_step('0')
            cantidad_materia_prima = adquisicion_data.get('cantidad_materia_prima', 0)

            if 1 <= step_number <= cantidad_materia_prima:  # Check bounds
                # Assuming you have a way to identify existing MateriaPrima instances
                # based on some criteria (e.g., an index, a naming convention, etc.)

                materia_prima_index = step_number -1  # Convert step to index

                # Example: Attempt to load an existing MateriaPrima object
                try:
                    # Modify this lookup logic based on your application's requirements.
                    #  For instance, look up based on a field in PasoAdquisicionForm
                    #  or on a session variable.
                    materia_prima = MateriaPrima.objects.filter(adquisicion__id=self.request.session.get('adquisicion_id', None), index=materia_prima_index).first() #Filter materia prima index based on current index
                    if materia_prima:
                        initial = materia_prima.__dict__ # use dict for form initialization.
                        initial.pop('_state', None) # Remove Django specific state fields
                        initial.pop('id', None) # Remove the ID
                        initial.pop('adquisicion_id', None) # Remove the related ID
                except MateriaPrima.DoesNotExist:
                    pass  # No existing MateriaPrima found for this step
                except Exception as e:
                   print(f"An error occurred while retrieving MateriaPrima: {e}")

        return initial

    def done(self, form_list, **kwargs):
        """
        Handles the completion of the wizard. Processes the data from all forms.
        """
        adquisicion_data = form_list[0].cleaned_data  # Data from PasoAdquisicionForm
        materia_prima_data = []

        for form in form_list[1:]:  # Skip the first form
            materia_prima_data.append(form.cleaned_data)

        from .models import Adquisicion, MateriaPrima  # Import your models

        # Create or update an Adquisicion instance
        adquisicion, created = Adquisicion.objects.get_or_create(**adquisicion_data)

        # Save the adquisicion ID to the session, for accessing at the MateriaPrima level
        self.request.session['adquisicion_id'] = adquisicion.id

        # Create or update MateriaPrima instances
        for i, data in enumerate(materia_prima_data):
            # Check if a MateriaPrima instance already exists for this index
            try:
                materia_prima = MateriaPrima.objects.get(adquisicion=adquisicion, index=i)
                # Update the existing instance
                for key, value in data.items():
                    setattr(materia_prima, key, value) # dynamically sets the attributes
                materia_prima.save()

            except MateriaPrima.DoesNotExist:
                # Create a new MateriaPrima instance
                MateriaPrima.objects.create(adquisicion=adquisicion, index=i, **data)

        return redirect('adquisicion_success')


    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context['step_number'] = self.steps.index
        return context