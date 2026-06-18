from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Avg

from apps.ingresos.models import RegistroNomina, OtroIngreso
from apps.gastos.models import Gasto, Categoria
from apps.provisiones.models import FondoEmergencia, AporteFondo, Provision
from apps.provisiones.services import (
    calcular_progreso,
    calcular_meses_restantes,
    calcular_ahorro_mensual_recomendado,
    calcular_ahorro_maximo_alcanzable,
    evaluar_alcanzabilidad,
)

Q = lambda x: x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


# ============================================================
# HELPER: Promedio histórico mensual
# ============================================================


def _promedio_ingresos_reales(usuario, mes, anio):
    """
    Calcula el ingreso neto promedio de un mes específico usando datos históricos
    del mismo mes del año anterior (si existe) o del último mes con datos.

    Returns:
        dict con 'nomina' y 'otro' como Decimal
    """
    hoy = date.today()
    nomina_total = Decimal("0")
    otro_total = Decimal("0")

    registros_nomina = RegistroNomina.objects.filter(
        usuario=usuario, mes=mes, anio=anio
    )
    if registros_nomina.exists():
        agg = registros_nomina.aggregate(s=Sum("neto_con_auxilio"))
        nomina_total = agg["s"] or Decimal("0")
    else:
        registros_previos = RegistroNomina.objects.filter(
            usuario=usuario, mes=mes, anio__lt=anio
        ).aggregate(avg=Avg("neto_con_auxilio"))
        nomina_total = registros_previos["avg"] or Decimal("0")

    otros = OtroIngreso.objects.filter(usuario=usuario, mes=mes, anio=anio)
    if otros.exists():
        agg = otros.aggregate(s=Sum("monto"))
        otro_total = agg["s"] or Decimal("0")
    else:
        otros_previos = OtroIngreso.objects.filter(
            usuario=usuario, mes=mes, anio__lt=anio
        ).aggregate(avg=Avg("monto"))
        otro_total = otros_previos["avg"] or Decimal("0")

    return {"nomina": nomina_total, "otro": otro_total}


def _promedio_gastos_reales(usuario, mes, anio):
    """
    Calcula el gasto promedio de un mes específico usando datos históricos.
    """
    total = Gasto.objects.filter(usuario=usuario, mes=mes, anio=anio)
    if total.exists():
        agg = total.aggregate(s=Sum("monto"))
        return agg["s"] or Decimal("0")

    previos = Gasto.objects.filter(usuario=usuario, mes=mes, anio__lt=anio).aggregate(
        avg=Avg("monto")
    )
    return previos["avg"] or Decimal("0")


# ============================================================
# PROYECCIÓN DE INGRESOS (RF-100)
# ============================================================


def proyectar_ingresos_mes(usuario, mes, anio, escenario=None):
    """
    Proyecta los ingresos totales para un mes/año específicos.

    Estrategia:
    1. Si existen proyecciones manuales (ProyeccionIngreso), usar esas
    2. Si no, inferir de datos reales históricos
    3. Aplicar factor del escenario (si existe)

    Args:
        usuario: UserProfile
        mes: int (1-12)
        anio: int
        escenario: instancia Escenario (opcional)

    Returns:
        dict con 'total', 'nomina', 'otro' en COP
    """
    from .models import ProyeccionIngreso as PI

    proyecciones = PI.objects.filter(
        usuario=usuario, mes=mes, anio=anio, escenario=escenario
    )
    if proyecciones.exists():
        nomina = Decimal("0")
        otro = Decimal("0")
        for p in proyecciones:
            if p.fuente == "nomina":
                nomina += p.monto_proyectado
            else:
                otro += p.monto_proyectado
        total = nomina + otro
    else:
        reales = _promedio_ingresos_reales(usuario, mes, anio)
        nomina = reales["nomina"]
        otro = reales["otro"]
        total = nomina + otro

    if escenario and escenario.factor_ingreso != Decimal("1"):
        total = Q(total * escenario.factor_ingreso)
        nomina = Q(nomina * escenario.factor_ingreso)
        otro = Q(otro * escenario.factor_ingreso)

    return {"total": total, "nomina": nomina, "otro": otro}


