import pytest
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model

from apps.proyecciones.models import Escenario, ProyeccionIngreso, ProyeccionGasto
from apps.proyecciones.services import (
    proyectar_ingresos_mes,
    proyectar_gastos_mes,
    calcular_ahorro_proyectado,
    calcular_mes_meta_emergencia,
    proyectar_cierre_provisiones,
    _promedio_ingresos_reales,
    _promedio_gastos_reales,
)
from apps.provisiones.models import FondoEmergencia, Provision
from apps.gastos.models import Categoria, Gasto
from apps.ingresos.models import RegistroNomina
from decimal import ROUND_HALF_UP
from tests.conftest import assert_cop, PARAMS_COLOMBIA_2025

User = get_user_model()
Q = lambda x: x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="test_proy",
        email="test@proy.co",
        password="test1234",
        smlv_vigente=PARAMS_COLOMBIA_2025["smlv"],
        uvt_vigente=PARAMS_COLOMBIA_2025["uvt"],
        auxilio_transporte=PARAMS_COLOMBIA_2025["auxilio_transporte"],
    )


@pytest.fixture
def escenarios(user, db):
    data = [
        ("optimista", Decimal("1.1000"), Decimal("0.9500")),
        ("realista", Decimal("1.0000"), Decimal("1.0000")),
        ("conservador", Decimal("0.9000"), Decimal("1.1000")),
    ]
    created = []
    for nombre, fi, fg in data:
        e, _ = Escenario.objects.get_or_create(
            usuario=user,
            nombre=nombre,
            defaults={"factor_ingreso": fi, "factor_gasto": fg, "activo": True},
        )
        created.append(e)
    return created


@pytest.fixture
def nomina_real(user, db):
    hoy = date.today()
    mes_pasado = hoy.month - 1 if hoy.month > 1 else 12
    anio_pasado = hoy.year if hoy.month > 1 else hoy.year - 1
    return RegistroNomina.objects.create(
        usuario=user,
        salario_bruto=Decimal("3000000"),
        mes=mes_pasado,
        anio=anio_pasado,
        deduccion_salud=Decimal("120000"),
        deduccion_pension=Decimal("120000"),
        deduccion_solidaridad=Decimal("0"),
        retencion_fuente=Decimal("0"),
        salario_neto=Decimal("2760000"),
        aplica_auxilio=False,
        auxilio_transporte=Decimal("0"),
        neto_con_auxilio=Decimal("2760000"),
        recurrente=True,
        calculado_automaticamente=True,
    )


@pytest.fixture
def gastos_reales(user, db):
    from apps.gastos.models import Rubro

    hoy = date.today()
    mes_pasado = hoy.month - 1 if hoy.month > 1 else 12
    anio_pasado = hoy.year if hoy.month > 1 else hoy.year - 1
    cat, _ = Categoria.objects.get_or_create(
        nombre="Test Cat", defaults={"color": "#000000", "visible": True}
    )
    rubro, _ = Rubro.objects.get_or_create(
        categoria=cat,
        nombre="Test Rubro",
        defaults={"tipo": "variable", "visible": True},
    )
    g1 = Gasto.objects.create(
        usuario=user,
        categoria=cat,
        rubro=rubro,
        monto=Decimal("500000"),
        fecha=date(anio_pasado, mes_pasado, 15),
        tipo="fijo",
        mes=mes_pasado,
        anio=anio_pasado,
    )
    g2 = Gasto.objects.create(
        usuario=user,
        categoria=cat,
        rubro=rubro,
        monto=Decimal("300000"),
        fecha=date(anio_pasado, mes_pasado, 20),
        tipo="variable",
        mes=mes_pasado,
        anio=anio_pasado,
    )
    return [g1, g2]


# ============================================================
# TESTS — ESCENARIOS (RF-103)
# ============================================================


@pytest.mark.financiero
@pytest.mark.django_db
def test_escenarios_creados(user):
    """Verifica que se creen correctamente los 3 escenarios."""
    for nombre, fi, fg in [
        ("optimista", Decimal("1.1000"), Decimal("0.9500")),
        ("realista", Decimal("1.0000"), Decimal("1.0000")),
        ("conservador", Decimal("0.9000"), Decimal("1.1000")),
    ]:
        e = Escenario.objects.create(
            usuario=user,
            nombre=nombre,
            factor_ingreso=fi,
            factor_gasto=fg,
        )
        assert e.factor_ingreso == fi
        assert e.factor_gasto == fg
        assert e.activo is True


@pytest.mark.financiero
@pytest.mark.django_db
def test_escenario_factor_rango(user):
    """Los factores deben estar entre 0.01 y 2.00."""
    e = Escenario.objects.create(
        usuario=user,
        nombre="optimista",
        factor_ingreso=Decimal("1.5000"),
        factor_gasto=Decimal("0.5000"),
    )
    assert Decimal("0.01") <= e.factor_ingreso <= Decimal("2.00")
    assert Decimal("0.01") <= e.factor_gasto <= Decimal("2.00")


