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
from apps.ingresos.services import verificar_alertas_prestaciones
from apps.gastos.models import Gasto, Categoria
from apps.provisiones.models import FondoEmergencia
from apps.indicadores.services import (
    calcular_indicadores_mes,
    generar_diagnostico,
    guardar_historial,
    calcular_tendencia,
    obtener_tendencia_ingresos_gastos,
    obtener_resumen_deudas,
    obtener_provisiones_activas,
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

    # Calcular todos los indicadores usando el módulo especializado
    indicadores = calcular_indicadores_mes(request.user, mes, anio)
    guardar_historial(request.user, mes, anio, indicadores)

    total_ingresos = indicadores['ingreso_neto']
    total_gastos = indicadores['gastos_totales']
    ahorro_neto = indicadores['ahorro_neto']
    tasa_ahorro = indicadores['tasa_ahorro']
    meta_tasa = request.user.meta_tasa_ahorro
    gastos_fijos = indicadores['gastos_fijos']
    presion_gastos_fijos = indicadores['presion_gastos_fijos']
    gasto_esencial = indicadores['gasto_esencial']
    cobertura_emergencia = indicadores['cobertura_emergencia']
    saldo_fondo = indicadores['saldo_fondo']
    ratio_endeudamiento = indicadores['ratio_endeudamiento']
    semaforo_endeudamiento = indicadores['semaforo_endeudamiento']
    semaforo_ahorro = indicadores['semaforo_ahorro']
    semaforo_emergencia = indicadores['semaforo_emergencia']

    # Tendencias respecto al mes anterior
    tendencias = {}
    for campo in ['tasa_ahorro', 'ratio_endeudamiento', 'cobertura_emergencia', 'presion_gastos_fijos']:
        tendencias[campo] = calcular_tendencia(request.user, campo, mes, anio)

    gastos_por_categoria = (
        Gasto.objects.filter(usuario=request.user, mes=mes, anio=anio)
        .values('categoria__nombre', 'categoria__color')
        .annotate(total=Sum('monto'))
        .order_by('-total')
    )

    ultimos_gastos = Gasto.objects.filter(
        usuario=request.user
    ).select_related('categoria', 'rubro').order_by('-fecha', '-creado_en')[:10]

    # Diagnóstico automático
    diagnostico = generar_diagnostico(indicadores)

    # Datos para gráfico de línea (RF-112)
    tendencia_ig = obtener_tendencia_ingresos_gastos(request.user)

    # Resumen de deudas (RF-115)
    resumen_deudas = obtener_resumen_deudas(request.user)

    # Provisiones activas (RF-116)
    provisiones_activas = obtener_provisiones_activas(request.user)

    # Alertas de prestaciones próximas
    alertas_prestaciones = verificar_alertas_prestaciones(request.user)

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
        'ratio_endeudamiento': ratio_endeudamiento,
        'semaforo_endeudamiento': semaforo_endeudamiento,
        'semaforo_ahorro': semaforo_ahorro,
        'semaforo_emergencia': semaforo_emergencia,
        'diagnostico': diagnostico,
        'tendencias': tendencias,
        'alertas_prestaciones': alertas_prestaciones,
        'indicadores': indicadores,
        'tendencia_ingresos_gastos': tendencia_ig,
        'tendencia_ig_json': tendencia_ig,
        'resumen_deudas': resumen_deudas,
        'provisiones_activas': provisiones_activas,
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
