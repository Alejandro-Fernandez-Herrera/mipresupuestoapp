from django.urls import path
from . import views

app_name = 'provisiones'

urlpatterns = [
    path('fondo/', views.ver_fondo, name='fondo'),
    path('fondo/aporte/', views.registrar_aporte, name='aporte'),
    path('fondo/ajustar/', views.ajustar_saldo, name='ajustar_saldo'),
]