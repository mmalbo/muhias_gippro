# notifications/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('unread/', views.unread_notifications, name='unread_notifications'),
    path('read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('read-all/', views.mark_all_read, name='mark_all_read'),
]