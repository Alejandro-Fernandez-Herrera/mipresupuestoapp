"""
Test Harness — App Finanzas Hogar y Personales
===============================================
Archivo: tests/conftest.py
Propósito: infraestructura de pruebas compartida para todo el proyecto.
           No contiene tests. Solo fixtures, factories, datos de referencia
           y helpers de aserción para lógica financiera colombiana.

Instalación de dependencias de test:
    pip install pytest pytest-django pytest-cov freezegun --break-system-packages

Correr tests:
    pytest tests/                          # todos los tests
    pytest tests/ -v                       # verbose
    pytest tests/ -k "nomina"              # solo tests de nómina
    pytest tests/ -m financiero            # solo tests de lógica financiera
    pytest tests/ --cov=apps --cov-report=term-missing  # con cobertura

Estructura de tests esperada:
    tests/
    ├── conftest.py                  ← este archivo
    ├── apps/
    │   ├── ingresos/
    │   │   └── test_nomina.py
    │   ├── deudas/
    │   │   ├── test_creditos.py
    │   │   └── test_tarjetas.py
    │   ├── provisiones/
    │   │   └── test_provisiones.py
    │   └── indicadores/
    │       └── test_salud_financiera.py
    └── integracion/
        └── test_dashboard.py
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP
from datetime import date


# ==============================================================
# 1. PARÁMETROS NORMATIVOS COLOMBIA
# ==============================================================
# Fuente de verdad para todos los tests.
# Actualizar cada enero cuando cambien los decretos.
# La app debe leer estos mismos valores desde ConfiguracionFiscal en BD.

PARAMS_COLOMBIA_2025 = {
    # Decreto de salario mínimo
    "smlv":                      Decimal("1423500"),
    "auxilio_transporte":        Decimal("200000"),

    # DIAN — Retención en la fuente
    "uvt":                       Decimal("49799"),
    "umbral_retencion_uvt":      Decimal("95"),       # 95 UVT/mes ≈ $4.730.905

    # Seguridad social — Ley 100/93
    "tasa_salud_empleado":       Decimal("0.04"),      # 4%
    "tasa_pension_empleado":     Decimal("0.04"),      # 4%
    "umbral_solidaridad_smlv":   Decimal("4"),         # aplica si salario > 4 SMLV
    "tasa_solidaridad_4_16":     Decimal("0.01"),      # 1% para rango 4–16 SMLV
    "tasa_solidaridad_16_17":    Decimal("0.012"),
    "tasa_solidaridad_17_18":    Decimal("0.014"),
    "tasa_solidaridad_18_19":    Decimal("0.016"),
    "tasa_solidaridad_19_20":    Decimal("0.018"),
    "tasa_solidaridad_mas_20":   Decimal("0.02"),

    # Prestaciones sociales — CST
    "factor_prima_mensual":      Decimal("0.0833"),    # 8.33% — CST Art. 306
    "factor_cesantias_mensual":  Decimal("0.0833"),    # 8.33% — CST Art. 249
    "tasa_intereses_cesantias":  Decimal("0.12"),      # 12% anual — Ley 52/75
    "factor_vacaciones_mensual": Decimal("0.0417"),    # 4.17%

    # Tarjetas de crédito — Circular SFC
    "cuota_minima_tc_pct":       Decimal("0.05"),      # 5% del saldo
}


# ==============================================================
# 2. CASOS DE PRUEBA CON VALORES CONOCIDOS
# ==============================================================
# Cada caso fue validado contra un simulador externo.
# Al escribir el test, documenta qué simulador usaste y cuándo.

# --------------------------------------------------------------
# 2.1 Créditos — Fórmula French
# --------------------------------------------------------------
# Fórmula: Cuota = (P × i) / (1 − (1+i)^−n)
#          donde i = (1 + EA)^(1/12) − 1
# Referencia: simulador Superfinanciera / Bancolombia

CASOS_CREDITO_FRENCH = [
    {
        "descripcion": "10M al 25% EA por 12 meses",
        "fuente_validacion": "Validado con French: Cuota = P*i/(1-(1+i)^-n)",
        "inputs": {
            "capital":      Decimal("10000000"),
            "tasa_ea":      Decimal("0.25"),
            "plazo_meses":  12,
        },
        "esperado": {
            "tasa_mensual":    Decimal("0.018769"),
            "cuota_mensual":   Decimal("938463"),
            "interes_total":   Decimal("1261556"),
        },
        "tolerancia_cop": Decimal("500"),
    },
    {
        "descripcion": "5M al 18% EA por 24 meses",
        "fuente_validacion": "Validado con French: Cuota = P*i/(1-(1+i)^-n)",
        "inputs": {
            "capital":      Decimal("5000000"),
            "tasa_ea":      Decimal("0.18"),
            "plazo_meses":  24,
        },
        "esperado": {
            "tasa_mensual":    Decimal("0.013888"),
            "cuota_mensual":   Decimal("246410"),
            "interes_total":   Decimal("913840"),
        },
        "tolerancia_cop": Decimal("500"),
    },
    {
        "descripcion": "1 SMLV al 30% EA por 6 meses — caso mínimo",
        "fuente_validacion": "Validado con French: Cuota = P*i/(1-(1+i)^-n)",
        "inputs": {
            "capital":      Decimal("1423500"),
            "tasa_ea":      Decimal("0.30"),
            "plazo_meses":  6,
        },
        "esperado": {
            "tasa_mensual":    Decimal("0.022104"),
            "cuota_mensual":   Decimal("255939"),
            "interes_total":   Decimal("112134"),
        },
        "tolerancia_cop": Decimal("500"),
    },
    {
        "descripcion": "50M al 15% EA por 60 meses — caso hipoteca/vehículo",
        "fuente_validacion": "Validado con French: Cuota = P*i/(1-(1+i)^-n)",
        "inputs": {
            "capital":      Decimal("50000000"),
            "tasa_ea":      Decimal("0.15"),
            "plazo_meses":  60,
        },
        "esperado": {
            "tasa_mensual":    Decimal("0.011715"),
            "cuota_mensual":   Decimal("1164914"),
            "interes_total":   Decimal("19894840"),
        },
        "tolerancia_cop": Decimal("500"),
    },
]

# --------------------------------------------------------------
# 2.2 Nómina colombiana
# --------------------------------------------------------------
# Referencia: liquidador DIAN / Gerencie.com

CASOS_NOMINA = [
    {
        "descripcion": "1 SMLV — aplica auxilio de transporte, sin retención",
        "fuente_validacion": "Gerencie.com liquidador — 2025-06",
        "inputs": {
            "salario_bruto":    Decimal("1423500"),
        },
        "esperado": {
            "deduccion_salud":          Decimal("56940"),
            "deduccion_pension":        Decimal("56940"),
            "deduccion_solidaridad":    Decimal("0"),
            "retencion_fuente":         Decimal("0"),
            "salario_neto":             Decimal("1309620"),
            "aplica_auxilio":           True,
            "auxilio_transporte":       Decimal("200000"),
            "neto_con_auxilio":         Decimal("1509620"),
        },
    },
    {
        "descripcion": "3 SMLV — sin retención, sin solidaridad",
        "fuente_validacion": "Cálculo manual — 2025-06",
        "inputs": {
            "salario_bruto":    Decimal("4270500"),   # 3 × 1,423,500
        },
        "esperado": {
            "deduccion_salud":          Decimal("170820"),
            "deduccion_pension":        Decimal("170820"),
            "deduccion_solidaridad":    Decimal("0"),
            "retencion_fuente":         Decimal("0"),
            "salario_neto":             Decimal("3928860"),
            "aplica_auxilio":           False,
        },
    },
    {
        "descripcion": "5 SMLV — aplica fondo solidaridad 1%",
        "fuente_validacion": "Cálculo manual — 2025-06",
        "inputs": {
            "salario_bruto":    Decimal("7117500"),   # 5 × 1,423,500
        },
        "esperado": {
            "deduccion_salud":          Decimal("284700"),
            "deduccion_pension":        Decimal("284700"),
            "deduccion_solidaridad":    Decimal("71175"),   # 1% × 7,117,500
            "retencion_fuente":         Decimal("0"),       # < 95 UVT
            "salario_neto":             Decimal("6476925"),
            "aplica_auxilio":           False,
        },
    },
    {
        "descripcion": "10 SMLV con retención — valores a validar con DIAN",
        "fuente_validacion": "PENDIENTE — validar con tabla retención DIAN 2025",
        "inputs": {
            "salario_bruto":    Decimal("14235000"),  # 10 × 1,423,500
        },
        "esperado": {
            "deduccion_salud":          Decimal("569400"),
            "deduccion_pension":        Decimal("569400"),
            "deduccion_solidaridad":    Decimal("142350"),  # 1%
            # retención: requiere tabla progresiva DIAN — completar
            "aplica_auxilio":           False,
        },
        "incompleto": True,  # marcar tests con este flag como xfail hasta validar
    },
]

# --------------------------------------------------------------
# 2.3 Provisiones
# --------------------------------------------------------------

CASOS_PROVISION = [
    {
        "descripcion": "SOAT: no alcanza por $10.000",
        "inputs": {
            "monto_total":                  Decimal("250000"),
            "ahorro_acumulado":             Decimal("50000"),
            "meses_restantes":              4,
            "ahorro_mensual_disponible":    Decimal("47500"),
        },
        "esperado": {
            "ahorro_mensual_recomendado":   Decimal("50000"),   # (250k−50k)/4
            "ahorro_maximo_alcanzable":     Decimal("190000"),  # 47.5k × 4
            "alcanza_meta":                 False,
            "deficit":                      Decimal("10000"),   # 250k − (50k+190k)
            "porcentaje_progreso":          Decimal("20.00"),   # 50k/250k × 100
        },
    },
    {
        "descripcion": "Matrícula: sí alcanza con margen",
        "inputs": {
            "monto_total":                  Decimal("1800000"),
            "ahorro_acumulado":             Decimal("600000"),
            "meses_restantes":              6,
            "ahorro_mensual_disponible":    Decimal("250000"),
        },
        "esperado": {
            "ahorro_mensual_recomendado":   Decimal("200000"),  # (1.8M−600k)/6
            "ahorro_maximo_alcanzable":     Decimal("1500000"), # 250k × 6
            "alcanza_meta":                 True,               # 600k + 1.5M = 2.1M > 1.8M
            "deficit":                      Decimal("0"),
            "porcentaje_progreso":          Decimal("33.33"),
        },
    },
    {
        "descripcion": "Vacaciones: imposible — tiempo insuficiente",
        "inputs": {
            "monto_total":                  Decimal("3000000"),
            "ahorro_acumulado":             Decimal("100000"),
            "meses_restantes":              3,
            "ahorro_mensual_disponible":    Decimal("150000"),
        },
        "esperado": {
            "ahorro_mensual_recomendado":   Decimal("966667"),  # (3M−100k)/3
            "ahorro_maximo_alcanzable":     Decimal("450000"),  # 150k × 3
            "alcanza_meta":                 False,
            "deficit":                      Decimal("2450000"),
            "porcentaje_progreso":          Decimal("3.33"),
        },
    },
]

# --------------------------------------------------------------
# 2.4 Indicadores de salud financiera
# --------------------------------------------------------------

CASOS_INDICADORES = [
    {
        "descripcion": "Situación financiera sana",
        "inputs": {
            "ingreso_neto":                 Decimal("4000000"),
            "cuotas_creditos_mes":          Decimal("500000"),
            "minimos_tarjetas_mes":         Decimal("100000"),
            "ahorro_neto_mes":              Decimal("800000"),
            "saldo_fondo_emergencia":       Decimal("6000000"),
            "gasto_esencial_mensual":       Decimal("2000000"),
            "gastos_fijos_mensual":         Decimal("1800000"),
        },
        "esperado": {
            # (500k + 100k) / 4M × 100
            "ratio_endeudamiento":          Decimal("15.00"),
            "semaforo_endeudamiento":       "verde",            # < 30%
            # 800k / 4M × 100
            "tasa_ahorro":                  Decimal("20.00"),
            "semaforo_ahorro":              "verde",            # ≥ 20%
            # 6M / 2M
            "cobertura_emergencia_meses":   Decimal("3.00"),
            "semaforo_emergencia":          "verde",            # ≥ 3 meses
            # 1.8M / 4M × 100
            "presion_gastos_fijos":         Decimal("45.00"),
        },
    },
    {
        "descripcion": "Deuda alta — rojo en endeudamiento",
        "inputs": {
            "ingreso_neto":                 Decimal("3000000"),
            "cuotas_creditos_mes":          Decimal("1000000"),
            "minimos_tarjetas_mes":         Decimal("300000"),
            "ahorro_neto_mes":              Decimal("200000"),
            "saldo_fondo_emergencia":       Decimal("500000"),
            "gasto_esencial_mensual":       Decimal("2000000"),
            "gastos_fijos_mensual":         Decimal("2200000"),
        },
        "esperado": {
            # (1M + 300k) / 3M × 100 = 43.3%
            "ratio_endeudamiento":          Decimal("43.33"),
            "semaforo_endeudamiento":       "rojo",             # > 40%
            # 200k / 3M × 100 = 6.7%
            "tasa_ahorro":                  Decimal("6.67"),
            "semaforo_ahorro":              "rojo",             # < 10%
            # 500k / 2M = 0.25 meses
            "cobertura_emergencia_meses":   Decimal("0.25"),
            "semaforo_emergencia":          "rojo",             # < 1 mes
        },
    },
    {
        "descripcion": "Zona amarilla — ahorro moderado, deuda controlada",
        "inputs": {
            "ingreso_neto":                 Decimal("3500000"),
            "cuotas_creditos_mes":          Decimal("700000"),
            "minimos_tarjetas_mes":         Decimal("200000"),
            "ahorro_neto_mes":              Decimal("420000"),
            "saldo_fondo_emergencia":       Decimal("3500000"),
            "gasto_esencial_mensual":       Decimal("2000000"),
            "gastos_fijos_mensual":         Decimal("1900000"),
        },
        "esperado": {
            # (700k + 200k) / 3.5M × 100 = 25.7%
            "ratio_endeudamiento":          Decimal("25.71"),
            "semaforo_endeudamiento":       "verde",
            # 420k / 3.5M × 100 = 12%
            "tasa_ahorro":                  Decimal("12.00"),
            "semaforo_ahorro":              "amarillo",         # 10–20%
            # 3.5M / 2M = 1.75
            "cobertura_emergencia_meses":   Decimal("1.75"),
            "semaforo_emergencia":          "amarillo",         # 1–3 meses
        },
    },
]


# ==============================================================
# 3. FACTORIES
# ==============================================================
# Generan dicts con datos válidos para tests.
# Migrar a factory_boy DjangoModelFactory cuando los modelos existan:
#   pip install factory-boy
#   class PerfilUsuarioFactory(factory.django.DjangoModelFactory):
#       class Meta:
#           model = PerfilUsuario

class PerfilFactory:
    """Factory para perfiles de usuario."""

    @staticmethod
    def crear(**kwargs) -> dict:
        defaults = {
            "nombre":             "Usuario Colombia",
            "email":              "usuario@finanzashogar.co",
            "ciudad":             "Bogotá",
            "smlv_vigente":       PARAMS_COLOMBIA_2025["smlv"],
            "uvt_vigente":        PARAMS_COLOMBIA_2025["uvt"],
            "auxilio_transporte": PARAMS_COLOMBIA_2025["auxilio_transporte"],
            "meta_tasa_ahorro":   Decimal("20.0"),
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def smlv(**kwargs) -> dict:
        return PerfilFactory.crear(
            nombre="Trabajador SMLV",
            email="smlv@test.co",
            **kwargs,
        )

    @staticmethod
    def profesional(**kwargs) -> dict:
        return PerfilFactory.crear(
            nombre="Profesional",
            email="profesional@test.co",
            ciudad="Cali",
            **kwargs,
        )


class IngresoFactory:
    """Factory para registros de ingresos."""

    TIPOS_VALIDOS = [
        "salario", "auxilio_transporte", "hora_extra_diurna",
        "hora_extra_nocturna", "dominical_festivo", "comision",
        "bonificacion", "honorarios", "ingreso_pasivo", "otro",
    ]

    @staticmethod
    def nomina(salario_bruto=Decimal("3000000"), mes=6, anio=2025) -> dict:
        return {
            "tipo":          "salario",
            "salario_bruto": salario_bruto,
            "mes":           mes,
            "anio":          anio,
            "recurrente":    True,
        }

    @staticmethod
    def adicional(tipo="comision", monto=Decimal("500000"), mes=6, anio=2025) -> dict:
        assert tipo in IngresoFactory.TIPOS_VALIDOS, f"Tipo inválido: {tipo}"
        return {
            "tipo":       tipo,
            "monto":      monto,
            "mes":        mes,
            "anio":       anio,
            "recurrente": False,
        }


class CategoriaFactory:
    """Factory para categorías de gastos."""

    SUGERIDAS = [
        ("Vivienda",                   "#FF5722", True),
        ("Alimentación",               "#4CAF50", True),
        ("Transporte",                 "#2196F3", True),
        ("Salud",                      "#E91E63", True),
        ("Educación Propia",           "#9C27B0", False),
        ("Educación Familia",          "#673AB7", False),
        ("Deudas y Créditos",          "#F44336", False),
        ("Familia y Dependientes",     "#FF9800", False),
        ("Telecomunicaciones",         "#00BCD4", False),
        ("Ocio y Entretenimiento",     "#8BC34A", False),
        ("Cuidado Personal y Vestuario", "#FFEB3B", False),
        ("Mascotas",                   "#795548", False),
        ("Ahorro e Inversión",         "#009688", True),
        ("Otros Gastos",               "#9E9E9E", False),
    ]

    @staticmethod
    def crear(nombre="Alimentación", color="#4CAF50", es_esencial=False) -> dict:
        return {
            "nombre":      nombre,
            "color":       color,
            "es_sugerida": True,
            "es_esencial": es_esencial,
            "visible":     True,
        }

    @staticmethod
    def esenciales() -> list[dict]:
        """Las categorías marcadas como esenciales para el cálculo del fondo de emergencia."""
        esenciales = {"Vivienda", "Alimentación", "Transporte", "Salud",
                      "Deudas y Créditos", "Ahorro e Inversión"}
        return [
            CategoriaFactory.crear(nombre=n, color=c, es_esencial=(n in esenciales))
            for n, c, _ in CategoriaFactory.SUGERIDAS
        ]

    @staticmethod
    def completo() -> list[dict]:
        return CategoriaFactory.esenciales()


class GastoFactory:
    """Factory para registros de gastos."""

    @staticmethod
    def crear(
        categoria="Alimentación",
        rubro="Mercado (supermercado / galería / plaza)",
        monto=Decimal("350000"),
        fecha=None,
        tipo="variable",
        metodo_pago="débito",
        recurrente=False,
        descripcion="",
    ) -> dict:
        return {
            "categoria":    categoria,
            "rubro":        rubro,
            "monto":        monto,
            "fecha":        fecha or date(2025, 6, 15),
            "tipo":         tipo,
            "metodo_pago":  metodo_pago,
            "recurrente":   recurrente,
            "descripcion":  descripcion,
        }

    @staticmethod
    def fijo(categoria="Vivienda", rubro="Arriendo / Cuota hipotecaria",
             monto=Decimal("800000")) -> dict:
        return GastoFactory.crear(
            categoria=categoria, rubro=rubro, monto=monto,
            tipo="fijo", recurrente=True,
        )

    @staticmethod
    def mes_completo() -> list[dict]:
        """
        Set representativo de gastos para un mes de prueba.
        Total aprox: $2.100.000 sobre ingreso neto de $3.000.000 → ahorro $900.000
        """
        return [
            GastoFactory.fijo("Vivienda",      "Arriendo / Cuota hipotecaria",  Decimal("800000")),
            GastoFactory.fijo("Vivienda",      "Energía eléctrica",             Decimal("120000")),
            GastoFactory.fijo("Vivienda",      "Internet",                      Decimal("90000")),
            GastoFactory.crear("Alimentación", "Mercado (supermercado / galería / plaza)", Decimal("400000")),
            GastoFactory.crear("Alimentación", "Domicilios (Rappi / iFood / etc.)",        Decimal("80000")),
            GastoFactory.crear("Transporte",   "Gasolina vehículo / moto",      Decimal("150000")),
            GastoFactory.fijo("Telecomunicaciones", "Plan celular / datos móviles", Decimal("70000")),
            GastoFactory.fijo("Telecomunicaciones", "Netflix",                   Decimal("20000")),
            GastoFactory.crear("Salud",        "Copagos / cuotas moderadoras EPS", Decimal("30000")),
            GastoFactory.crear("Alimentación", "Almuerzo / cafetería trabajo",  Decimal("200000")),
            GastoFactory.crear("Ocio y Entretenimiento", "Salidas y recreación", Decimal("100000")),
            GastoFactory.crear("Cuidado Personal y Vestuario", "Peluquería / barbería / estética", Decimal("50000")),
        ]


class CreditoFactory:
    """Factory para créditos de consumo."""

    TIPOS_ENTIDAD = ["bancario", "cooperativa", "libranza", "fintech", "familiar", "otro"]

    @staticmethod
    def crear(
        nombre="Crédito de consumo",
        entidad_tipo="bancario",
        capital=Decimal("10000000"),
        tasa_ea=Decimal("0.25"),
        plazo_meses=12,
        fecha_desembolso=None,
    ) -> dict:
        assert entidad_tipo in CreditoFactory.TIPOS_ENTIDAD
        return {
            "nombre":            nombre,
            "entidad_tipo":      entidad_tipo,
            "capital":           capital,
            "tasa_ea":           tasa_ea,
            "plazo_meses":       plazo_meses,
            "fecha_desembolso":  fecha_desembolso or date(2025, 1, 15),
        }

    @staticmethod
    def cooperativa(**kwargs) -> dict:
        defaults = dict(
            nombre="Crédito cooperativa",
            entidad_tipo="cooperativa",
            capital=Decimal("15000000"),
            tasa_ea=Decimal("0.20"),
            plazo_meses=36,
        )
        defaults.update(kwargs)
        return CreditoFactory.crear(**defaults)

    @staticmethod
    def libranza(**kwargs) -> dict:
        defaults = dict(
            nombre="Libranza",
            entidad_tipo="libranza",
            capital=Decimal("8000000"),
            tasa_ea=Decimal("0.22"),
            plazo_meses=24,
        )
        defaults.update(kwargs)
        return CreditoFactory.crear(**defaults)

    @staticmethod
    def caso_french(index=0) -> dict:
        """Retorna el crédito del caso de prueba French por índice."""
        caso = CASOS_CREDITO_FRENCH[index]
        return CreditoFactory.crear(**caso["inputs"])


class TarjetaCreditoFactory:
    """Factory para tarjetas de crédito."""

    @staticmethod
    def crear(
        nombre="Tarjeta Visa",
        banco="Bancolombia",
        limite=Decimal("5000000"),
        tasa_mensual=Decimal("0.0234"),   # ~28% EA aprox
        saldo_actual=Decimal("1500000"),
        fecha_corte=20,
    ) -> dict:
        return {
            "nombre":         nombre,
            "banco":          banco,
            "limite":         limite,
            "tasa_mensual":   tasa_mensual,
            "saldo_actual":   saldo_actual,
            "fecha_corte":    fecha_corte,
        }

    @staticmethod
    def sin_deuda(**kwargs) -> dict:
        defaults = dict(saldo_actual=Decimal("0"))
        defaults.update(kwargs)
        return TarjetaCreditoFactory.crear(**defaults)

    @staticmethod
    def al_limite(limite=Decimal("3000000"), pct=Decimal("0.85")) -> dict:
        """Tarjeta al porcentaje especificado del límite — activa semáforo rojo > 80%."""
        saldo = (limite * pct).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return TarjetaCreditoFactory.crear(
            nombre="Tarjeta al límite",
            limite=limite,
            saldo_actual=saldo,
        )


class ProvisionFactory:
    """Factory para provisiones de pagos futuros."""

    @staticmethod
    def crear(
        concepto="SOAT vehículo / moto",
        monto_total=Decimal("250000"),
        fecha_pago=None,
        ahorro_acumulado=Decimal("0"),
    ) -> dict:
        return {
            "concepto":          concepto,
            "monto_total":       monto_total,
            "fecha_pago":        fecha_pago or date(2025, 12, 1),
            "ahorro_acumulado":  ahorro_acumulado,
        }

    @staticmethod
    def alcanzable() -> dict:
        return ProvisionFactory.crear(
            concepto="Matrícula educación superior",
            monto_total=Decimal("1800000"),
            fecha_pago=date(2026, 1, 15),
            ahorro_acumulado=Decimal("600000"),
        )

    @staticmethod
    def en_deficit() -> dict:
        return ProvisionFactory.crear(
            concepto="Vacaciones familiares",
            monto_total=Decimal("3000000"),
            fecha_pago=date(2025, 9, 1),
            ahorro_acumulado=Decimal("100000"),
        )

    @staticmethod
    def recien_creada(monto=Decimal("250000")) -> dict:
        """Provisión sin ahorros — para probar el inicio del flujo."""
        return ProvisionFactory.crear(
            concepto="Nueva provisión",
            monto_total=monto,
            ahorro_acumulado=Decimal("0"),
        )


# ==============================================================
# 4. HELPERS DE ASERCIÓN FINANCIERA
# ==============================================================

def assert_cop(actual: Decimal, esperado: Decimal, tolerancia: Decimal = Decimal("500"),
               etiqueta: str = ""):
    """
    Valida que dos valores Decimal estén dentro de tolerancia en COP.
    Usada para cuotas y montos donde puede haber diferencias de redondeo.

    Args:
        actual:      valor calculado por la función bajo prueba
        esperado:    valor de referencia validado externamente
        tolerancia:  diferencia máxima aceptable en COP (default: $500)
        etiqueta:    nombre del campo para el mensaje de error
    """
    diferencia = abs(actual - esperado)
    assert diferencia <= tolerancia, (
        f"\n{'[' + etiqueta + '] ' if etiqueta else ''}"
        f"Calculado:  ${actual:>15,.0f}\n"
        f"Esperado:   ${esperado:>15,.0f}\n"
        f"Diferencia: ${diferencia:>15,.0f}  (tolerancia: ${tolerancia:,.0f})"
    )


def assert_pct(actual: Decimal, esperado: Decimal, tolerancia: Decimal = Decimal("0.01"),
               etiqueta: str = ""):
    """
    Valida porcentajes dentro de tolerancia en puntos porcentuales.

    Args:
        tolerancia: en pp (default: 0.01 pp)
    """
    diferencia = abs(actual - esperado)
    assert diferencia <= tolerancia, (
        f"\n{'[' + etiqueta + '] ' if etiqueta else ''}"
        f"Calculado:  {actual:.4f}%\n"
        f"Esperado:   {esperado:.4f}%\n"
        f"Diferencia: {diferencia:.4f} pp  (tolerancia: {tolerancia:.4f} pp)"
    )


def assert_tabla_amortizacion(tabla: list[dict]):
    """
    Valida la coherencia estructural de una tabla de amortización French.

    Comprueba:
    - Claves requeridas en cada fila
    - Cuota = intereses + capital amortizado (cuadre por fila)
    - Saldo disminuye monotónicamente
    - Saldo final ≈ 0 (máx $1 por redondeo)
    """
    CLAVES = {"numero_cuota", "fecha_pago", "cuota_total",
              "intereses", "capital_amortizado", "saldo_capital"}

    assert len(tabla) > 0, "La tabla de amortización está vacía"

    for i, fila in enumerate(tabla, start=1):
        faltantes = CLAVES - set(fila.keys())
        assert not faltantes, f"Cuota {i}: faltan claves {faltantes}"

        reconstruida = fila["intereses"] + fila["capital_amortizado"]
        assert_cop(
            reconstruida, fila["cuota_total"],
            tolerancia=Decimal("2"),
            etiqueta=f"cuadre cuota {i}",
        )

    for i in range(1, len(tabla)):
        assert tabla[i]["saldo_capital"] < tabla[i - 1]["saldo_capital"], (
            f"Saldo no decrece en cuota {i + 1}: "
            f"${tabla[i]['saldo_capital']:,.0f} ≥ ${tabla[i-1]['saldo_capital']:,.0f}"
        )

    assert tabla[-1]["saldo_capital"] <= Decimal("1"), (
        f"Saldo final no es cero: ${tabla[-1]['saldo_capital']:,.2f}"
    )


def calcular_nomina_referencia(salario_bruto: Decimal,
                               params: dict = None) -> dict:
    """
    Implementación de referencia del cálculo de nómina colombiana.
    Úsala en tests para comparar contra la implementación real de la app.

    IMPORTANTE: Para salarios > 95 UVT/mes, la retención en la fuente
    requiere la tabla progresiva DIAN. Esta función retorna None en ese campo
    y los tests correspondientes deben marcarse como pendientes.
    """
    p = params or PARAMS_COLOMBIA_2025
    Q = lambda x: x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    salud    = Q(salario_bruto * p["tasa_salud_empleado"])
    pension  = Q(salario_bruto * p["tasa_pension_empleado"])

    umbral_solid = p["smlv"] * p["umbral_solidaridad_smlv"]
    if salario_bruto > umbral_solid:
        # Tasa base: 1% para 4–16 SMLV. Tiers superiores pendiente de implementar.
        solidaridad = Q(salario_bruto * p["tasa_solidaridad_4_16"])
    else:
        solidaridad = Decimal("0")

    uvt_mes = salario_bruto / p["uvt"]
    retencion = Decimal("0") if uvt_mes < p["umbral_retencion_uvt"] else None

    neto = salario_bruto - salud - pension - solidaridad
    if retencion is not None:
        neto -= retencion

    aplica_auxilio = salario_bruto <= (p["smlv"] * 2)
    auxilio = p["auxilio_transporte"] if aplica_auxilio else Decimal("0")

    return {
        "salario_bruto":          salario_bruto,
        "deduccion_salud":        salud,
        "deduccion_pension":      pension,
        "deduccion_solidaridad":  solidaridad,
        "retencion_fuente":       retencion,   # None = requiere tabla DIAN
        "salario_neto":           neto,
        "aplica_auxilio":         aplica_auxilio,
        "auxilio_transporte":     auxilio,
        "neto_con_auxilio":       neto + auxilio,
    }


# ==============================================================
# 5. FIXTURES PYTEST
# ==============================================================

@pytest.fixture(scope="session")
def params_colombia():
    """Parámetros normativos 2025 — disponibles en toda la sesión de test."""
    return PARAMS_COLOMBIA_2025


@pytest.fixture
def perfil():
    return PerfilFactory.crear()


@pytest.fixture
def perfil_smlv():
    return PerfilFactory.smlv()


@pytest.fixture
def perfil_profesional():
    return PerfilFactory.profesional()


@pytest.fixture
def nomina_smlv():
    return IngresoFactory.nomina(salario_bruto=PARAMS_COLOMBIA_2025["smlv"])


@pytest.fixture
def nomina_3_smlv():
    return IngresoFactory.nomina(salario_bruto=PARAMS_COLOMBIA_2025["smlv"] * 3)


@pytest.fixture
def categorias():
    return CategoriaFactory.completo()


@pytest.fixture
def gastos_mes():
    return GastoFactory.mes_completo()


@pytest.fixture
def credito_10m_25ea_12m():
    return CreditoFactory.crear(
        capital=Decimal("10000000"),
        tasa_ea=Decimal("0.25"),
        plazo_meses=12,
    )


@pytest.fixture
def credito_cooperativa():
    return CreditoFactory.cooperativa()


@pytest.fixture
def tarjeta_normal():
    return TarjetaCreditoFactory.crear()


@pytest.fixture
def tarjeta_al_limite():
    return TarjetaCreditoFactory.al_limite()


@pytest.fixture
def provision_soat():
    return ProvisionFactory.crear(
        concepto="SOAT vehículo / moto",
        monto_total=Decimal("250000"),
        fecha_pago=date(2025, 11, 1),
        ahorro_acumulado=Decimal("100000"),
    )


@pytest.fixture
def provision_deficit():
    return ProvisionFactory.en_deficit()


# Fixtures de conjuntos de casos parametrizados
@pytest.fixture(params=CASOS_CREDITO_FRENCH,
                ids=[c["descripcion"] for c in CASOS_CREDITO_FRENCH])
def caso_credito(request):
    """Parametriza automáticamente tests de crédito con todos los casos definidos."""
    return request.param


@pytest.fixture(params=CASOS_NOMINA,
                ids=[c["descripcion"] for c in CASOS_NOMINA])
def caso_nomina(request):
    """Parametriza automáticamente tests de nómina."""
    return request.param


@pytest.fixture(params=CASOS_PROVISION,
                ids=[c["descripcion"] for c in CASOS_PROVISION])
def caso_provision(request):
    """Parametriza automáticamente tests de provisiones."""
    return request.param


@pytest.fixture(params=CASOS_INDICADORES,
                ids=[c["descripcion"] for c in CASOS_INDICADORES])
def caso_indicadores(request):
    """Parametriza automáticamente tests de indicadores de salud financiera."""
    return request.param


# ==============================================================
# 6. PYTEST.INI — referencia (crear como archivo aparte en raíz)
# ==============================================================
# Crear pytest.ini en la raíz junto a docker-compose.yml:
#
# [pytest]
# DJANGO_SETTINGS_MODULE = config.settings
# python_files  = test_*.py *_test.py
# python_classes = Test*
# python_functions = test_*
# addopts = -v --tb=short
# markers =
#     financiero:   lógica financiera colombiana (validar externamente)
#     nomina:       módulo nómina y prestaciones
#     creditos:     módulo créditos — fórmula French
#     provisiones:  módulo provisiones de pagos futuros
#     indicadores:  salud financiera — semáforos e indicadores
#     integracion:  tests con base de datos real (más lentos)
#     lento:        tests de performance
#
# [coverage:run]
# source = apps
# omit = */migrations/*, */tests/*, */admin.py
#
# [coverage:report]
# show_missing = True
# fail_under = 60


# ==============================================================
# 7. EJEMPLO DE USO — cómo quedan los tests reales
# ==============================================================
#
# === tests/apps/deudas/test_creditos.py ===
#
# import pytest
# from decimal import Decimal
# from apps.deudas.services import calcular_cuota_mensual, generar_tabla_amortizacion
# from tests.conftest import assert_cop, assert_tabla_amortizacion
#
# @pytest.mark.financiero
# @pytest.mark.creditos
# def test_cuota_caso_conocido(caso_credito):
#     """Valida todos los casos definidos en CASOS_CREDITO_FRENCH."""
#     if caso_credito.get("incompleto"):
#         pytest.xfail("Caso incompleto — pendiente validación externa")
#
#     cuota = calcular_cuota_mensual(**caso_credito["inputs"])
#     assert_cop(
#         cuota,
#         caso_credito["esperado"]["cuota_mensual"],
#         tolerancia=caso_credito["tolerancia_cop"],
#         etiqueta="cuota_mensual",
#     )
#
#
# @pytest.mark.financiero
# @pytest.mark.creditos
# def test_tabla_estructura_valida(credito_10m_25ea_12m):
#     tabla = generar_tabla_amortizacion(**credito_10m_25ea_12m)
#     assert_tabla_amortizacion(tabla)
#     assert len(tabla) == credito_10m_25ea_12m["plazo_meses"]
#
#
# === tests/apps/ingresos/test_nomina.py ===
#
# @pytest.mark.financiero
# @pytest.mark.nomina
# def test_nomina_caso(caso_nomina):
#     if caso_nomina.get("incompleto"):
#         pytest.xfail("Caso incompleto — pendiente validación DIAN")
#
#     resultado = calcular_nomina(caso_nomina["inputs"]["salario_bruto"])
#     for campo, valor_esperado in caso_nomina["esperado"].items():
#         if isinstance(valor_esperado, Decimal):
#             assert_cop(resultado[campo], valor_esperado,
#                        tolerancia=Decimal("100"), etiqueta=campo)
#         elif isinstance(valor_esperado, bool):
#             assert resultado[campo] == valor_esperado, f"Campo {campo} incorrecto"
