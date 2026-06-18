from django.urls import path
from . import views

app_name = 'provisiones'

urlpatterns = [
    # Fondo de emergencia
    path('fondo/', views.ver_fondo, name='fondo'),
    path('fondo/aporte/', views.registrar_aporte, name='aporte'),
    path('fondo/ajustar/', views.ajustar_saldo, name='ajustar_saldo'),

    # Provisiones para pagos futuros
    path('', views.listar_provisiones, name='lista'),
    path('registrar/', views.registrar_provision, name='registrar'),
    path('<int:provision_id>/', views.detalle_provision, name='detalle'),
    path('<int:provision_id>/editar/', views.editar_provision, name='editar'),
    path('<int:provision_id>/eliminar/', views.eliminar_provision, name='eliminar'),
    path('<int:provision_id>/aporte/', views.registrar_aporte_provision, name='aporte_provision'),
]