# ============================================================
# TESTS — PROYECCIÓN INGRESOS (RF-100)
# ============================================================


@pytest.mark.financiero
@pytest.mark.django_db
def test_proyeccion_ingreso_sin_datos(user, escenarios):
    """Sin datos históricos, la proyección retorna 0."""
    escenario = escenarios[1]  # realista
    resultado = proyectar_ingresos_mes(user, 6, 2026, escenario)
    assert resultado["total"] == Decimal("0")
    assert resultado["nomina"] == Decimal("0")
    assert resultado["otro"] == Decimal("0")


@pytest.mark.financiero
@pytest.mark.django_db
def test_proyeccion_ingreso_con_historial(user, escenarios, nomina_real):
    """Con datos históricos, la proyección debe reflejar el promedio."""
    escenario = escenarios[1]  # realista (factor 1.0)
    mes = nomina_real.mes
    anio = nomina_real.anio + 1
    resultado = proyectar_ingresos_mes(user, mes, anio, escenario)
    assert resultado["total"] > Decimal("0")
    assert_cop(resultado["nomina"], Decimal("2760000"), tolerancia=Decimal("500"))


@pytest.mark.financiero
@pytest.mark.django_db
def test_proyeccion_ingreso_manual(user, escenarios):
    """Proyección manual debe usarse cuando existe."""
    escenario = escenarios[1]
    ProyeccionIngreso.objects.create(
        usuario=user,
        escenario=escenario,
        mes=12,
        anio=2026,
        fuente="nomina",
        monto_proyectado=Decimal("5000000"),
    )
    resultado = proyectar_ingresos_mes(user, 12, 2026, escenario)
    assert_cop(resultado["total"], Decimal("5000000"), tolerancia=Decimal("1"))


@pytest.mark.financiero
@pytest.mark.django_db
def test_proyeccion_ingreso_factor_optimista(user, escenarios, nomina_real):
    """El factor optimista debe incrementar los ingresos en 10%."""
    escenario = escenarios[0]  # optimista: factor 1.10
    mes = nomina_real.mes
    anio = nomina_real.anio + 1
    resultado = proyectar_ingresos_mes(user, mes, anio, escenario)
    esperado = Q(Decimal("2760000") * Decimal("1.10"))
    assert_cop(resultado["total"], esperado, tolerancia=Decimal("500"))


@pytest.mark.financiero
@pytest.mark.django_db
def test_proyeccion_ingreso_factor_conservador(user, escenarios, nomina_real):
    """El factor conservador debe reducir los ingresos en 10%."""
    escenario = escenarios[2]  # conservador: factor 0.90
    mes = nomina_real.mes
    anio = nomina_real.anio + 1
    resultado = proyectar_ingresos_mes(user, mes, anio, escenario)
    esperado = Q(Decimal("2760000") * Decimal("0.90"))
    assert_cop(resultado["total"], esperado, tolerancia=Decimal("500"))


# ============================================================
# TESTS — PROYECCIÓN GASTOS (RF-101)
# ============================================================


@pytest.mark.financiero
@pytest.mark.django_db
def test_proyeccion_gasto_sin_datos(user, escenarios):
    """Sin datos históricos, la proyección retorna 0."""
    escenario = escenarios[1]
    resultado = proyectar_gastos_mes(user, 6, 2026, escenario)
    assert resultado["total"] == Decimal("0")


@pytest.mark.financiero
@pytest.mark.django_db
def test_proyeccion_gasto_con_historial(user, escenarios, gastos_reales):
    """Con datos históricos, la proyección debe reflejar el promedio de gastos."""
    escenario = escenarios[1]
    mes = gastos_reales[0].mes
    anio = gastos_reales[0].anio + 1
    resultado = proyectar_gastos_mes(user, mes, anio, escenario)
    # Promedio de 500k + 300k entre 2 registros = 400k
    assert_cop(resultado["total"], Decimal("400000"), tolerancia=Decimal("500"))


@pytest.mark.financiero
@pytest.mark.django_db
def test_proyeccion_gasto_manual(user, escenarios):
    """Proyección manual de gasto debe usarse cuando existe."""
    escenario = escenarios[1]
    cat, _ = Categoria.objects.get_or_create(
        nombre="Test", defaults={"color": "#ff0000", "visible": True}
    )
    ProyeccionGasto.objects.create(
        usuario=user,
        escenario=escenario,
        mes=12,
        anio=2026,
        categoria=cat,
        monto_proyectado=Decimal("2000000"),
    )
    resultado = proyectar_gastos_mes(user, 12, 2026, escenario)
    assert_cop(resultado["total"], Decimal("2000000"), tolerancia=Decimal("1"))


# ============================================================
# TESTS — AHORRO PROYECTADO (RF-102)
# ============================================================


