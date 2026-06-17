from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db.models import Sum, Q
from apps.gastos.models import Categoria, Gasto
from apps.ingresos.models import RegistroNomina, OtroIngreso


Q_DEC = lambda x: x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def calcular_gasto_esencial_mensual(usuario, mes=None, anio=None):
    hoy = date.today()
    mes = mes or hoy.month
    anio = anio or hoy.year

    categorias_esenciales = Categoria.objects.filter(
        es_esencial=True, visible=True
    )

    total = Gasto.objects.filter(
        usuario=usuario,
        mes=mes,
        anio=anio,
        categoria__in=categorias_esenciales,
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

    return total


def calcular_ingresos_totales(usuario, mes, anio):
    total_nomina = RegistroNomina.objects.filter(
        usuario=usuario, mes=mes, anio=anio
    ).aggregate(s=Sum('neto_con_auxilio'))['s'] or Decimal('0')

    total_otros = OtroIngreso.objects.filter(
        usuario=usuario, mes=mes, anio=anio
    ).aggregate(s=Sum('monto'))['s'] or Decimal('0')

    return total_nomina + total_otros


def calcular_gastos_totales(usuario, mes, anio):
    return Gasto.objects.filter(
        usuario=usuario, mes=mes, anio=anio
    ).aggregate(s=Sum('monto'))['s'] or Decimal('0')


def calcular_gastos_fijos(usuario, mes, anio):
    return Gasto.objects.filter(
        usuario=usuario, mes=mes, anio=anio, tipo='fijo'
    ).aggregate(s=Sum('monto'))['s'] or Decimal('0')


def calcular_ahorro_neto(usuario, mes, anio):
    ingresos = calcular_ingresos_totales(usuario, mes, anio)
    gastos = calcular_gastos_totales(usuario, mes, anio)
    return ingresos - gastos


def calcular_tasa_ahorro(usuario, mes, anio):
    ingresos = calcular_ingresos_totales(usuario, mes, anio)
    if ingresos <= Decimal('0'):
        return Decimal('0')
    ahorro = calcular_ahorro_neto(usuario, mes, anio)
    return Q_DEC((ahorro / ingresos) * 100)


def calcular_cobertura_meses(saldo_fondo, gasto_esencial_mensual):
    if gasto_esencial_mensual <= Decimal('0'):
        return Decimal('0')
    return Q_DEC(saldo_fondo / gasto_esencial_mensual)


def calcular_meta_niveles(gasto_esencial_mensual):
    return {
        'minimo': gasto_esencial_mensual * 1,
        'recomendado': gasto_esencial_mensual * 3,
        'ideal': gasto_esencial_mensual * 6,
    }


def calcular_meses_para_meta(saldo_actual, aporte_mensual, meta):
    if aporte_mensual <= Decimal('0'):
        return None
    restante = meta - saldo_actual
    if restante <= Decimal('0'):
        return 0
    meses = (restante / aporte_mensual).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(meses)


def obtener_aportes_mensuales(usuario, mes, anio):
    from .models import FondoEmergencia, AporteFondo
    try:
        fondo = FondoEmergencia.objects.get(usuario=usuario)
        total = AporteFondo.objects.filter(
            fondo=fondo, mes=mes, anio=anio
        ).aggregate(s=Sum('monto'))['s'] or Decimal('0')
        return total
    except FondoEmergencia.DoesNotExist:
        return Decimal('0')


def calcular_presion_gastos_fijos(usuario, mes, anio):
    ingresos = calcular_ingresos_totales(usuario, mes, anio)
    if ingresos <= Decimal('0'):
        return Decimal('0')
    fijos = calcular_gastos_fijos(usuario, mes, anio)
    return Q_DEC((fijos / ingresos) * 100)


def generar_diagnostico(indicadores):
    criticos = []
    if indicadores.get('tasa_ahorro', 100) < 10:
        criticos.append(f"Tasa de ahorro crítica ({indicadores['tasa_ahorro']:.0f}%). Revisa gastos variables.")
    elif indicadores.get('tasa_ahorro', 100) < 20:
        criticos.append(f"Tasa de ahorro baja ({indicadores['tasa_ahorro']:.0f}%). Intenta reducir gastos no esenciales.")

    if indicadores.get('presion_gastos_fijos', 0) > 50:
        criticos.append(f"Presión de gastos fijos alta ({indicadores['presion_gastos_fijos']:.0f}%). Ideal < 50%.")

    if indicadores.get('cobertura_emergencia', 99) < 1:
        criticos.append(f"Fondo de emergencia crítico. Cobertura de {indicadores['cobertura_emergencia']:.1f} meses. Prioriza este fondo.")

    if not criticos:
        return "Salud financiera estable. Sigue así."

    return " | ".join(criticos[:2])
