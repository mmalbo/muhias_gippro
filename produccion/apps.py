from django.apps import AppConfig

class ProduccionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'produccion'
    verbose_name = "Produccion"
    
    def ready(self):
        # Importa y registra las señales
        import produccion.signals  # Asegúrate que este import existe