from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Q
from datetime import date
from dateutil.relativedelta import relativedelta
from apps.gastos.models import Categoria, Gasto
from apps.ingresos.models import RegistroNomina, OtroIngreso
from apps.deudas.models import Credito, CuotaCredito, TarjetaCredito
from apps.provisiones.models import FondoEmergencia, Provision
from apps.provisiones.services import (
    calcular_meses_restantes as _cmr_provision,
    calcular_progreso as _cp_provision,
    chequear_recordatorio as _cr_provision,
)
from .models import HistorialIndicador

Q_DEC = lambda x: x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ============================================================
# FUNCIONES BASE DE CÁLCULO (puras, sin BD)
# ============================================================


def calcular_ratio_endeudamiento(
    ingreso_neto: Decimal,
    total_cuotas_creditos: Decimal,
    minimos_tarjetas: Decimal,
) -> dict:
    """
    Calcula el ratio de endeudamiento mensual.

    Fórmula:
        Ratio = (Cuotas créditos + Mínimos TC) / Ingreso neto × 100

    Semáforo:
        Verde:   < 30%
        Amarillo: 30–40%
        Rojo:    > 40%

    Referencia: Circular SFC — indicadores de salud financiera

    Args:
        ingreso_neto:         ingreso neto total del mes (COP)
        total_cuotas_creditos: suma de cuotas de créditos activas (COP)
        minimos_tarjetas:     suma de pagos mínimos de tarjetas (COP)

    Returns:
        dict con valor y semáforo
    """
    if ingreso_neto <= Decimal("0"):
        return {"valor": Decimal("0"), "semaforo": "verde"}
    total_deuda = total_cuotas_creditos + minimos_tarjetas
    valor = Q_DEC((total_deuda / ingreso_neto) * 100)
    semaforo = _semaforo_endeudamiento(valor)
    return {"valor": valor, "semaforo": semaforo}


def _semaforo_endeudamiento(valor: Decimal) -> str:
    if valor < Decimal("30"):
        return "verde"
    elif valor <= Decimal("40"):
        return "amarillo"
    return "rojo"


def calcular_tasa_ahorro(
    ahorro_neto: Decimal, ingreso_neto: Decimal, meta: Decimal = Decimal("20")
) -> dict:
    """
    Calcula la tasa de ahorro mensual.

    Fórmula:
        Tasa = Ahorro neto / Ingreso neto × 100

    Semáforo:
        Verde:   ≥ meta (default 20%)
        Amarillo: 10% – meta
        Rojo:    < 10%

    Args:
        ahorro_neto:  ingreso neto - gastos totales (COP)
        ingreso_neto: ingreso neto total del mes (COP)
        meta:         meta de tasa de ahorro del usuario (%, default 20)

    Returns:
        dict con valor y semáforo
    """
    if ingreso_neto <= Decimal("0"):
        return {"valor": Decimal("0"), "semaforo": "verde"}
    valor = Q_DEC((ahorro_neto / ingreso_neto) * 100)
    semaforo = _semaforo_ahorro(valor, meta)
    return {"valor": valor, "semaforo": semaforo}


def _semaforo_ahorro(valor: Decimal, meta: Decimal) -> str:
    if valor >= meta:
        return "verde"
    elif valor >= Decimal("10"):
        return "amarillo"
    return "rojo"


def calcular_cobertura_emergencia(
    saldo_fondo: Decimal, gasto_esencial_mensual: Decimal
) -> dict:
    """
    Calcula la cobertura del fondo de emergencia en meses.

    Fórmula:
        Cobertura = Saldo fondo / Gasto esencial mensual

    Semáforo:
        Verde:   ≥ 3 meses
        Amarillo: 1–3 meses
        Rojo:    < 1 mes

    Args:
        saldo_fondo:            saldo actual del fondo de emergencia (COP)
        gasto_esencial_mensual: suma de gastos en categorías esenciales (COP)

    Returns:
        dict con valor (meses) y semáforo
    """
    if gasto_esencial_mensual <= Decimal("0"):
        return {"valor": Decimal("0"), "semaforo": "verde"}
    valor = Q_DEC(saldo_fondo / gasto_esencial_mensual)
    semaforo = _semaforo_emergencia(valor)
    return {"valor": valor, "semaforo": semaforo}


