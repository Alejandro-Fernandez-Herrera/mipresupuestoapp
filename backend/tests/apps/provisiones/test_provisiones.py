import pytest
from decimal import Decimal
from datetime import date
from apps.provisiones.services import (
    calcular_meses_restantes,
    calcular_ahorro_mensual_recomendado,
    calcular_ahorro_maximo_alcanzable,
    calcular_progreso,
    evaluar_alcanzabilidad,
    chequear_recordatorio,
    PROVISIONES_SUGERIDAS,
)
from tests.conftest import assert_cop, CASOS_PROVISION


class TestCalcularMesesRestantes:
    def test_fecha_pasada(self):
        hoy = date(2025, 6, 17)
        assert calcular_meses_restantes(date(2025, 1, 15), referencia=hoy) == 0

    def test_mismo_mes(self):
        hoy = date(2025, 6, 17)
        assert calcular_meses_restantes(date(2025, 6, 25), referencia=hoy) == 1

    def test_un_mes(self):
        hoy = date(2025, 6, 17)
        assert calcular_meses_restantes(date(2025, 7, 17), referencia=hoy) == 1

    def test_seis_meses(self):
        hoy = date(2025, 6, 17)
        assert calcular_meses_restantes(date(2025, 12, 17), referencia=hoy) == 6

    def test_doce_meses(self):
        hoy = date(2025, 6, 17)
        assert calcular_meses_restantes(date(2026, 6, 17), referencia=hoy) == 12

    def test_frontera_dias(self):
        hoy = date(2025, 6, 17)
        assert calcular_meses_restantes(date(2025, 7, 16), referencia=hoy) == 1
        assert calcular_meses_restantes(date(2025, 7, 18), referencia=hoy) == 2
        assert calcular_meses_restantes(date(2025, 7, 17), referencia=hoy) == 1


class TestCalcularAhorroMensualRecomendado:
    def test_sin_acumulado(self):
        rec = calcular_ahorro_mensual_recomendado(Decimal('250000'), Decimal('0'), 5)
        assert rec == Decimal('50000')

    def test_con_acumulado(self):
        rec = calcular_ahorro_mensual_recomendado(Decimal('1800000'), Decimal('600000'), 6)
        assert rec == Decimal('200000')

    def test_meses_cero(self):
        rec = calcular_ahorro_mensual_recomendado(Decimal('250000'), Decimal('50000'), 0)
        assert rec == Decimal('0')

    def test_ya_alcanzado(self):
        rec = calcular_ahorro_mensual_recomendado(Decimal('250000'), Decimal('250000'), 5)
        assert rec == Decimal('0')

    def test_monto_grande(self):
        rec = calcular_ahorro_mensual_recomendado(Decimal('3000000'), Decimal('100000'), 3)
        esperado = Decimal('966667')
        assert_cop(rec, esperado, Decimal('1'), etiqueta="ahorro_recomendado")


class TestCalcularAhorroMaximoAlcanzable:
    def test_maximo_basico(self):
        maximo = calcular_ahorro_maximo_alcanzable(Decimal('60000'), 4)
        assert maximo == Decimal('240000')

    def test_maximo_cero(self):
        maximo = calcular_ahorro_maximo_alcanzable(Decimal('250000'), 0)
        assert maximo == Decimal('0')

    def test_maximo_grande(self):
        maximo = calcular_ahorro_maximo_alcanzable(Decimal('150000'), 10)
        assert maximo == Decimal('1500000')


class TestCalcularProgreso:
    def test_mitad(self):
        pct = calcular_progreso(Decimal('125000'), Decimal('250000'))
        assert pct == Decimal('50.00')

    def test_completado(self):
        pct = calcular_progreso(Decimal('250000'), Decimal('250000'))
        assert pct == Decimal('100')

    def test_excede_meta(self):
        pct = calcular_progreso(Decimal('300000'), Decimal('250000'))
        assert pct == Decimal('100')

    def test_cero(self):
        pct = calcular_progreso(Decimal('0'), Decimal('250000'))
        assert pct == Decimal('0')

    def test_meta_cero(self):
        pct = calcular_progreso(Decimal('50000'), Decimal('0'))
        assert pct == Decimal('100')


