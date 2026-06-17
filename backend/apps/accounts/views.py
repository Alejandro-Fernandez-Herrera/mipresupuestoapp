from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from datetime import date
from .forms import RegistroForm, PerfilForm, ConfiguracionFiscalForm
from .models import UserProfile, ConfiguracionFiscal
from apps.ingresos.models import RegistroNomina, OtroIngreso
from apps.gastos.models import Gasto, Categoria
from apps.provisiones.models import FondoEmergencia
from apps.provisiones.services import (
    calcular_ingresos_totales,
    calcular_gastos_totales,
    calcular_ahorro_neto,
    calcular_tasa_ahorro,
    calcular_gasto_esencial_mensual,
    calcular_cobertura_meses,
    calcular_presion_gastos_fijos,
    generar_diagnostico,
    calcular_gastos_fijos,
)


MESES_NOMBRE = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


@login_required
def cerrar_sesion(request):
    if request.method == 'POST':
        logout(request)
        return render(request, 'accounts/sesion_cerrada.html')
    return render(request, 'accounts/confirmar_cierre.html')


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = 'apps.accounts.backends.EmailOrUsernameBackend'
            login(request, user)
            messages.success(request, '¡Bienvenido! Tu cuenta ha sido creada.')
            return redirect('dashboard')
    else:
        form = RegistroForm()
    return render(request, 'accounts/registro.html', {'form': form})


@login_required
def dashboard(request):
    hoy = date.today()
    mes = int(request.GET.get('mes', hoy.month))
    anio = int(request.GET.get('anio', hoy.year))

    total_ingresos = calcular_ingresos_totales(request.user, mes, anio)
    total_gastos = calcular_gastos_totales(request.user, mes, anio)
    ahorro_neto = calcular_ahorro_neto(request.user, mes, anio)
    tasa_ahorro = calcular_tasa_ahorro(request.user, mes, anio)
    meta_tasa = request.user.meta_tasa_ahorro

    gastos_fijos = calcular_gastos_fijos(request.user, mes, anio)
    presion_gastos_fijos = calcular_presion_gastos_fijos(request.user, mes, anio)

    gastos_por_categoria = (
        Gasto.objects.filter(usuario=request.user, mes=mes, anio=anio)
        .values('categoria__nombre', 'categoria__color')
        .annotate(total=Sum('monto'))
        .order_by('-total')
    )

    ultimos_gastos = Gasto.objects.filter(
        usuario=request.user
    ).select_related('categoria', 'rubro').order_by('-fecha', '-creado_en')[:10]

    gasto_esencial = calcular_gasto_esencial_mensual(request.user, mes, anio)

    try:
        fondo = FondoEmergencia.objects.get(usuario=request.user)
        cobertura_emergencia = calcular_cobertura_meses(fondo.saldo_actual, gasto_esencial)
        saldo_fondo = fondo.saldo_actual
    except FondoEmergencia.DoesNotExist:
        cobertura_emergencia = Decimal('0')
        saldo_fondo = Decimal('0')

    indicadores = {
        'tasa_ahorro': tasa_ahorro,
        'presion_gastos_fijos': presion_gastos_fijos,
        'cobertura_emergencia': cobertura_emergencia,
    }
    diagnostico = generar_diagnostico(indicadores)

    return render(request, 'dashboard.html', {
        'mes': mes,
        'anio': anio,
        'mes_nombre': MESES_NOMBRE[mes],
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'ahorro_neto': ahorro_neto,
        'tasa_ahorro': tasa_ahorro,
        'meta_tasa': meta_tasa,
        'gastos_fijos': gastos_fijos,
        'presion_gastos_fijos': presion_gastos_fijos,
        'gastos_por_categoria': list(gastos_por_categoria),
        'gastos_por_categoria_json': list(gastos_por_categoria),
        'ultimos_gastos': ultimos_gastos,
        'gasto_esencial': gasto_esencial,
        'cobertura_emergencia': cobertura_emergencia,
        'saldo_fondo': saldo_fondo,
        'diagnostico': diagnostico,
    })


@login_required
def perfil(request):
    return render(request, 'accounts/perfil.html', {'user': request.user})


@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('accounts:perfil')
    else:
        form = PerfilForm(instance=request.user)
    return render(request, 'accounts/editar_perfil.html', {'form': form})


@login_required
def configuracion_fiscal(request):
    configs = ConfiguracionFiscal.objects.all().order_by('-anio')
    if request.method == 'POST':
        form = ConfiguracionFiscalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración fiscal creada.')
            return redirect('accounts:configuracion_fiscal')
    else:
        form = ConfiguracionFiscalForm()
    return render(request, 'accounts/configuracion_fiscal.html', {
        'form': form,
        'configs': configs,
    })