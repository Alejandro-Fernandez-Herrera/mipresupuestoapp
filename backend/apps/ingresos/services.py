from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

Q = lambda x: x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def calcular_nomina(salario_bruto, config):
    """
    Calcula el salario neto a partir del salario bruto usando parámetros colombianos.

    Fórmulas:
        Salud:        salario_bruto × tasa_salud_empleado (4%)
        Pensión:      salario_bruto × tasa_pension_empleado (4%)
        Solidaridad:  1% si salario > 4 SMLV (escala progresiva, ver ConfiguracionFiscal)
        Retención:    0% si ingreso ≤ umbral_retencion_uvt × UVT/mes
                      (requiere tabla DIAN progresiva para montos superiores)
        Neto = Bruto - Salud - Pensión - Solidaridad - Retención
        Auxilio transporte: aplica si salario_bruto ≤ 2 SMLV

    Referencias:
        - Ley 100/93 (Salud y Pensión)
        - Decreto anual SMLV
        - DIAN — tabla retención en la fuente

    Args:
        salario_bruto: salario base mensual en COP (Decimal)
        config: instancia de ConfiguracionFiscal con parámetros del año

    Returns:
        dict con todas las deducciones y el neto calculado
    """
    salud = Q(salario_bruto * config.tasa_salud_empleado)
    pension = Q(salario_bruto * config.tasa_pension_empleado)

    umbral_solidaridad = config.smlv * config.umbral_solidaridad_smlv
    if salario_bruto > umbral_solidaridad:
        smlvs = salario_bruto / config.smlv
        if smlvs <= Decimal("16"):
            tasa_solidaridad = config.tasa_solidaridad_4_16
        elif smlvs <= Decimal("17"):
            tasa_solidaridad = config.tasa_solidaridad_16_17
        elif smlvs <= Decimal("18"):
            tasa_solidaridad = config.tasa_solidaridad_17_18
        elif smlvs <= Decimal("19"):
            tasa_solidaridad = config.tasa_solidaridad_18_19
        elif smlvs <= Decimal("20"):
            tasa_solidaridad = config.tasa_solidaridad_19_20
        else:
            tasa_solidaridad = config.tasa_solidaridad_mas_20
        solidaridad = Q(salario_bruto * tasa_solidaridad)
    else:
        solidaridad = Decimal("0")

    uvt_mes = salario_bruto / config.uvt
    if uvt_mes <= config.umbral_retencion_uvt:
        retencion = Decimal("0")
    else:
        retencion = None

    neto = salario_bruto - salud - pension - solidaridad
    if retencion is not None:
        neto -= retencion

    aplica_auxilio = salario_bruto <= (config.smlv * 2)
    auxilio = config.auxilio_transporte if aplica_auxilio else Decimal("0")

    return {
        "salario_bruto": salario_bruto,
        "deduccion_salud": salud,
        "deduccion_pension": pension,
        "deduccion_solidaridad": solidaridad,
        "retencion_fuente": retencion,
        "salario_neto": neto,
        "aplica_auxilio": aplica_auxilio,
        "auxilio_transporte": auxilio,
        "neto_con_auxilio": neto + auxilio,
    }


def calcular_prima(salario_base, meses, config):
    """
    Calcula la provisión mensual de prima de servicios.

    Fórmula:
        Prima mensual = Salario base × factor_prima_mensual (8.33%)
        Prima total = Prima mensual × meses trabajados

    Referencia: CST Art. 306 — prima de servicios (30 días de salario por año)

    Args:
        salario_base: salario base mensual (COP)
        meses: número de meses acumulados
        config: ConfiguracionFiscal

    Returns:
        monto total de prima proyectada (Decimal)
    """
    prima_mensual = Q(salario_base * config.factor_prima_mensual)
    return Q(prima_mensual * meses)


def calcular_cesantias(salario_base, meses, config):
    """
    Calcula la provisión mensual de cesantías.

    Fórmula:
        Cesantías mensual = Salario base × factor_cesantias_mensual (8.33%)
        Cesantías total = Cesantías mensual × meses trabajados

    Referencia: CST Art. 249 — cesantías (30 días de salario por año)

    Args:
        salario_base: salario base mensual (COP)
        meses: número de meses acumulados
        config: ConfiguracionFiscal

    Returns:
        monto total de cesantías proyectadas (Decimal)
    """
    cesantias_mensual = Q(salario_base * config.factor_cesantias_mensual)
    return Q(cesantias_mensual * meses)


