from django.urls import path
from . import views

app_name = "deudas"

urlpatterns = [
    # Créditos de consumo
    path("", views.listar_creditos, name="lista"),
    path("registrar/", views.registrar_credito, name="registrar"),
    path("<int:credito_id>/", views.detalle_credito, name="detalle"),
    path("<int:credito_id>/editar/", views.editar_credito, name="editar"),
    path("<int:credito_id>/eliminar/", views.eliminar_credito, name="eliminar"),
    path("<int:credito_id>/pagar/", views.registrar_pago, name="pagar"),
    path("<int:credito_id>/desactivar/", views.desactivar_credito, name="desactivar"),
    # Tarjetas de crédito
    path("tarjetas/", views.listar_tarjetas, name="lista_tarjetas"),
    path("tarjetas/registrar/", views.registrar_tarjeta, name="registrar_tarjeta"),
    path("tarjetas/<int:tarjeta_id>/", views.detalle_tarjeta, name="detalle_tarjeta"),
    path(
        "tarjetas/<int:tarjeta_id>/editar/", views.editar_tarjeta, name="editar_tarjeta"
    ),
    path(
        "tarjetas/<int:tarjeta_id>/eliminar/",
        views.eliminar_tarjeta,
        name="eliminar_tarjeta",
    ),
    path(
        "tarjetas/<int:tarjeta_id>/toggle/", views.toggle_tarjeta, name="toggle_tarjeta"
    ),
    path(
        "tarjetas/<int:tarjeta_id>/compra/",
        views.registrar_compra_tc,
        name="registrar_compra",
    ),
    path(
        "tarjetas/<int:tarjeta_id>/pago/", views.registrar_pago_tc, name="pago_tarjeta"
    ),
]
