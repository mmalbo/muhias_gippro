from django.apps import AppConfig


class AdquisicionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Cambia el tipo de campo automático si es necesario
    name = 'adquisiciones'  # Nombre de la aplicación
    verbose_name = 'Adquisiciones'  # Nombre legible para humanos de la aplicación

    def ready(self):
        # Importa y registra las señales
        import adquisiciones.signals  # Asegúrate que este import existe

#
# class MateriaPrimaAdquisicionConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'adquisicio'
#
# class EnvaseAdquisicionConfig(AppConfig):
#     defaul_auto_field = 'django.db.models.BigAutoField'
#     name = 'envaseadquisiciones'