# ============================================================
# PROYECCIÓN DE GASTOS (RF-101)
# ============================================================


def proyectar_gastos_mes(usuario, mes, anio, escenario=None):
    """
    Proyecta los gastos totales para un mes/año específicos.

    Estrategia:
    1. Si existen proyecciones manuales (ProyeccionGasto), usar esas
    2. Si no, inferir de datos reales históricos
    3. Aplicar factor del escenario (si existe)

    Returns:
        dict con 'total' en COP y 'por_categoria' (lista de dicts)
    """
    from .models import ProyeccionGasto as PG

    proyecciones = PG.objects.filter(
        usuario=usuario, mes=mes, anio=anio, escenario=escenario
    )
    if proyecciones.exists():
        total = proyecciones.aggregate(s=Sum("monto_proyectado"))["s"] or Decimal("0")
        por_categoria = [
            {
                "categoria": p.categoria.nombre if p.categoria else "Sin categoría",
                "color": p.categoria.color if p.categoria else "#999999",
                "monto": p.monto_proyectado,
            }
            for p in proyecciones.select_related("categoria")
        ]
    else:
        total = _promedio_gastos_reales(usuario, mes, anio)
        por_categoria = []
        if total > 0:
            gastos = Gasto.objects.filter(usuario=usuario, mes=mes, anio=anio)
            if not gastos.exists():
                gastos = Gasto.objects.filter(usuario=usuario, mes=mes, anio__lt=anio)
            if gastos.exists():
                cats = (
                    gastos.values("categoria__nombre", "categoria__color")
                    .annotate(total=Sum("monto"))
                    .order_by("-total")
                )
                por_categoria = [
                    {
                        "categoria": c["categoria__nombre"],
                        "color": c["categoria__color"],
                        "monto": c["total"],
                    }
                    for c in cats
                ]

    if escenario and escenario.factor_gasto != Decimal("1"):
        total = Q(total * escenario.factor_gasto)
        for item in por_categoria:
            item["monto"] = Q(item["monto"] * escenario.factor_gasto)

    return {"total": total, "por_categoria": por_categoria}


# ============================================================
# PROYECCIÓN DE AHORRO (RF-102)
# ============================================================


def calcular_ahorro_proyectado(usuario, meses, escenario=None):
    """
    Calcula la proyección de ahorro mensual y acumulado a N meses.

    Args:
        usuario: UserProfile
        meses: int — cantidad de meses a proyectar (6, 12, 24)
        escenario: instancia Escenario (opcional)

    Returns:
        dict con 'mensual', 'acumulado', 'detalle_meses' (lista de dicts)
    """
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year

    total_ingresos = Decimal("0")
    total_gastos = Decimal("0")
    detalle = []

    for i in range(meses):
        m = mes_actual + i
        a = anio_actual
        while m > 12:
            m -= 12
            a += 1

        ing = proyectar_ingresos_mes(usuario, m, a, escenario)
        gas = proyectar_gastos_mes(usuario, m, a, escenario)
        ahorro = ing["total"] - gas["total"]
        total_ingresos += ing["total"]
        total_gastos += gas["total"]

        detalle.append(
            {
                "mes": m,
                "anio": a,
                "ingresos": ing["total"],
                "gastos": gas["total"],
                "ahorro": ahorro,
            }
        )

    ahorro_mensual_promedio = Q(total_ingresos - total_gastos) / Decimal(str(meses))
    ahorro_acumulado = total_ingresos - total_gastos

    return {
        "ahorro_mensual_promedio": Q(ahorro_mensual_promedio),
        "ahorro_acumulado": Q(ahorro_acumulado),
        "total_ingresos_acumulado": Q(total_ingresos),
        "total_gastos_acumulado": Q(total_gastos),
        "detalle_meses": detalle,
    }


