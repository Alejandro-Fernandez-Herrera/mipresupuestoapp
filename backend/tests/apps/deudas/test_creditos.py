import pytest
from decimal import Decimal
from datetime import date
from collections import namedtuple
from apps.deudas.services import (
    calcular_cuota_mensual,
    generar_tabla_amortizacion,
    calcular_interes_total,
    calcular_tasa_mensual,
)
from tests.conftest import assert_cop, CASOS_CREDITO_FRENCH


CreditoMock = namedtuple('CreditoMock', ['capital', 'tasa_ea', 'plazo_meses', 'fecha_desembolso'])


class TestCalcularTasaMensual:
    def test_tasa_cero(self):
        assert calcular_tasa_mensual(Decimal('0')) == Decimal('0')

    def test_tasa_25_ea(self):
        tasa = calcular_tasa_mensual(Decimal('0.25'))
        assert tasa == Decimal('0.018769')

    def test_tasa_18_ea(self):
        tasa = calcular_tasa_mensual(Decimal('0.18'))
        assert tasa == Decimal('0.013888')

    def test_tasa_30_ea(self):
        tasa = calcular_tasa_mensual(Decimal('0.30'))
        assert tasa == Decimal('0.022104')


class TestCalcularCuotaMensual:
    def test_cuota_cero_interes(self):
        cuota = calcular_cuota_mensual(Decimal('12000000'), Decimal('0'), 12)
        assert cuota == Decimal('1000000')

    def test_cuota_datos_pequenos(self):
        cuota = calcular_cuota_mensual(Decimal('100000'), Decimal('0.12'), 6)
        assert cuota > Decimal('0')
        assert cuota < Decimal('100000')


class TestCasosFrench:
    @pytest.mark.parametrize("caso", CASOS_CREDITO_FRENCH,
                             ids=[c["descripcion"] for c in CASOS_CREDITO_FRENCH])
    def test_cuota_mensual(self, caso):
        cuota = calcular_cuota_mensual(**caso["inputs"])
        assert_cop(
            cuota,
            caso["esperado"]["cuota_mensual"],
            tolerancia=caso["tolerancia_cop"],
            etiqueta=f"cuota_mensual — {caso['descripcion']}",
        )

    @pytest.mark.parametrize("caso", CASOS_CREDITO_FRENCH,
                             ids=[c["descripcion"] for c in CASOS_CREDITO_FRENCH])
    def test_interes_total(self, caso):
        if "interes_total" not in caso["esperado"]:
            pytest.skip("Caso sin interes_total definido")
        interes = calcular_interes_total(**caso["inputs"])
        assert_cop(
            interes,
            caso["esperado"]["interes_total"],
            tolerancia=caso["tolerancia_cop"],
            etiqueta=f"interes_total — {caso['descripcion']}",
        )


class TestGenerarTablaAmortizacion:
    def test_tabla_cantidad_cuotas(self):
        credito = CreditoMock(
            capital=Decimal('10000000'),
            tasa_ea=Decimal('0.25'),
            plazo_meses=12,
            fecha_desembolso=date(2025, 1, 15),
        )
        tabla = generar_tabla_amortizacion(credito)
        assert len(tabla) == 12

    def test_tabla_saldo_final_cero(self):
        credito = CreditoMock(
            capital=Decimal('5000000'),
            tasa_ea=Decimal('0.18'),
            plazo_meses=24,
            fecha_desembolso=date(2025, 1, 15),
        )
        tabla = generar_tabla_amortizacion(credito)
        assert tabla[-1]["saldo_capital"] == Decimal('0')

    def test_tabla_suma_capital_amortizado(self):
        credito = CreditoMock(
            capital=Decimal('10000000'),
            tasa_ea=Decimal('0.25'),
            plazo_meses=12,
            fecha_desembolso=date(2025, 1, 15),
        )
        tabla = generar_tabla_amortizacion(credito)
        total_amortizado = sum(f["capital_amortizado"] for f in tabla)
        assert abs(total_amortizado - credito.capital) < Decimal('10')

    def test_tabla_cuota_constante(self):
        credito = CreditoMock(
            capital=Decimal('10000000'),
            tasa_ea=Decimal('0.25'),
            plazo_meses=12,
            fecha_desembolso=date(2025, 1, 15),
        )
        tabla = generar_tabla_amortizacion(credito)
        primera_cuota = tabla[0]["cuota_total"]
        for fila in tabla:
            assert abs(fila["cuota_total"] - primera_cuota) < Decimal('10')
