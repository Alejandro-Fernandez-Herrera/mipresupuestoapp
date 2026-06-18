from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from datetime import date
from .models import FondoEmergencia, AporteFondo, Provision, AporteProvision
from .forms import ProvisionForm, AporteProvisionForm
from .services import (
    calcular_gasto_esencial_mensual,
    calcular_meta_niveles,
    calcular_cobertura_meses,
    calcular_meses_para_meta,
    obtener_aportes_mensuales,
    calcular_meses_restantes,
    calcular_ahorro_mensual_recomendado,
    calcular_ahorro_maximo_alcanzable,
    calcular_progreso,
    evaluar_alcanzabilidad,
    chequear_recordatorio,
    crear_provisiones_sugeridas,
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


# ============================================================
# VISTAS PROVISIONES (RF-070 a RF-078)
# ============================================================

@login_required
def listar_provisiones(request):
    crear_provisiones_sugeridas(request.user)

    provisiones = Provision.objects.filter(usuario=request.user, activa=True).order_by('fecha_pago')

    resultados = []
    total_faltante = Decimal('0')

    for p in provisiones:
        meses_rest = calcular_meses_restantes(p.fecha_pago)
        rec = calcular_ahorro_mensual_recomendado(p.monto_total, p.ahorro_acumulado, meses_rest)
        maximo = calcular_ahorro_maximo_alcanzable(p.ahorro_mensual_disponible, meses_rest)
        progreso = calcular_progreso(p.ahorro_acumulado, p.monto_total)
        alcanza, deficit = evaluar_alcanzabilidad(p.ahorro_acumulado, maximo, p.monto_total)
        alerta = chequear_recordatorio(p.fecha_pago, progreso)

        restante = p.monto_total - p.ahorro_acumulado
        if restante > 0:
            total_faltante += restante

        resultados.append({
            'provision': p,
            'meses_restantes': meses_rest,
            'ahorro_recomendado': rec,
            'ahorro_maximo': maximo,
            'progreso': int(progreso),
            'alcanza': alcanza,
            'deficit': deficit,
            'alerta': alerta,
        })

    return render(request, 'provisiones/lista.html', {
        'resultados': resultados,
        'total_faltante': total_faltante,
    })


@login_required
def registrar_provision(request):
    if request.method == 'POST':
        form = ProvisionForm(request.POST)
        if form.is_valid():
            provision = form.save(commit=False)
            provision.usuario = request.user
            provision.save()
            messages.success(request, f'Provisión "{provision.concepto}" creada.')
            return redirect('provisiones:lista')
    else:
        form = ProvisionForm(initial={'fecha_pago': date.today()})

    return render(request, 'provisiones/form.html', {
        'form': form,
        'titulo': 'Nueva Provisión',
    })


@login_required
def detalle_provision(request, provision_id):
    provision = get_object_or_404(Provision, id=provision_id, usuario=request.user)
    aportes = provision.aportes.all().order_by('-fecha')

    meses_rest = calcular_meses_restantes(provision.fecha_pago)
    rec = calcular_ahorro_mensual_recomendado(provision.monto_total, provision.ahorro_acumulado, meses_rest)
    maximo = calcular_ahorro_maximo_alcanzable(provision.ahorro_mensual_disponible, meses_rest)
    progreso = calcular_progreso(provision.ahorro_acumulado, provision.monto_total)
    alcanza, deficit = evaluar_alcanzabilidad(provision.ahorro_acumulado, maximo, provision.monto_total)
    alerta = chequear_recordatorio(provision.fecha_pago, progreso)

    aporte_form = AporteProvisionForm()

    faltante = max(provision.monto_total - provision.ahorro_acumulado, Decimal('0'))

    return render(request, 'provisiones/detalle.html', {
        'provision': provision,
        'aportes': aportes,
        'meses_restantes': meses_rest,
        'ahorro_recomendado': rec,
        'ahorro_maximo': maximo,
        'progreso': int(progreso),
        'alcanza': alcanza,
        'deficit': deficit,
        'alerta': alerta,
        'faltante': faltante,
        'aporte_form': aporte_form,
    })


@login_required
def editar_provision(request, provision_id):
    provision = get_object_or_404(Provision, id=provision_id, usuario=request.user)

    if request.method == 'POST':
        form = ProvisionForm(request.POST, instance=provision)
        if form.is_valid():
            form.save()
            messages.success(request, 'Provisión actualizada.')
            return redirect('provisiones:detalle', provision_id=provision.id)
    else:
        form = ProvisionForm(instance=provision)

    return render(request, 'provisiones/form.html', {
        'form': form,
        'titulo': 'Editar Provisión',
    })


@login_required
def eliminar_provision(request, provision_id):
    provision = get_object_or_404(Provision, id=provision_id, usuario=request.user)
    provision.delete()
    messages.success(request, 'Provisión eliminada.')
    return redirect('provisiones:lista')


@login_required
def registrar_aporte_provision(request, provision_id):
    provision = get_object_or_404(Provision, id=provision_id, usuario=request.user)

    if request.method == 'POST':
        form = AporteProvisionForm(request.POST)
        if form.is_valid():
            monto = form.cleaned_data['monto']
            fecha = form.cleaned_data['fecha']
            AporteProvision.objects.create(
                provision=provision,
                monto=monto,
                fecha=fecha,
            )
            provision.ahorro_acumulado += monto
            provision.save()
            messages.success(request, f'Aporte de ${monto:,.0f} registrado.')
            return redirect('provisiones:detalle', provision_id=provision.id)
    return redirect('provisiones:detalle', provision_id=provision.id)
