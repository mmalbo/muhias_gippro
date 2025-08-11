from django.urls import path
from .views import recepcion_materia_prima

urlpatterns = [
     path('recepcion/mp/<int:adq_id>/', recepcion_materia_prima , name='recepcion_mp'),
]