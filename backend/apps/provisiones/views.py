from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from datetime import date
from .models import FondoEmergencia, AporteFondo
from .services import (
    calcular_gasto_esencial_mensual,
    calcular_meta_niveles,
    calcular_cobertura_meses,
    calcular_meses_para_meta,
    obtener_aportes_mensuales,
)


MESES_NOMBRE = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


@login_required
def ver_fondo(request):
    fondo, created = FondoEmergencia.objects.get_or_create(usuario=request.user)
    hoy = date.today()
    mes = int(request.GET.get('mes', hoy.month))
    anio = int(request.GET.get('anio', hoy.year))

    gasto_esencial = calcular_gasto_esencial_mensual(request.user, mes, anio)
    metas = calcular_meta_niveles(gasto_esencial)
    cobertura = calcular_cobertura_meses(fondo.saldo_actual, gasto_esencial)
    aporte_mes = obtener_aportes_mensuales(request.user, mes, anio)
    aportes = AporteFondo.objects.filter(fondo=fondo).order_by('-fecha')[:20]

    meses_minimo = calcular_meses_para_meta(fondo.saldo_actual, aporte_mes, metas['minimo'])
    meses_recomendado = calcular_meses_para_meta(fondo.saldo_actual, aporte_mes, metas['recomendado'])
    meses_ideal = calcular_meses_para_meta(fondo.saldo_actual, aporte_mes, metas['ideal'])

    progreso_minimo = _calcular_progreso(fondo.saldo_actual, metas['minimo'])
    progreso_recomendado = _calcular_progreso(fondo.saldo_actual, metas['recomendado'])
    progreso_ideal = _calcular_progreso(fondo.saldo_actual, metas['ideal'])

    return render(request, 'provisiones/fondo_emergencia.html', {
        'fondo': fondo,
        'gasto_esencial': gasto_esencial,
        'metas': metas,
        'cobertura': cobertura,
        'aporte_mes': aporte_mes,
        'aportes': aportes,
        'mes': mes,
        'anio': anio,
        'mes_nombre': MESES_NOMBRE[mes],
        'meses_minimo': meses_minimo,
        'meses_recomendado': meses_recomendado,
        'meses_ideal': meses_ideal,
        'progreso_minimo': progreso_minimo,
        'progreso_recomendado': progreso_recomendado,
        'progreso_ideal': progreso_ideal,
    })


def _calcular_progreso(saldo, meta):
    if meta <= 0:
        return 100
    pct = int((saldo / meta) * 100)
    return min(pct, 100)


@login_required
def registrar_aporte(request):
    fondo = get_object_or_404(FondoEmergencia, usuario=request.user)
    hoy = date.today()

    if request.method == 'POST':
        try:
            monto = Decimal(request.POST.get('monto', '0'))
            if monto <= 0:
                raise ValueError
        except (ValueError, Decimal.InvalidOperation):
            messages.error(request, 'Ingresa un monto válido mayor a 0.')
            return redirect('provisiones:fondo')

        mes = int(request.POST.get('mes', hoy.month))
        anio = int(request.POST.get('anio', hoy.year))
        fecha_str = request.POST.get('fecha', str(hoy))
        fecha = date.fromisoformat(fecha_str) if '-' in fecha_str else hoy

        AporteFondo.objects.create(
            fondo=fondo,
            monto=monto,
            fecha=fecha,
            mes=mes,
            anio=anio,
        )
        fondo.saldo_actual += monto
        fondo.save()

        messages.success(request, f'Aporte de ${monto:,.0f} registrado correctamente.')
        return redirect('provisiones:fondo')

    return redirect('provisiones:fondo')


@login_required
def ajustar_saldo(request):
    fondo = get_object_or_404(FondoEmergencia, usuario=request.user)

    if request.method == 'POST':
        try:
            nuevo_saldo = Decimal(request.POST.get('saldo_actual', '0'))
            if nuevo_saldo < 0:
                raise ValueError
        except (ValueError, Decimal.InvalidOperation):
            messages.error(request, 'Ingresa un saldo válido.')
            return redirect('provisiones:fondo')

        fondo.saldo_actual = nuevo_saldo
        fondo.save()
        messages.success(request, 'Saldo del fondo actualizado.')
        return redirect('provisiones:fondo')

    return redirect('provisiones:fondo')
