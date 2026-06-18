from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services import (
    calcular_indicadores_mes,
    calcular_tendencia,
    guardar_historial,
    obtener_historial,
)
from datetime import date

MESES_NOMBRE = [
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


@login_required
def historial_indicadores(request):
    mes = int(request.GET.get("mes", date.today().month))
    anio = int(request.GET.get("anio", date.today().year))

    indicadores = calcular_indicadores_mes(request.user, mes, anio)
    guardar_historial(request.user, mes, anio, indicadores)

    historial = obtener_historial(request.user, meses=12)

    tendencias = {}
    for campo in [
        "tasa_ahorro",
        "ratio_endeudamiento",
        "cobertura_emergencia",
        "presion_gastos_fijos",
    ]:
        tendencias[campo] = calcular_tendencia(request.user, campo, mes, anio)

    return render(
        request,
        "indicadores/historial.html",
        {
            "mes": mes,
            "anio": anio,
            "mes_nombre": MESES_NOMBRE[mes],
            "indicadores": indicadores,
            "historial": historial,
            "tendencias": tendencias,
        },
    )
