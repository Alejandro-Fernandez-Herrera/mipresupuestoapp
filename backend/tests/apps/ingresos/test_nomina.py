import pytest
from decimal import Decimal
from apps.ingresos.services import (
    calcular_nomina,
    calcular_prima,
    calcular_cesantias,
    calcular_intereses_cesantias,
    calcular_vacaciones,
    calcular_prestaciones,
)
from tests.conftest import (
    assert_cop,
    PARAMS_COLOMBIA_2025,
    CASOS_NOMINA,
)


class MockConfig:
    """Simula ConfiguracionFiscal para tests sin BD."""
    def __init__(self, params=None):
        p = params or PARAMS_COLOMBIA_2025
        self.smlv = p["smlv"]
        self.auxilio_transporte = p["auxilio_transporte"]
        self.uvt = p["uvt"]
        self.umbral_retencion_uvt = p["umbral_retencion_uvt"]
        self.tasa_salud_empleado = p["tasa_salud_empleado"]
        self.tasa_pension_empleado = p["tasa_pension_empleado"]
        self.umbral_solidaridad_smlv = p["umbral_solidaridad_smlv"]
        self.tasa_solidaridad_4_16 = p["tasa_solidaridad_4_16"]
        self.tasa_solidaridad_16_17 = p["tasa_solidaridad_16_17"]
        self.tasa_solidaridad_17_18 = p["tasa_solidaridad_17_18"]
        self.tasa_solidaridad_18_19 = p["tasa_solidaridad_18_19"]
        self.tasa_solidaridad_19_20 = p["tasa_solidaridad_19_20"]
        self.tasa_solidaridad_mas_20 = p["tasa_solidaridad_mas_20"]
        self.factor_prima_mensual = p["factor_prima_mensual"]
        self.factor_cesantias_mensual = p["factor_cesantias_mensual"]
        self.tasa_intereses_cesantias = p["tasa_intereses_cesantias"]
        self.factor_vacaciones_mensual = p["factor_vacaciones_mensual"]


config = MockConfig()


@pytest.mark.financiero
@pytest.mark.nomina
class TestCalcularNomina:

    def test_salud_correcto(self):
        """4% del salario bruto."""
        resultado = calcular_nomina(Decimal("1423500"), config)
        assert_cop(resultado["deduccion_salud"], Decimal("56940"),
                   tolerancia=Decimal("1"), etiqueta="salud")

    def test_pension_correcto(self):
        """4% del salario bruto."""
        resultado = calcular_nomina(Decimal("1423500"), config)
        assert_cop(resultado["deduccion_pension"], Decimal("56940"),
                   tolerancia=Decimal("1"), etiqueta="pension")

    def test_sin_solidaridad_menor_4_smlv(self):
        """Salario ≤ 4 SMLV no paga fondo de solidaridad."""
        resultado = calcular_nomina(Decimal("5000000"), config)
        assert resultado["deduccion_solidaridad"] == Decimal("0")

    def test_solidaridad_5_smlv(self):
        """Salario > 4 SMLV paga 1% de fondo solidaridad."""
        resultado = calcular_nomina(Decimal("7117500"), config)
        assert_cop(resultado["deduccion_solidaridad"], Decimal("71175"),
                   tolerancia=Decimal("1"), etiqueta="solidaridad")

    def test_auxilio_transporte_aplica(self):
        """Salario ≤ 2 SMLV aplica auxilio de transporte."""
        resultado = calcular_nomina(Decimal("1423500"), config)
        assert resultado["aplica_auxilio"] is True
        assert_cop(resultado["auxilio_transporte"], Decimal("200000"),
                   tolerancia=Decimal("1"), etiqueta="auxilio")

    def test_auxilio_transporte_no_aplica(self):
        """Salario > 2 SMLV no aplica auxilio de transporte."""
        resultado = calcular_nomina(Decimal("5000000"), config)
        assert resultado["aplica_auxilio"] is False
        assert resultado["auxilio_transporte"] == Decimal("0")

    def test_sin_retencion_menor_95_uvt(self):
        """Salario ≤ 95 UVT/mes no paga retención."""
        resultado = calcular_nomina(Decimal("4000000"), config)
        assert resultado["retencion_fuente"] == Decimal("0")

    def test_retencion_mayor_95_uvt(self):
        """Salario > 95 UVT/mes requiere tabla DIAN (None = pendiente)."""
        resultado = calcular_nomina(Decimal("10000000"), config)
        assert resultado["retencion_fuente"] is None

    def test_neto_1_smlv(self):
        """1 SMLV: bruto - salud - pension + auxilio."""
        resultado = calcular_nomina(Decimal("1423500"), config)
        esperado_neto = Decimal("1309620")
        assert_cop(resultado["salario_neto"], esperado_neto,
                   tolerancia=Decimal("1"), etiqueta="salario_neto")
        esperado_total = esperado_neto + Decimal("200000")
        assert_cop(resultado["neto_con_auxilio"], esperado_total,
                   tolerancia=Decimal("1"), etiqueta="neto_con_auxilio")

    def test_neto_3_smlv(self):
        """3 SMLV: sin solidaridad, sin retención, sin auxilio."""
        resultado = calcular_nomina(Decimal("4270500"), config)
        esperado = Decimal("3928860")
        assert_cop(resultado["salario_neto"], esperado,
                   tolerancia=Decimal("1"), etiqueta="salario_neto")

    def test_neto_5_smlv(self):
        """5 SMLV: con solidaridad 1%."""
        resultado = calcular_nomina(Decimal("7117500"), config)
        esperado = Decimal("6476925")
        assert_cop(resultado["salario_neto"], esperado,
                   tolerancia=Decimal("1"), etiqueta="salario_neto")

    def test_casos_nomina(self, caso_nomina):
        """Valida todos los casos parametrizados de nómina."""
        if caso_nomina.get("incompleto"):
            pytest.xfail("Caso incompleto — pendiente validación externa")

        salario = caso_nomina["inputs"]["salario_bruto"]
        resultado = calcular_nomina(salario, config)

        for campo, valor_esperado in caso_nomina["esperado"].items():
            valor_actual = resultado[campo]
            if isinstance(valor_esperado, Decimal):
                if valor_actual is None:
                    continue
                assert_cop(valor_actual, valor_esperado,
                           tolerancia=Decimal("100"), etiqueta=campo)
            elif isinstance(valor_esperado, bool):
                assert valor_actual == valor_esperado, (
                    f"Campo {campo}: esperado {valor_esperado}, obtenido {valor_actual}"
                )


