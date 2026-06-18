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


# ============================================================
# SERVICIOS PROVISIONES (RF-070 a RF-078)
# ============================================================

def calcular_meses_restantes(fecha_pago, referencia=None):
    """
    Calcula los meses calendario entre la fecha actual y la fecha de pago.
    Si ya pasó la fecha, retorna 0.
    """
    from dateutil.relativedelta import relativedelta
    hoy = referencia or date.today()
    if fecha_pago <= hoy:
        return 0
    # Si el pago es en el mismo mes, retorna 1 (al menos un mes parcial)
    if fecha_pago.year == hoy.year and fecha_pago.month == hoy.month:
        return 1 if fecha_pago.day > hoy.day else 0
    diff = relativedelta(fecha_pago, hoy)
    meses = diff.years * 12 + diff.months
    if diff.days > 0:
        meses += 1
    return meses


def calcular_ahorro_mensual_recomendado(monto_total, ahorro_acumulado, meses_restantes):
    """
    Calcula el ahorro mensual recomendado para alcanzar la meta.

    Fórmula: Ahorro mensual = (Monto total - Acumulado) / Meses restantes

    Args:
        monto_total: monto total estimado de la provisión (Decimal)
        ahorro_acumulado: ahorro acumulado a la fecha (Decimal)
        meses_restantes: meses disponibles para ahorrar (int)

    Returns:
        ahorro mensual recomendado en COP (Decimal)
    """
    if meses_restantes <= 0:
        return Decimal('0')
    restante = monto_total - ahorro_acumulado
    if restante <= 0:
        return Decimal('0')
    return Q_DEC(restante / Decimal(str(meses_restantes)))


def calcular_ahorro_maximo_alcanzable(ahorro_mensual_disponible, meses_restantes):
    """
    Calcula el máximo ahorro alcanzable al ritmo actual.

    Fórmula: Máximo = Ahorro mensual disponible × Meses restantes
    """
    if meses_restantes <= 0:
        return Decimal('0')
    return Q_DEC(ahorro_mensual_disponible * Decimal(str(meses_restantes)))