def calcular_intereses_cesantias(cesantias_acumuladas, meses, config):
    """
    Calcula los intereses sobre cesantías acumuladas.

    Fórmula:
        Intereses = Cesantías acumuladas × tasa_intereses_cesantias (12%)
                    × (meses / 12)

    Referencia: Ley 52/75 — intereses sobre cesantías (12% anual)

    Args:
        cesantias_acumuladas: total de cesantías acumuladas (COP)
        meses: número de meses del período (usualmente 12 para cálculo anual)
        config: ConfiguracionFiscal

    Returns:
        monto de intereses sobre cesantías (Decimal)
    """
    return Q(cesantias_acumuladas * config.tasa_intereses_cesantias * meses / 12)


def calcular_vacaciones(salario_base, config):
    """
    Calcula la provisión mensual de vacaciones.

    Fórmula:
        Vacaciones mensual = Salario base × factor_vacaciones_mensual (4.17%)

    Referencia: CST Art. 186–192 — vacaciones (15 días hábiles por año)

    Args:
        salario_base: salario base mensual (COP)
        config: ConfiguracionFiscal

    Returns:
        monto de provisión mensual de vacaciones (Decimal)
    """
    return Q(salario_base * config.factor_vacaciones_mensual)


def _calcular_fechas_prestaciones(anio):
    """
    Calcula las fechas de pago de prestaciones sociales para un año dado.

    Args:
        anio: año para el cual calcular las fechas

    Returns:
        dict con las fechas de pago de cada prestación
    """
    return {
        'prima_junio': date(anio, 6, 30),
        'prima_diciembre': date(anio, 12, 20),
        'cesantias': date(anio + 1, 2, 14),
        'intereses_cesantias': date(anio + 1, 1, 31),
    }


def calcular_prestaciones(salario_base, meses, config, anio=None):
    """
    Calcula todas las prestaciones sociales proyectadas para un período.

    Las fechas de pago se calculan dinámicamente según el año actual,
    evitando fechas hardcodeadas.

    Args:
        salario_base: salario base mensual (COP)
        meses: número de meses trabajados en el período
        config: ConfiguracionFiscal
        anio: año base para el cálculo (default: año actual)

    Returns:
        dict con cada prestación y sus fechas de pago esperadas
    """
    if anio is None:
        anio = date.today().year

    prima = calcular_prima(salario_base, meses, config)
    cesantias = calcular_cesantias(salario_base, meses, config)
    intereses = calcular_intereses_cesantias(cesantias, meses, config)
    vacaciones = calcular_vacaciones(salario_base, config)
    fechas = _calcular_fechas_prestaciones(anio)

    return {
        "prima_servicios": {
            "monto": prima,
            "fecha_pago_1": fechas['prima_junio'],
            "fecha_pago_2": fechas['prima_diciembre'],
        },
        "cesantias": {
            "monto": cesantias,
            "fecha_pago": fechas['cesantias'],
        },
        "intereses_cesantias": {
            "monto": intereses,
            "fecha_pago": fechas['intereses_cesantias'],
        },
        "vacaciones": {
            "monto_mensual": vacaciones,
        },
    }


def calcular_alerta_prestacion(fecha_pago, dias_alerta=45):
    """
    Determina si una prestación está próxima a vencer y debe generar alerta.

    Args:
        fecha_pago:    fecha de pago esperada de la prestación
        dias_alerta:   número de días antes para emitir alerta (default: 45)

    Returns:
        dict con:
            - alerta: bool — True si debe mostrar alerta
            - dias_restantes: int — días hasta la fecha de pago
            - nivel: str — 'critico' (≤7 días), 'proximo' (≤45 días), 'normal'
    """
    hoy = date.today()
    dias_restantes = (fecha_pago - hoy).days

    if dias_restantes < 0:
        return {'alerta': False, 'dias_restantes': dias_restantes, 'nivel': 'vencida'}

    if dias_restantes <= 7:
        return {'alerta': True, 'dias_restantes': dias_restantes, 'nivel': 'critico'}
    elif dias_restantes <= dias_alerta:
        return {'alerta': True, 'dias_restantes': dias_restantes, 'nivel': 'proximo'}

    return {'alerta': False, 'dias_restantes': dias_restantes, 'nivel': 'normal'}


def verificar_alertas_prestaciones(usuario):
    """
    Verifica todas las prestaciones pendientes de un usuario y
    retorna las que están próximas a vencer.

    Args:
        usuario: UserProfile instance

    Returns:
        list de dicts con prestación + alerta para las que están próximas
    """
    from .models import PrestacionSocial
    prestaciones = PrestacionSocial.objects.filter(
        usuario=usuario, pagada=False
    )
    alertas = []
    for p in prestaciones:
        info_alerta = calcular_alerta_prestacion(p.fecha_pago_esperada)
        if info_alerta['alerta']:
            alertas.append({
                'prestacion': p,
                'alerta': info_alerta,
            })
    return alertas
