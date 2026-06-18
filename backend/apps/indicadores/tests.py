import pytest
from decimal import Decimal
from apps.indicadores import services
from apps.indicadores.services import (
    calcular_ratio_endeudamiento,
    calcular_tasa_ahorro,
    calcular_cobertura_emergencia,
    calcular_presion_gastos_fijos,
    generar_diagnostico,
)


@pytest.mark.financiero
@pytest.mark.indicadores
class TestRatioEndeudamiento:

    def test_caso_sano(self):
        resultado = calcular_ratio_endeudamiento(
            ingreso_neto=Decimal('4000000'),
            total_cuotas_creditos=Decimal('500000'),
            minimos_tarjetas=Decimal('100000'),
        )
        assert resultado['valor'] == Decimal('15.00')
        assert resultado['semaforo'] == 'verde'

    def test_caso_deuda_alta(self):
        resultado = calcular_ratio_endeudamiento(
            ingreso_neto=Decimal('3000000'),
            total_cuotas_creditos=Decimal('1000000'),
            minimos_tarjetas=Decimal('300000'),
        )
        assert resultado['valor'] == Decimal('43.33')
        assert resultado['semaforo'] == 'rojo'

    def test_caso_zona_amarilla(self):
        resultado = calcular_ratio_endeudamiento(
            ingreso_neto=Decimal('3500000'),
            total_cuotas_creditos=Decimal('700000'),
            minimos_tarjetas=Decimal('200000'),
        )
        assert resultado['valor'] == Decimal('25.71')
        assert resultado['semaforo'] == 'verde'

    def test_sin_ingresos(self):
        resultado = calcular_ratio_endeudamiento(
            ingreso_neto=Decimal('0'),
            total_cuotas_creditos=Decimal('500000'),
            minimos_tarjetas=Decimal('0'),
        )
        assert resultado['valor'] == Decimal('0')
        assert resultado['semaforo'] == 'verde'

    def test_sin_deuda(self):
        resultado = calcular_ratio_endeudamiento(
            ingreso_neto=Decimal('4000000'),
            total_cuotas_creditos=Decimal('0'),
            minimos_tarjetas=Decimal('0'),
        )
        assert resultado['valor'] == Decimal('0')
        assert resultado['semaforo'] == 'verde'


@pytest.mark.financiero
@pytest.mark.indicadores
class TestTasaAhorro:

    def test_caso_sano(self):
        resultado = calcular_tasa_ahorro(
            ahorro_neto=Decimal('800000'),
            ingreso_neto=Decimal('4000000'),
        )
        assert resultado['valor'] == Decimal('20.00')
        assert resultado['semaforo'] == 'verde'

    def test_caso_rojo(self):
        resultado = calcular_tasa_ahorro(
            ahorro_neto=Decimal('200000'),
            ingreso_neto=Decimal('3000000'),
        )
        assert resultado['valor'] == Decimal('6.67')
        assert resultado['semaforo'] == 'rojo'

    def test_caso_amarillo(self):
        resultado = calcular_tasa_ahorro(
            ahorro_neto=Decimal('420000'),
            ingreso_neto=Decimal('3500000'),
        )
        assert resultado['valor'] == Decimal('12.00')
        assert resultado['semaforo'] == 'amarillo'

    def test_meta_personalizada(self):
        resultado = calcular_tasa_ahorro(
            ahorro_neto=Decimal('500000'),
            ingreso_neto=Decimal('5000000'),
            meta=Decimal('15'),
        )
        assert resultado['valor'] == Decimal('10.00')
        assert resultado['semaforo'] == 'amarillo'

    def test_sin_ingresos(self):
        resultado = calcular_tasa_ahorro(
            ahorro_neto=Decimal('0'),
            ingreso_neto=Decimal('0'),
        )
        assert resultado['valor'] == Decimal('0')
        assert resultado['semaforo'] == 'verde'


@pytest.mark.financiero
@pytest.mark.indicadores
class TestCoberturaEmergencia:

    def test_caso_sano(self):
        resultado = calcular_cobertura_emergencia(
            saldo_fondo=Decimal('6000000'),
            gasto_esencial_mensual=Decimal('2000000'),
        )
        assert resultado['valor'] == Decimal('3.00')
        assert resultado['semaforo'] == 'verde'

    def test_caso_rojo(self):
        resultado = calcular_cobertura_emergencia(
            saldo_fondo=Decimal('500000'),
            gasto_esencial_mensual=Decimal('2000000'),
        )
        assert resultado['valor'] == Decimal('0.25')
        assert resultado['semaforo'] == 'rojo'

    def test_caso_amarillo(self):
        resultado = calcular_cobertura_emergencia(
            saldo_fondo=Decimal('3500000'),
            gasto_esencial_mensual=Decimal('2000000'),
        )
        assert resultado['valor'] == Decimal('1.75')
        assert resultado['semaforo'] == 'amarillo'

    def test_sin_gasto_esencial(self):
        resultado = calcular_cobertura_emergencia(
            saldo_fondo=Decimal('5000000'),
            gasto_esencial_mensual=Decimal('0'),
        )
        assert resultado['valor'] == Decimal('0')
        assert resultado['semaforo'] == 'verde'


@pytest.mark.financiero
@pytest.mark.indicadores
class TestPresionGastosFijos:

    def test_caso_sano(self):
        resultado = calcular_presion_gastos_fijos(
            gastos_fijos=Decimal('1800000'),
            ingreso_neto=Decimal('4000000'),
        )
        assert resultado == Decimal('45.00')

    def test_sin_ingresos(self):
        resultado = calcular_presion_gastos_fijos(
            gastos_fijos=Decimal('1000000'),
            ingreso_neto=Decimal('0'),
        )
        assert resultado == Decimal('0')

    def test_sin_gastos_fijos(self):
        resultado = calcular_presion_gastos_fijos(
            gastos_fijos=Decimal('0'),
            ingreso_neto=Decimal('5000000'),
        )
        assert resultado == Decimal('0')


@pytest.mark.financiero
@pytest.mark.indicadores
class TestDiagnostico:

    def test_salud_estable(self):
        indicadores = {
            'tasa_ahorro': Decimal('25'),
            'presion_gastos_fijos': Decimal('30'),
            'cobertura_emergencia': Decimal('5'),
            'ratio_endeudamiento': Decimal('15'),
        }
        resultado = generar_diagnostico(indicadores)
        assert resultado == "Salud financiera estable. Sigue así."

    def test_tasa_ahorro_critica(self):
        indicadores = {
            'tasa_ahorro': Decimal('5'),
            'presion_gastos_fijos': Decimal('30'),
            'cobertura_emergencia': Decimal('5'),
            'ratio_endeudamiento': Decimal('15'),
        }
        resultado = generar_diagnostico(indicadores)
        assert "crítica" in resultado.lower()

    def test_ratio_endeudamiento_alto(self):
        indicadores = {
            'tasa_ahorro': Decimal('25'),
            'presion_gastos_fijos': Decimal('30'),
            'cobertura_emergencia': Decimal('5'),
            'ratio_endeudamiento': Decimal('50'),
        }
        resultado = generar_diagnostico(indicadores)
        assert "endeudamiento" in resultado.lower()
