CHOICE_ESTADO_PROD = (
    ('1', 'Planificada'),
    ('2', 'Iniciando mezcla'),
    ('3', 'En proceso: Agitado'),
    ('4', 'En proceso: Validación'),
    ('5', 'Concluida'),
    ('6', 'Cancelada')
)

CHOICE_ESTADO_SOL = (
    ('1', 'Solicitada'),
    ('2', 'Aprobada'),
    ('3', 'Utilizada'),
    ('4', 'Devuelta'),
    ('5', 'Cancelada')
)

TIPOS_PARAMETRO = [
        ('fisico', 'Físico'),
        ('quimico', 'Químico'),
        ('microbiologico', 'Microbiológico'),
        ('organoleptico', 'Organoléptico'),
    ]

ESTADOS_PRUEBA = [
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('rechazada', 'Rechazada'),
        ('aprobada', 'Aprobada'),
    ]