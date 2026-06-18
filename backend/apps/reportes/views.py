from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import date
from .services import generar_pdf_mes, exportar_csv, exportar_excel


@login_required
def reporte_pdf(request):
    hoy = date.today()
    mes = int(request.GET.get("mes", hoy.month))
    anio = int(request.GET.get("anio", hoy.year))
    return generar_pdf_mes(request.user, mes, anio)


@login_required
def exportar_csv_view(request):
    hoy = date.today()
    mes = int(request.GET.get("mes", hoy.month))
    anio = int(request.GET.get("anio", hoy.year))
    return exportar_csv(request.user, mes, anio)


@login_required
def exportar_excel_view(request):
    hoy = date.today()
    mes = int(request.GET.get("mes", hoy.month))
    anio = int(request.GET.get("anio", hoy.year))
    return exportar_excel(request.user, mes, anio)