def calcular_progreso(ahorro_acumulado, monto_total):
    """
    Calcula el porcentaje de progreso de la provisión.

    Fórmula: Progreso = (Acumulado / Monto total) × 100
    """
    if monto_total <= 0:
        return Decimal('100')
    pct = (ahorro_acumulado / monto_total) * Decimal('100')
    return min(pct, Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def evaluar_alcanzabilidad(ahorro_acumulado, ahorro_maximo, monto_total):
    """
    Evalúa si la meta es alcanzable al ritmo actual.

    Args:
        ahorro_acumulado: ahorro acumulado actual (Decimal)
        ahorro_maximo: ahorro máximo alcanzable (Decimal)
        monto_total: monto total de la provisión (Decimal)

    Returns:
        (alcanza: bool, deficit: Decimal)
    """
    total_posible = ahorro_acumulado + ahorro_maximo
    if total_posible >= monto_total:
        return True, Decimal('0')
    return False, Q_DEC(monto_total - total_posible)


def chequear_recordatorio(fecha_pago, progreso):
    """
    Determina si debe mostrarse un recordatorio visual.

    Recordatorio: faltan 2 meses o menos Y progreso < 80%
    """
    from datetime import date as date_type
    hoy = date_type.today()
    from dateutil.relativedelta import relativedelta
    dos_meses = hoy + relativedelta(months=2)
    if fecha_pago <= dos_meses and progreso < 80:
        return True
    return False


# ============================================================
# CATÁLOGO DE PROVISIONES SUGERIDAS (RF-078)
# ============================================================

PROVISIONES_SUGERIDAS = [
    {
        "concepto": "SOAT vehículo / moto",
        "monto_total": Decimal("250000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 1,
        "anio_ejemplo": 2026,
        "categoria": "Transporte",
    },
    {
        "concepto": "Revisión técnico-mecánica + gases",
        "monto_total": Decimal("150000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 1,
        "anio_ejemplo": 2026,
        "categoria": "Transporte",
    },
    {
        "concepto": "Mantenimiento preventivo vehículo",
        "monto_total": Decimal("300000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 6,
        "anio_ejemplo": 2026,
        "categoria": "Transporte",
    },
    {
        "concepto": "Seguro todo riesgo vehículo",
        "monto_total": Decimal("1200000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 1,
        "anio_ejemplo": 2026,
        "categoria": "Transporte",
    },
    {
        "concepto": "Matrícula educación superior",
        "monto_total": Decimal("3000000"),
        "fecha_pago_dia": 15, "fecha_pago_mes": 1,
        "anio_ejemplo": 2026,
        "categoria": "Educación Propia",
    },
    {
        "concepto": "Libros y materiales de estudio",
        "monto_total": Decimal("400000"),
        "fecha_pago_dia": 15, "fecha_pago_mes": 1,
        "anio_ejemplo": 2026,
        "categoria": "Educación Propia",
    },
    {
        "concepto": "Matrícula jardín / colegio (dependiente)",
        "monto_total": Decimal("1500000"),
        "fecha_pago_dia": 15, "fecha_pago_mes": 1,
        "anio_ejemplo": 2026,
        "categoria": "Educación Familia",
    },
    {
        "concepto": "Útiles y libros escolares",
        "monto_total": Decimal("300000"),
        "fecha_pago_dia": 15, "fecha_pago_mes": 1,
        "anio_ejemplo": 2026,
        "categoria": "Educación Familia",
    },
    {
        "concepto": "Uniformes y calzado escolar",
        "monto_total": Decimal("350000"),
        "fecha_pago_dia": 15, "fecha_pago_mes": 1,
        "anio_ejemplo": 2026,
        "categoria": "Educación Familia",
    },
    {
        "concepto": "Regalos navidad y fin de año",
        "monto_total": Decimal("500000"),
        "fecha_pago_dia": 15, "fecha_pago_mes": 12,
        "anio_ejemplo": 2026,
        "categoria": "Otros",
    },
    {
        "concepto": "Cumpleaños (persona relevante 1)",
        "monto_total": Decimal("150000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 6,
        "anio_ejemplo": 2026,
        "categoria": "Familia",
    },
    {
        "concepto": "Cumpleaños (persona relevante 2)",
        "monto_total": Decimal("150000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 9,
        "anio_ejemplo": 2026,
        "categoria": "Familia",
    },
    {
        "concepto": "Vacaciones familiares",
        "monto_total": Decimal("2000000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 7,
        "anio_ejemplo": 2026,
        "categoria": "Ocio",
    },
    {
        "concepto": "Vacunas anuales mascotas",
        "monto_total": Decimal("150000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 3,
        "anio_ejemplo": 2026,
        "categoria": "Mascotas",
    },
    {
        "concepto": "Seguro de vida / accidentes personales",
        "monto_total": Decimal("800000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 1,
        "anio_ejemplo": 2026,
        "categoria": "Salud",
    },
    {
        "concepto": "Impuesto predial",
        "monto_total": Decimal("500000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 5,
        "anio_ejemplo": 2026,
        "categoria": "Vivienda",
    },
    {
        "concepto": "Renovación cámara de comercio",
        "monto_total": Decimal("100000"),
        "fecha_pago_dia": 1, "fecha_pago_mes": 3,
        "anio_ejemplo": 2026,
        "categoria": "Otros",
    },
]


def crear_provisiones_sugeridas(usuario):
    """
    Crea las 17 provisiones sugeridas por defecto para un usuario.
    Se ejecuta al crear el perfil o cuando el usuario las solicite.
    """
    from .models import Provision
    from datetime import date as date_type
    hoy = date_type.today()
    count = 0
    for data in PROVISIONES_SUGERIDAS:
        try:
            anio = hoy.year
            fecha_pago = date_type(anio, data["fecha_pago_mes"], min(data["fecha_pago_dia"], 28))
            if fecha_pago < hoy:
                fecha_pago = date_type(anio + 1, data["fecha_pago_mes"], min(data["fecha_pago_dia"], 28))
            _, created = Provision.objects.get_or_create(
                usuario=usuario,
                concepto=data["concepto"],
                defaults={
                    "monto_total": data["monto_total"],
                    "fecha_pago": fecha_pago,
                    "ahorro_acumulado": Decimal('0'),
                    "es_sugerida": True,
                    "activa": True,
                },
            )
            if created:
                count += 1
        except Exception:
            pass
    return count


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
