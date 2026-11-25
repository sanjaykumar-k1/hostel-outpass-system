from django.urls import path
from . import views

urlpatterns = [
    path('request/', views.request_outpass, name='request_outpass'),
    path('my-requests/', views.my_requests, name='my_requests'),
]