def _semaforo_emergencia(valor: Decimal) -> str:
    if valor >= Decimal("3"):
        return "verde"
    elif valor >= Decimal("1"):
        return "amarillo"
    return "rojo"


def calcular_presion_gastos_fijos(
    gastos_fijos: Decimal, ingreso_neto: Decimal
) -> Decimal:
    """
    Calcula la presión de gastos fijos sobre el ingreso.

    Fórmula:
        Presión = Gastos fijos / Ingreso neto × 100

    Referencia: idealmente < 50%

    Args:
        gastos_fijos: suma de gastos de tipo fijo del mes (COP)
        ingreso_neto: ingreso neto total del mes (COP)

    Returns:
        porcentaje de presión (Decimal)
    """
    if ingreso_neto <= Decimal("0"):
        return Decimal("0")
    return Q_DEC((gastos_fijos / ingreso_neto) * 100)


# ============================================================
# FUNCIONES CON BD (orquestación)
# ============================================================


def _calcular_ingresos_totales(usuario, mes, anio):
    total_nomina = RegistroNomina.objects.filter(
        usuario=usuario, mes=mes, anio=anio
    ).aggregate(s=Sum("neto_con_auxilio"))["s"] or Decimal("0")
    total_otros = OtroIngreso.objects.filter(
        usuario=usuario, mes=mes, anio=anio
    ).aggregate(s=Sum("monto"))["s"] or Decimal("0")
    return total_nomina + total_otros


def _calcular_gastos_totales(usuario, mes, anio):
    return Gasto.objects.filter(usuario=usuario, mes=mes, anio=anio).aggregate(
        s=Sum("monto")
    )["s"] or Decimal("0")


def _calcular_gastos_fijos(usuario, mes, anio):
    return Gasto.objects.filter(
        usuario=usuario, mes=mes, anio=anio, tipo="fijo"
    ).aggregate(s=Sum("monto"))["s"] or Decimal("0")


def _calcular_gasto_esencial(usuario, mes, anio):
    categorias_esenciales = Categoria.objects.filter(es_esencial=True, visible=True)
    total = Gasto.objects.filter(
        usuario=usuario,
        mes=mes,
        anio=anio,
        categoria__in=categorias_esenciales,
    ).aggregate(total=Sum("monto"))["total"] or Decimal("0")
    return total


def _calcular_cuotas_creditos_mes(usuario, mes, anio):
    credito_ids = Credito.objects.filter(usuario=usuario, activo=True).values_list(
        "id", flat=True
    )
    fecha_ref = date(anio, mes, 1)
    return CuotaCredito.objects.filter(
        credito_id__in=credito_ids,
        fecha_pago__year=anio,
        fecha_pago__month=mes,
        pagada=False,
    ).aggregate(s=Sum("cuota_total"))["s"] or Decimal("0")


def _calcular_minimos_tarjetas(usuario, mes, anio):
    tarjetas = TarjetaCredito.objects.filter(usuario=usuario, activa=True)
    total = Decimal("0")
    for t in tarjetas:
        total += Q_DEC(t.saldo_actual * t.cuota_minima_pct)
    return total


def _obtener_saldo_fondo(usuario):
    try:
        fondo = FondoEmergencia.objects.get(usuario=usuario)
        return fondo.saldo_actual
    except FondoEmergencia.DoesNotExist:
        return Decimal("0")


