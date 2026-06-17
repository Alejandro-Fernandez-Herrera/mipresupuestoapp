import pytest
from decimal import Decimal
from datetime import date
from apps.deudas.services import (
    calcular_cuota_minima,
    calcular_intereses_tc,
    obtener_semaforo_uso,
    calcular_disponible,
    calcular_dias_proximo_corte,
    calcular_pago_diferido,
)
from tests.conftest import assert_cop


class TestCalcularCuotaMinima:
    def test_saldo_cero(self):
        assert calcular_cuota_minima(Decimal('0'), Decimal('0.05')) == Decimal('0')

    def test_cuota_minima_5pct(self):
        cuota = calcular_cuota_minima(Decimal('1500000'), Decimal('0.05'))
        assert cuota == Decimal('75000')

    def test_cuota_minima_10pct(self):
        cuota = calcular_cuota_minima(Decimal('2000000'), Decimal('0.10'))
        assert cuota == Decimal('200000')

    def test_cuota_minima_saldo_grande(self):
        cuota = calcular_cuota_minima(Decimal('10000000'), Decimal('0.05'))
        assert cuota == Decimal('500000')


class TestCalcularInteresesTC:
    def test_saldo_cero(self):
        assert calcular_intereses_tc(Decimal('0'), Decimal('0.0234')) == Decimal('0')

    def test_tasa_cero(self):
        assert calcular_intereses_tc(Decimal('1500000'), Decimal('0')) == Decimal('0')

    def test_intereses_mensuales_tipicos(self):
        intereses = calcular_intereses_tc(Decimal('1500000'), Decimal('0.0234'))
        esperado = Decimal('35100')
        assert_cop(intereses, esperado, Decimal('1'), etiqueta="intereses_tc")

    def test_intereses_saldo_grande(self):
        intereses = calcular_intereses_tc(Decimal('5000000'), Decimal('0.03'))
        esperado = Decimal('150000')
        assert_cop(intereses, esperado, Decimal('1'), etiqueta="intereses_grandes")


class TestObtenerSemaforoUso:
    def test_verde_30pct(self):
        sem = obtener_semaforo_uso(Decimal('30'))
        assert sem['nivel'] == 'verde'

    def test_verde_59pct(self):
        sem = obtener_semaforo_uso(Decimal('59'))
        assert sem['nivel'] == 'verde'

    def test_amarillo_60pct(self):
        sem = obtener_semaforo_uso(Decimal('60'))
        assert sem['nivel'] == 'amarillo'

    def test_amarillo_75pct(self):
        sem = obtener_semaforo_uso(Decimal('75'))
        assert sem['nivel'] == 'amarillo'

    def test_rojo_81pct(self):
        sem = obtener_semaforo_uso(Decimal('81'))
        assert sem['nivel'] == 'rojo'

    def test_rojo_100pct(self):
        sem = obtener_semaforo_uso(Decimal('100'))
        assert sem['nivel'] == 'rojo'

    def test_colores_presentes(self):
        for pct, esperado in [(30, 'verde'), (70, 'amarillo'), (90, 'rojo')]:
            sem = obtener_semaforo_uso(Decimal(pct))
            assert 'color' in sem
            assert sem['nivel'] == esperado


class TestCalcularDisponible:
    def test_disponible_positivo(self):
        disp = calcular_disponible(Decimal('5000000'), Decimal('1500000'))
        assert disp == Decimal('3500000')

    def test_saldo_igual_limite(self):
        disp = calcular_disponible(Decimal('3000000'), Decimal('3000000'))
        assert disp == Decimal('0')

    def test_saldo_excede_limite(self):
        disp = calcular_disponible(Decimal('3000000'), Decimal('3500000'))
        assert disp == Decimal('0')

    def test_saldo_cero(self):
        disp = calcular_disponible(Decimal('5000000'), Decimal('0'))
        assert disp == Decimal('5000000')


class TestCalcularDiasProximoCorte:
    def test_corte_mismo_mes(self):
        hoy = date(2025, 6, 10)
        dias = calcular_dias_proximo_corte(20, referencia=hoy)
        assert dias == 10

    def test_corte_mes_siguiente(self):
        hoy = date(2025, 6, 25)
        dias = calcular_dias_proximo_corte(10, referencia=hoy)
        assert dias > 0
        assert dias <= 45

    def test_corte_cambio_anio(self):
        hoy = date(2025, 12, 25)
        dias = calcular_dias_proximo_corte(10, referencia=hoy)
        assert dias > 0

    def test_corte_hoy_mismo(self):
        hoy = date(2025, 6, 20)
        dias = calcular_dias_proximo_corte(20, referencia=hoy)
        # hoy > fecha_corte (20 > 20 = false, so same month)
        # Actually today == 20, so hoy > fecha_corte is False, cort should be this month
        # 20 is not > 20, so mes_corte stays 6, prox_corte = 2025-06-20, dias = 0
        assert dias == 0


class TestCalcularPagoDiferido:
    def test_contado(self):
        assert calcular_pago_diferido(Decimal('250000'), 1) == Decimal('250000')

    def test_tres_cuotas(self):
        cuota = calcular_pago_diferido(Decimal('300000'), 3)
        assert cuota == Decimal('100000')

    def test_doce_cuotas(self):
        cuota = calcular_pago_diferido(Decimal('1200000'), 12)
        assert cuota == Decimal('100000')

    def test_monto_con_centavos(self):
        cuota = calcular_pago_diferido(Decimal('1000000'), 3)
        assert cuota == Decimal('333333')

    def test_cuota_cero(self):
        assert calcular_pago_diferido(Decimal('500000'), 0) == Decimal('0')
