from django.urls import path

from bases import views

app_name = "bases"
urlpatterns = [
    path(
        "aprobar/<str:instancia>/<str:pk>",
        views.aprobar,
        name="aprobar",
    ),
]