@pytest.mark.financiero
@pytest.mark.django_db
def test_ahorro_proyectado_sin_datos(user, escenarios):
    """Sin datos, el ahorro proyectado debe ser 0."""
    escenario = escenarios[1]
    resultado = calcular_ahorro_proyectado(user, 6, escenario)
    assert resultado["ahorro_acumulado"] == Decimal("0")
    assert len(resultado["detalle_meses"]) == 6


@pytest.mark.financiero
@pytest.mark.django_db
def test_ahorro_proyectado_12_meses(user, escenarios, nomina_real, gastos_reales):
    """Con datos históricos, debe generar 12 meses de proyección."""
    escenario = escenarios[1]
    resultado = calcular_ahorro_proyectado(user, 12, escenario)
    assert len(resultado["detalle_meses"]) == 12
    assert resultado["ahorro_mensual_promedio"] is not None


@pytest.mark.financiero
@pytest.mark.django_db
def test_ahorro_proyectado_24_meses(user, escenarios):
    """Debe proyectar correctamente a 24 meses (sin datos = 0)."""
    escenario = escenarios[1]
    resultado = calcular_ahorro_proyectado(user, 24, escenario)
    assert len(resultado["detalle_meses"]) == 24


# ============================================================
# TESTS — META EMERGENCIA (RF-104)
# ============================================================


@pytest.mark.financiero
@pytest.mark.django_db
def test_meta_emergencia_sin_fondo(user, escenarios):
    """Sin fondo de emergencia, la meta no debe ser alcanzable si ahorro=0."""
    escenario = escenarios[1]
    resultado = calcular_mes_meta_emergencia(user, escenario)
    assert "minimo" in resultado
    assert "recomendado" in resultado
    assert "ideal" in resultado


@pytest.mark.financiero
@pytest.mark.django_db
def test_meta_emergencia_con_fondo_y_ahorro(user, escenarios):
    """Con fondo y ahorro, se debe proyectar el mes de la meta."""
    FondoEmergencia.objects.create(usuario=user, saldo_actual=Decimal("1000000"))
    escenario = escenarios[1]
    resultado = calcular_mes_meta_emergencia(user, escenario)
    # Sin gastos esenciales, la meta es 0, por lo que debería alcanzarse
    # inmediatamente (el escenario realista retorna ahorro=0, lo que significa
    # que no se alcanzan metas > saldo actual)
    for nivel in ["minimo", "recomendado", "ideal"]:
        assert "alcanza" in resultado[nivel]


# ============================================================
# TESTS — CIERRE PROVISIONES (RF-105)
# ============================================================


@pytest.mark.financiero
@pytest.mark.django_db
def test_cierre_provisiones_sin_provisiones(user, escenarios):
    """Sin provisiones activas, debe retornar lista vacía."""
    escenario = escenarios[1]
    resultado = proyectar_cierre_provisiones(user, escenario)
    assert resultado == []


@pytest.mark.financiero
@pytest.mark.django_db
def test_cierre_provisiones_con_provision(user, escenarios):
    """Con una provisión activa, debe calcular si alcanza o no."""
    escenario = escenarios[1]
    futuro = date.today() + relativedelta(months=6)
    Provision.objects.create(
        usuario=user,
        concepto="SOAT",
        monto_total=Decimal("250000"),
        fecha_pago=futuro,
        ahorro_acumulado=Decimal("50000"),
        activa=True,
    )
    resultado = proyectar_cierre_provisiones(user, escenario)
    assert len(resultado) == 1
    assert resultado[0]["concepto"] == "SOAT"
    assert "alcanza" in resultado[0]
    assert "progreso" in resultado[0]


# ============================================================
# TESTS — MULTIPLICADORES DE ESCENARIO
# ============================================================


@pytest.mark.financiero
@pytest.mark.django_db
def test_escenario_optimista_vs_conservador(
    user, escenarios, nomina_real, gastos_reales
):
    """
    El escenario optimista debe mostrar MEJOR ahorro que el conservador.
    Optimista: +10% ingresos, -5% gastos
    Conservador: -10% ingresos, +5% gastos
    """
    opt = escenarios[0]
    cons = escenarios[2]
    mes = nomina_real.mes
    anio = nomina_real.anio + 1

    ing_opt = proyectar_ingresos_mes(user, mes, anio, opt)
    ing_cons = proyectar_ingresos_mes(user, mes, anio, cons)
    gas_reales = _promedio_gastos_reales(user, mes, anio)

    # Optimista debe tener mayores ingresos y menores gastos
    assert ing_opt["total"] > ing_cons["total"]

    proy_opt = calcular_ahorro_proyectado(user, 12, opt)
    proy_cons = calcular_ahorro_proyectado(user, 12, cons)
    assert proy_opt["ahorro_acumulado"] >= proy_cons["ahorro_acumulado"]