def calcular_indicadores_mes(usuario, mes, anio):
    """
    Calcula los 4 indicadores de salud financiera para un mes/año.

    Args:
        usuario: UserProfile instance
        mes:     mes (1–12)
        anio:    año (ej: 2026)

    Returns:
        dict con todos los indicadores, semáforos y valores intermedios
    """
    ingreso_neto = _calcular_ingresos_totales(usuario, mes, anio)
    gastos_totales = _calcular_gastos_totales(usuario, mes, anio)
    ahorro_neto = ingreso_neto - gastos_totales
    gastos_fijos = _calcular_gastos_fijos(usuario, mes, anio)
    gasto_esencial = _calcular_gasto_esencial(usuario, mes, anio)
    cuotas_creditos = _calcular_cuotas_creditos_mes(usuario, mes, anio)
    minimos_tarjetas = _calcular_minimos_tarjetas(usuario, mes, anio)
    saldo_fondo = _obtener_saldo_fondo(usuario)

    ratio_endeudamiento = calcular_ratio_endeudamiento(
        ingreso_neto, cuotas_creditos, minimos_tarjetas
    )
    tasa_ahorro = calcular_tasa_ahorro(
        ahorro_neto, ingreso_neto, usuario.meta_tasa_ahorro
    )
    cobertura = calcular_cobertura_emergencia(saldo_fondo, gasto_esencial)
    presion = calcular_presion_gastos_fijos(gastos_fijos, ingreso_neto)

    return {
        "ratio_endeudamiento": ratio_endeudamiento["valor"],
        "semaforo_endeudamiento": ratio_endeudamiento["semaforo"],
        "tasa_ahorro": tasa_ahorro["valor"],
        "semaforo_ahorro": tasa_ahorro["semaforo"],
        "cobertura_emergencia": cobertura["valor"],
        "semaforo_emergencia": cobertura["semaforo"],
        "presion_gastos_fijos": presion,
        "ingreso_neto": ingreso_neto,
        "ahorro_neto": ahorro_neto,
        "gastos_totales": gastos_totales,
        "gastos_fijos": gastos_fijos,
        "gasto_esencial": gasto_esencial,
        "cuotas_creditos_mes": cuotas_creditos,
        "minimos_tarjetas_mes": minimos_tarjetas,
        "saldo_fondo": saldo_fondo,
    }


def calcular_tendencia(usuario, indicador, mes, anio):
    """
    Calcula la tendencia de un indicador respecto al mes anterior.

    Args:
        usuario:  UserProfile instance
        indicador: nombre del campo en HistorialIndicador (ej: 'tasa_ahorro')
        mes:      mes actual
        anio:     año actual

    Returns:
        '↑' si mejoró, '↓' si empeoró, '→' si se mantuvo

    Nota: Para ratio_endeudamiento y presion_gastos_fijos,
    un valor MENOR es mejora. Para los demás, un valor MAYOR es mejora.
    """
    mejor_si_menor = {"ratio_endeudamiento", "presion_gastos_fijos"}
    mejor_si_mayor = {"tasa_ahorro", "cobertura_emergencia"}

    if indicador not in mejor_si_menor and indicador not in mejor_si_mayor:
        return "→"

    actual = HistorialIndicador.objects.filter(
        usuario=usuario, mes=mes, anio=anio
    ).first()
    if not actual:
        return "→"

    # Mes anterior
    if mes == 1:
        mes_ant, anio_ant = 12, anio - 1
    else:
        mes_ant, anio_ant = mes - 1, anio

    anterior = HistorialIndicador.objects.filter(
        usuario=usuario, mes=mes_ant, anio=anio_ant
    ).first()
    if not anterior:
        return "→"

    valor_actual = getattr(actual, indicador, Decimal("0"))
    valor_anterior = getattr(anterior, indicador, Decimal("0"))

    if valor_actual == valor_anterior:
        return "→"

    if indicador in mejor_si_menor:
        return "↓" if valor_actual < valor_anterior else "↑"
    else:
        return "↑" if valor_actual > valor_anterior else "↓"