# ============================================================
# PROYECCIÓN FONDO DE EMERGENCIA (RF-104)
# ============================================================


def calcular_mes_meta_emergencia(usuario, escenario=None):
    """
    Calcula en qué mes se alcanza la meta del fondo de emergencia
    (1, 3 y 6 meses de gasto esencial) según el ahorro proyectado
    del escenario seleccionado.

    Returns:
        dict con 'minimo', 'recomendado', 'ideal' — cada uno con
            {'alcanza': bool, 'mes': int, 'anio': int, 'meses_necesarios': int|None}
    """
    from apps.provisiones.services import (
        calcular_gasto_esencial_mensual,
        calcular_meta_niveles,
    )

    hoy = date.today()
    gasto_esencial = calcular_gasto_esencial_mensual(usuario)
    metas = calcular_meta_niveles(gasto_esencial)

    try:
        fondo = FondoEmergencia.objects.get(usuario=usuario)
        saldo_actual = fondo.saldo_actual
    except FondoEmergencia.DoesNotExist:
        saldo_actual = Decimal("0")

    # Ahorro mensual proyectado (promedio a 12 meses)
    proy = calcular_ahorro_proyectado(usuario, 12, escenario)
    ahorro_mensual = proy["ahorro_mensual_promedio"]

    resultado = {}
    for nivel, meta in [
        ("minimo", metas["minimo"]),
        ("recomendado", metas["recomendado"]),
        ("ideal", metas["ideal"]),
    ]:
        restante = meta - saldo_actual
        if restante <= Decimal("0"):
            resultado[nivel] = {
                "alcanza": True,
                "mes": hoy.month,
                "anio": hoy.year,
                "meses_necesarios": 0,
            }
            continue
        if ahorro_mensual <= Decimal("0"):
            resultado[nivel] = {
                "alcanza": False,
                "mes": None,
                "anio": None,
                "meses_necesarios": None,
            }
            continue
        meses_necesarios = int(
            (restante / ahorro_mensual).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        meses_necesarios = max(meses_necesarios, 1)
        fecha_meta = hoy + relativedelta(months=meses_necesarios)
        resultado[nivel] = {
            "alcanza": True,
            "mes": fecha_meta.month,
            "anio": fecha_meta.year,
            "meses_necesarios": meses_necesarios,
        }

    return resultado


# ============================================================
# PROYECCIÓN CIERRE PROVISIONES (RF-105)
# ============================================================


def proyectar_cierre_provisiones(usuario, escenario=None):
    """
    Para cada provisión activa, calcula si se cierra o no al ritmo
    de ahorro proyectado del escenario.

    Returns:
        list de dicts con info de cada provisión
    """
    proy = calcular_ahorro_proyectado(usuario, 12, escenario)
    ahorro_mensual = proy["ahorro_mensual_promedio"]

    provisiones = Provision.objects.filter(usuario=usuario, activa=True)
    resultados = []

    for p in provisiones:
        meses_rest = calcular_meses_restantes(p.fecha_pago)
        ahorro_disponible = max(ahorro_mensual, p.ahorro_mensual_disponible)
        rec = calcular_ahorro_mensual_recomendado(
            p.monto_total, p.ahorro_acumulado, meses_rest
        )
        maximo = calcular_ahorro_maximo_alcanzable(ahorro_disponible, meses_rest)
        alcanza, deficit = evaluar_alcanzabilidad(
            p.ahorro_acumulado, maximo, p.monto_total
        )
        progreso = calcular_progreso(p.ahorro_acumulado, p.monto_total)

        resultados.append(
            {
                "concepto": p.concepto,
                "monto_total": p.monto_total,
                "ahorro_acumulado": p.ahorro_acumulado,
                "fecha_pago": p.fecha_pago,
                "meses_restantes": meses_rest,
                "progreso": progreso,
                "ahorro_recomendado": rec,
                "ahorro_disponible_proyectado": ahorro_disponible,
                "alcanza": alcanza,
                "deficit": deficit,
            }
        )

    return resultados
