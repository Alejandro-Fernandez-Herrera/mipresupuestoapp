from django.urls import path
from . import views

app_name = 'gastos'

urlpatterns = [
    path('', views.listar_gastos, name='lista'),
    path('registrar/', views.registrar_gasto, name='registrar'),
    path('<int:gasto_id>/editar/', views.editar_gasto, name='editar'),
    path('<int:gasto_id>/eliminar/', views.eliminar_gasto, name='eliminar'),
    path('<int:gasto_id>/duplicar/', views.duplicar_gasto, name='duplicar'),
    path('categorias/', views.gestionar_categorias, name='categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/ocultar/', views.ocultar_categoria, name='ocultar_categoria'),
    path('categorias/<int:categoria_id>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),
    path('rubros/crear/', views.crear_rubro, name='crear_rubro'),
    path('rubros/<int:rubro_id>/editar/', views.editar_rubro, name='editar_rubro'),
    path('rubros/<int:rubro_id>/ocultar/', views.ocultar_rubro, name='ocultar_rubro'),
    path('rubros/<int:rubro_id>/eliminar/', views.eliminar_rubro, name='eliminar_rubro'),
    path('rubros/cargar/', views.cargar_rubros, name='cargar_rubros'),
]