@pytest.mark.financiero
@pytest.mark.nomina
class TestPrestaciones:

    def test_prima_mensual(self):
        """8.33% mensual del salario base."""
        prima_mensual = calcular_prima(Decimal("1423500"), 1, config)
        esperado = Decimal("118578")
        assert_cop(prima_mensual, esperado, tolerancia=Decimal("100"),
                   etiqueta="prima_mensual")

    def test_prima_semestral(self):
        """Prima de 6 meses."""
        prima = calcular_prima(Decimal("1423500"), 6, config)
        esperado = Decimal("711468")  # 118578 × 6
        assert_cop(prima, esperado, tolerancia=Decimal("500"),
                   etiqueta="prima_semestral")

    def test_cesantias_mensual(self):
        """8.33% mensual del salario base."""
        cesantias = calcular_cesantias(Decimal("1423500"), 1, config)
        esperado = Decimal("118578")
        assert_cop(cesantias, esperado, tolerancia=Decimal("100"),
                   etiqueta="cesantias_mensual")

    def test_cesantias_anuales(self):
        """Cesantías de 12 meses."""
        cesantias = calcular_cesantias(Decimal("3000000"), 12, config)
        esperado = Decimal("2998800")  # 3M × 0.0833 × 12
        assert_cop(cesantias, esperado, tolerancia=Decimal("500"),
                   etiqueta="cesantias_anuales")

    def test_intereses_cesantias(self):
        """12% anual sobre cesantías acumuladas."""
        cesantias = calcular_cesantias(Decimal("1423500"), 12, config)
        intereses = calcular_intereses_cesantias(cesantias, 12, config)
        esperado = Decimal("170718")  # 12% × cesantías × 12/12
        assert_cop(intereses, esperado, tolerancia=Decimal("500"),
                   etiqueta="intereses_cesantias")

    def test_vacaciones_mensual(self):
        """4.17% mensual del salario base."""
        vacaciones = calcular_vacaciones(Decimal("1423500"), config)
        esperado = Decimal("59360")
        assert_cop(vacaciones, esperado, tolerancia=Decimal("100"),
                   etiqueta="vacaciones_mensual")

    def test_prestaciones_completas(self):
        """Calcula todas las prestaciones de una vez."""
        resultado = calcular_prestaciones(Decimal("1423500"), 12, config)
        assert "prima_servicios" in resultado
        assert "cesantias" in resultado
        assert "intereses_cesantias" in resultado
        assert "vacaciones" in resultado
        assert resultado["prima_servicios"]["monto"] > 0
        assert resultado["cesantias"]["monto"] > 0
        assert resultado["intereses_cesantias"]["monto"] > 0
        assert resultado["vacaciones"]["monto_mensual"] > 0
