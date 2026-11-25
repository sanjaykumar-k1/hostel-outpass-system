from django.urls import path
from . import views

urlpatterns = [
    path('request/', views.request_outpass, name='request_outpass'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('warden/', views.warden_requests, name='warden_requests'),
    path('update/<int:pk>/', views.update_status, name='update_status'),
    path('my-id/', views.my_id, name='my_id'),
    path('my-qr/', views.my_qr, name='my_qr'),
    path('gate/', views.gate_scan, name='gate_scan'),
    path('logs/', views.movement_logs, name='movement_logs'),
]