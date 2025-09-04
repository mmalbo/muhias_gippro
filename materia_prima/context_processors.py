# materia_prima/context_processors.py
from .choices import ESTADOS, Tipo_mat_prima

def choices_context(request):
    return {
        'available_states': ESTADOS,
        'available_tipos': Tipo_mat_prima,
    }