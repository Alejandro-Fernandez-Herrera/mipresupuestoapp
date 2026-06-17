from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta


Q = lambda x: x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def calcular_tasa_mensual(tasa_ea):
    """
    Convierte tasa efectiva anual a tasa efectiva mensual.

    Fórmula: i_mensual = (1 + EA)^(1/12) - 1
    """
    if tasa_ea <= 0:
        return Decimal('0')
    uno = Decimal('1')
    i_mensual = (uno + tasa_ea) ** (uno / Decimal('12')) - uno
    return i_mensual.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)


def calcular_cuota_mensual(capital, tasa_ea, plazo_meses):
    """
    Calcula la cuota mensual usando el sistema de amortización French.

    Fórmula: Cuota = (P * i) / (1 - (1+i)^(-n))

    donde:
        P = capital prestado
        i = tasa mensual (decimal)
        n = número de cuotas (meses)

    Args:
        capital: monto del préstamo (Decimal)
        tasa_ea: tasa efectiva anual como decimal (ej: 0.25 para 25%)
        plazo_meses: número de meses

    Returns:
        cuota mensual fija (Decimal)
    """
    i = calcular_tasa_mensual(tasa_ea)
    if i <= 0:
        return Q(capital / Decimal(str(plazo_meses)))

    uno = Decimal('1')
    denominador = uno - (uno + i) ** (-Decimal(str(plazo_meses)))
    cuota = Q(capital * i / denominador)
    return cuota


def generar_tabla_amortizacion(credito):
    """
    Genera la tabla de amortización completa para un crédito.

    Args:
        credito: instancia de Credito

    Returns:
        lista de dicts con cada cuota
    """
    capital = credito.capital
    tasa_ea = credito.tasa_ea
    plazo = credito.plazo_meses
    fecha_base = credito.fecha_desembolso

    i = calcular_tasa_mensual(tasa_ea)
    cuota = calcular_cuota_mensual(capital, tasa_ea, plazo)

    tabla = []
    saldo = capital

    for n in range(1, plazo + 1):
        interes = Q(saldo * i)
        capital_amortizado = Q(cuota - interes)
        if capital_amortizado > saldo:
            capital_amortizado = saldo
            cuota = Q(saldo + interes)
        saldo -= capital_amortizado
        if saldo < Decimal('0'):
            saldo = Decimal('0')

        fecha_pago = fecha_base + relativedelta(months=n)

        tabla.append({
            'numero': n,
            'fecha_pago': fecha_pago,
            'cuota_total': cuota,
            'interes': interes,
            'capital_amortizado': capital_amortizado,
            'saldo_capital': saldo,
        })

    return tabla


def calcular_interes_total(capital, tasa_ea, plazo_meses):
    """
    Calcula el interés total pagado en la vida del crédito.

    Fórmula: Interés total = (Cuota mensual * n) - Capital
    """
    cuota = calcular_cuota_mensual(capital, tasa_ea, plazo_meses)
    return Q(cuota * plazo_meses - capital)


# ============================================================
# SERVICIOS TARJETAS DE CRÉDITO
# ============================================================

def calcular_cuota_minima(saldo_actual, cuota_minima_pct):
    """
    Calcula la cuota mínima a pagar en una tarjeta de crédito.

    Fórmula: Cuota mínima = max(saldo_actual × %, mínimo definido)
    Por defecto: 5% del saldo (Circular SFC)

    Args:
        saldo_actual: saldo actual de la tarjeta (Decimal)
        cuota_minima_pct: porcentaje como decimal (ej: 0.05 para 5%)

    Returns:
        cuota mínima en COP (Decimal)
    """
    if saldo_actual <= 0:
        return Decimal('0')
    return Q(saldo_actual * cuota_minima_pct)


def calcular_intereses_tc(saldo_actual, tasa_mensual):
    """
    Calcula los intereses mensuales sobre saldo no pagado.

    Fórmula: Intereses = Saldo actual × Tasa mensual

    Args:
        saldo_actual: saldo actual de la tarjeta (Decimal)
        tasa_mensual: tasa mensual como decimal (ej: 0.0234 para 2.34%)

    Returns:
        intereses del mes en COP (Decimal)
    """
    if saldo_actual <= 0 or tasa_mensual <= 0:
        return Decimal('0')
    return Q(saldo_actual * tasa_mensual)


def obtener_semaforo_uso(porcentaje_uso):
    """
    Determina el semáforo de uso de una tarjeta de crédito.

    Umbrales:
        Verde:   < 60% del límite
        Amarillo: 60-80% del límite
        Rojo:    > 80% del límite

    Args:
        porcentaje_uso: porcentaje del límite usado (Decimal, ej: 45 para 45%)

    Returns:
        dict con 'nivel' (verde/amarillo/rojo) y 'color' (hex)
    """
    if porcentaje_uso < 60:
        return {'nivel': 'verde', 'color': '#22c55e'}
    elif porcentaje_uso <= 80:
        return {'nivel': 'amarillo', 'color': '#eab308'}
    else:
        return {'nivel': 'rojo', 'color': '#ef4444'}


def calcular_disponible(limite, saldo_actual):
    """
    Calcula el disponible restante de una tarjeta.

    Fórmula: Disponible = Límite - Saldo actual

    Args:
        limite: límite de la tarjeta (Decimal)
        saldo_actual: saldo actual (Decimal)

    Returns:
        disponible en COP (Decimal)
    """
    disponible = limite - saldo_actual
    return disponible if disponible > 0 else Decimal('0')


def calcular_dias_proximo_corte(fecha_corte, referencia=None):
    """
    Calcula los días hasta el próximo corte de la tarjeta.

    Args:
        fecha_corte: día del mes del corte (1-31)
        referencia: fecha de referencia (date, por defecto today)

    Returns:
        días hasta el próximo corte (int)
    """
    from datetime import date as date_type
    from dateutil.relativedelta import relativedelta

    hoy = referencia or date_type.today()
    mes_corte = hoy.month
    anio_corte = hoy.year

    try:
        fecha_corte_obj = hoy.replace(day=min(fecha_corte, 28))
    except (ValueError, OverflowError):
        fecha_corte_obj = hoy.replace(day=28)

    if hoy > fecha_corte_obj:
        if mes_corte == 12:
            mes_corte = 1
            anio_corte += 1
        else:
            mes_corte += 1

    try:
        prox_corte = hoy.replace(year=anio_corte, month=mes_corte, day=min(fecha_corte, 28))
    except (ValueError, OverflowError):
        prox_corte = hoy.replace(year=anio_corte, month=mes_corte, day=28)

    return (prox_corte - hoy).days


def calcular_pago_diferido(monto, numero_cuotas):
    """
    Calcula el valor de cada cuota en una compra diferida.

    Args:
        monto: monto total de la compra (Decimal)
        numero_cuotas: número de cuotas (int)

    Returns:
        monto por cuota en COP (Decimal)
    """
    if numero_cuotas <= 0:
        return Decimal('0')
    return Q(monto / Decimal(str(numero_cuotas)))