class TestEvaluarAlcanzabilidad:
    def test_alcanza_con_margen(self):
        alcanza, deficit = evaluar_alcanzabilidad(
            Decimal('600000'), Decimal('1500000'), Decimal('1800000')
        )
        assert alcanza is True
        assert deficit == Decimal('0')

    def test_no_alcanza(self):
        alcanza, _ = evaluar_alcanzabilidad(
            Decimal('50000'), Decimal('190000'), Decimal('250000')
        )
        assert alcanza is False

    def test_deficit_correcto(self):
        _, deficit = evaluar_alcanzabilidad(
            Decimal('50000'), Decimal('190000'), Decimal('250000')
        )
        assert deficit == Decimal('10000')

    def test_exacto(self):
        alcanza, deficit = evaluar_alcanzabilidad(
            Decimal('100000'), Decimal('200000'), Decimal('300000')
        )
        assert alcanza is True
        assert deficit == Decimal('0')

    def test_ya_alcanzado(self):
        alcanza, _ = evaluar_alcanzabilidad(
            Decimal('300000'), Decimal('0'), Decimal('250000')
        )
        assert alcanza is True


class TestChequearRecordatorio:
    def test_no_alerta_fecha_lejana(self):
        from datetime import date as dt
        from dateutil.relativedelta import relativedelta
        hoy = dt.today()
        fecha_lejana = hoy + relativedelta(months=6)
        assert chequear_recordatorio(fecha_lejana, Decimal('50')) is False

    def test_alerta_por_vencer_progreso_bajo(self):
        from datetime import date as dt
        hoy = dt.today()
        from dateutil.relativedelta import relativedelta
        fecha_prox = hoy + relativedelta(months=1)
        assert chequear_recordatorio(fecha_prox, Decimal('50')) is True

    def test_alerta_fecha_cercana_progreso_alto(self):
        from datetime import date as dt
        hoy = dt.today()
        from dateutil.relativedelta import relativedelta
        fecha_prox = hoy + relativedelta(months=1)
        assert chequear_recordatorio(fecha_prox, Decimal('90')) is False


class TestCasosProvision:
    @pytest.mark.parametrize("caso", CASOS_PROVISION,
                             ids=[c["descripcion"] for c in CASOS_PROVISION])
    def test_caso_provision(self, caso):
        monto_total = caso["inputs"]["monto_total"]
        ahorro_acum = caso["inputs"]["ahorro_acumulado"]
        meses_rest = caso["inputs"]["meses_restantes"]
        disponible = caso["inputs"]["ahorro_mensual_disponible"]

        rec = calcular_ahorro_mensual_recomendado(monto_total, ahorro_acum, meses_rest)
        maximo = calcular_ahorro_maximo_alcanzable(disponible, meses_rest)
        alcanza, deficit = evaluar_alcanzabilidad(ahorro_acum, maximo, monto_total)
        progreso = calcular_progreso(ahorro_acum, monto_total)

        e = caso["esperado"]
        tolerancia = Decimal('1')

        assert_cop(rec, e["ahorro_mensual_recomendado"], tolerancia,
                   etiqueta="ahorro_mensual_recomendado")
        assert_cop(maximo, e["ahorro_maximo_alcanzable"], tolerancia,
                   etiqueta="ahorro_maximo_alcanzable")
        assert alcanza is e["alcanza_meta"], f"alcanza_meta: esperado {e['alcanza_meta']}"
        assert_cop(deficit, e["deficit"], tolerancia, etiqueta="deficit")
        assert_cop(progreso, e["porcentaje_progreso"], Decimal('0.01'),
                   etiqueta="porcentaje_progreso")


class TestProvisionesSugeridas:
    def test_catalogo_tiene_17_items(self):
        assert len(PROVISIONES_SUGERIDAS) == 17

    def test_catalogo_tiene_campos_requeridos(self):
        for item in PROVISIONES_SUGERIDAS:
            assert "concepto" in item
            assert "monto_total" in item
            assert "fecha_pago_dia" in item
            assert "fecha_pago_mes" in item
            assert "categoria" in item

    def test_catalogo_conceptos_son_unicos(self):
        conceptos = [p["concepto"] for p in PROVISIONES_SUGERIDAS]
        assert len(conceptos) == len(set(conceptos))

    def test_catalogo_montos_positivos(self):
        for item in PROVISIONES_SUGERIDAS:
            assert item["monto_total"] > 0, f"'{item['concepto']}' tiene monto 0 o negativo"

    def test_catalogo_dias_validos(self):
        for item in PROVISIONES_SUGERIDAS:
            assert 1 <= item["fecha_pago_dia"] <= 31
            assert 1 <= item["fecha_pago_mes"] <= 31
