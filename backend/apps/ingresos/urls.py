from django.urls import path
from . import views

app_name = 'ingresos'

urlpatterns = [
    path('', views.listar_ingresos, name='lista'),
    path('nomina/registrar/', views.registrar_nomina, name='registrar_nomina'),
    path('nomina/<int:nomina_id>/', views.detalle_nomina, name='detalle_nomina'),
    path('nomina/<int:nomina_id>/editar/', views.editar_nomina, name='editar_nomina'),
    path('nomina/<int:nomina_id>/eliminar/', views.eliminar_nomina, name='eliminar_nomina'),
    path('otros/registrar/', views.registrar_otro_ingreso, name='registrar_otro_ingreso'),
    path('otros/<int:ingreso_id>/editar/', views.editar_otro_ingreso, name='editar_otro_ingreso'),
    path('otros/<int:ingreso_id>/eliminar/', views.eliminar_otro_ingreso, name='eliminar_otro_ingreso'),
    path('prestaciones/', views.prestaciones_proyectadas, name='prestaciones'),
    path('prestaciones/<int:pk>/marcar-pagada/', views.marcar_prestacion_pagada, name='marcar_pagada'),
]