def generar_diagnostico(indicadores):
    """
    Genera un diagnóstico automático de salud financiera
    basado en los indicadores calculados.

    Args:
        indicadores: dict con al menos tasa_ahorro, presion_gastos_fijos,
                     cobertura_emergencia, ratio_endeudamiento

    Returns:
        string con máximo 3 líneas de recomendación
    """
    criticos = []

    ta = indicadores.get("tasa_ahorro", 100)
    if ta < 10:
        criticos.append(f"Tasa de ahorro crítica ({ta:.0f}%). Revisa gastos variables.")
    elif ta < 20:
        criticos.append(
            f"Tasa de ahorro baja ({ta:.0f}%). Intenta reducir gastos no esenciales."
        )

    pf = indicadores.get("presion_gastos_fijos", 0)
    if pf > 50:
        criticos.append(f"Presión de gastos fijos alta ({pf:.0f}%). Ideal < 50%.")

    ce = indicadores.get("cobertura_emergencia", 99)
    if ce < 1:
        criticos.append(
            f"Fondo de emergencia crítico. Cobertura de {ce:.1f} meses. Prioriza este fondo."
        )

    re = indicadores.get("ratio_endeudamiento", 0)
    if re > 40:
        criticos.append(
            f"Ratio de endeudamiento alto ({re:.0f}%). Evita nuevas deudas."
        )

    if not criticos:
        return "Salud financiera estable. Sigue así."

    return " | ".join(criticos[:2])


def guardar_historial(usuario, mes, anio, indicadores):
    """
    Guarda un snapshot de los indicadores en HistorialIndicador.

    Args:
        usuario:     UserProfile instance
        mes:         mes (1–12)
        anio:        año
        indicadores: dict retornado por calcular_indicadores_mes()

    Returns:
        HistorialIndicador instance
    """
    historial, _ = HistorialIndicador.objects.update_or_create(
        usuario=usuario,
        mes=mes,
        anio=anio,
        defaults={
            "ratio_endeudamiento": indicadores["ratio_endeudamiento"],
            "semaforo_endeudamiento": indicadores["semaforo_endeudamiento"],
            "tasa_ahorro": indicadores["tasa_ahorro"],
            "semaforo_ahorro": indicadores["semaforo_ahorro"],
            "cobertura_emergencia": indicadores["cobertura_emergencia"],
            "semaforo_emergencia": indicadores["semaforo_emergencia"],
            "presion_gastos_fijos": indicadores["presion_gastos_fijos"],
        },
    )
    return historial


def obtener_historial(usuario, meses=12):
    """
    Obtiene el historial de indicadores de los últimos N meses.

    Args:
        usuario: UserProfile instance
        meses:   número de meses hacia atrás (default 12)

    Returns:
        QuerySet de HistorialIndicador ordenado por fecha descendente
    """
    hoy = date.today()
    fecha_limite = hoy - relativedelta(months=meses)
    return HistorialIndicador.objects.filter(
        usuario=usuario,
        anio__gte=fecha_limite.year,
    ).order_by("-anio", "-mes")


# ============================================================
# FUNCIONES PARA DASHBOARD INTEGRADO (HU-014 / S10)
# ============================================================


def obtener_tendencia_ingresos_gastos(usuario, meses=6):
    """
    Obtiene los totales de ingresos y gastos de los últimos N meses
    para el gráfico de línea del dashboard.

    Args:
        usuario: UserProfile instance
        meses:   cantidad de meses hacia atrás (default 6)

    Returns:
        dict con listas de etiquetas, ingresos y gastos
    """
    hoy = date.today()
    labels = []
    ingresos = []
    gastos = []

    MESES_CORTO = [
        "",
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    ]

    for i in range(meses - 1, -1, -1):
        d = hoy - relativedelta(months=i)
        m, a = d.month, d.year

        total_nomina = RegistroNomina.objects.filter(
            usuario=usuario, mes=m, anio=a
        ).aggregate(s=Sum("neto_con_auxilio"))["s"] or Decimal("0")
        total_otros = OtroIngreso.objects.filter(
            usuario=usuario, mes=m, anio=a
        ).aggregate(s=Sum("monto"))["s"] or Decimal("0")
        total_gasto = Gasto.objects.filter(usuario=usuario, mes=m, anio=a).aggregate(
            s=Sum("monto")
        )["s"] or Decimal("0")

        labels.append(f"{MESES_CORTO[m]} {a}")
        ingresos.append(float(total_nomina + total_otros))
        gastos.append(float(total_gasto))

    return {
        "labels": labels,
        "ingresos": ingresos,
        "gastos": gastos,
    }


