from django.urls import path
from . import views

app_name = "proyecciones"

urlpatterns = [
    path("", views.ver_proyecciones, name="ver"),
    path("configurar/", views.configurar_escenarios, name="configurar"),
    path("ingresos/", views.listar_proyecciones_ingreso, name="ingresos"),
    path(
        "ingresos/registrar/",
        views.registrar_proyeccion_ingreso,
        name="registrar_ingreso",
    ),
    path(
        "ingresos/<int:pk>/editar/",
        views.editar_proyeccion_ingreso,
        name="editar_ingreso",
    ),
    path(
        "ingresos/<int:pk>/eliminar/",
        views.eliminar_proyeccion_ingreso,
        name="eliminar_ingreso",
    ),
    path("gastos/", views.listar_proyecciones_gasto, name="gastos"),
    path("gastos/registrar/", views.registrar_proyeccion_gasto, name="registrar_gasto"),
    path("gastos/<int:pk>/editar/", views.editar_proyeccion_gasto, name="editar_gasto"),
    path(
        "gastos/<int:pk>/eliminar/",
        views.eliminar_proyeccion_gasto,
        name="eliminar_gasto",
    ),
    path("api/", views.api_resultados, name="api"),
]