def obtener_resumen_deudas(usuario):
    """
    Obtiene un resumen consolidado de créditos y tarjetas activas
    para el dashboard.

    Args:
        usuario: UserProfile instance

    Returns:
        dict con conteos, totales y lista de tarjetas con semáforo
    """
    creditos_activos = Credito.objects.filter(usuario=usuario, activo=True)
    tarjetas_activas = TarjetaCredito.objects.filter(usuario=usuario, activa=True)

    total_cuotas_mes = Decimal("0")
    total_saldo_creditos = Decimal("0")

    for c in creditos_activos:
        ultima = c.cuotas.filter(pagada=True).order_by("-numero").first()
        if ultima:
            total_saldo_creditos += ultima.saldo_capital
            siguiente = c.cuotas.filter(pagada=False).order_by("numero").first()
            if siguiente:
                total_cuotas_mes += siguiente.cuota_total
        else:
            total_saldo_creditos += c.capital

    total_saldo_tarjetas = tarjetas_activas.aggregate(s=Sum("saldo_actual"))[
        "s"
    ] or Decimal("0")

    total_minimos = Decimal("0")
    tarjetas_info = []
    for t in tarjetas_activas:
        pct = t.porcentaje_uso
        total_minimos += t.saldo_actual * t.cuota_minima_pct
        tarjetas_info.append(
            {
                "id": t.id,
                "nombre": t.nombre,
                "saldo_actual": t.saldo_actual,
                "limite": t.limite,
                "porcentaje_uso": pct,
                "semaforo": (
                    "verde" if pct < 60 else ("amarillo" if pct < 80 else "rojo")
                ),
                "disponible": t.disponible,
            }
        )

    return {
        "creditos_activos": creditos_activos.count(),
        "tarjetas_activas": tarjetas_activas.count(),
        "total_cuotas_mes": total_cuotas_mes,
        "total_saldo_creditos": total_saldo_creditos,
        "total_saldo_tarjetas": total_saldo_tarjetas,
        "total_minimos": total_minimos,
        "total_deuda_total": total_saldo_creditos + total_saldo_tarjetas,
        "tarjetas_info": tarjetas_info,
    }


def obtener_provisiones_activas(usuario, limite=5):
    """
    Obtiene las provisiones activas más urgentes para el dashboard.

    Args:
        usuario: UserProfile instance
        limite:  cantidad máxima a retornar (default 5)

    Returns:
        list de dicts con datos de cada provisión
    """
    provisiones = Provision.objects.filter(usuario=usuario, activa=True).order_by(
        "fecha_pago"
    )[:limite]

    resultados = []
    for p in provisiones:
        meses_rest = _cmr_provision(p.fecha_pago)
        progreso = _cp_provision(p.ahorro_acumulado, p.monto_total)
        alerta = _cr_provision(p.fecha_pago, progreso)

        faltante = max(p.monto_total - p.ahorro_acumulado, Decimal("0"))

        resultados.append(
            {
                "id": p.id,
                "concepto": p.concepto,
                "monto_total": p.monto_total,
                "ahorro_acumulado": p.ahorro_acumulado,
                "faltante": faltante,
                "progreso": int(progreso),
                "fecha_pago": p.fecha_pago,
                "meses_restantes": meses_rest,
                "alerta": alerta,
            }
        )

    return resultados
