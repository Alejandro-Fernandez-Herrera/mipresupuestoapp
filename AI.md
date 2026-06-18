# AI Development Harness — Finanzas Hogar y Personales

> Este archivo contiene el contexto, las reglas y las restricciones que guían
> el desarrollo asistido por IA en este proyecto. Aplica a Claude, GitHub Copilot,
> Cursor y cualquier asistente de código. Leer completo antes de generar código.

---

## 1. QUÉ ES ESTE PROYECTO

Aplicación web local para gestión de finanzas personales y del hogar, diseñada
para familias colombianas. Calcula nómina colombiana (bruto → neto con deducciones
legales), gestiona gastos por categorías, créditos con amortización French,
tarjetas de crédito, provisiones para pagos periódicos, fondo de emergencia e
indicadores de salud financiera.

**Usuarios objetivo:** cualquier hogar colombiano con salario dependiente.
**Entorno:** local (localhost). Migrará a cloud en versión futura.
**Idioma:** 100% español colombiano en UI y documentación.
**Desarrollador:** solo, tiempo parcial (~8-10h/semana).

---

## 2. STACK — DECISIONES FIJAS (no proponer alternativas)

```
Backend:      Django 5.x + Python 3.12
Base de datos: PostgreSQL 16 (Docker, volumen nombrado)
Frontend:     Django Templates + Alpine.js + Chart.js
PDF:          WeasyPrint
Excel/CSV:    openpyxl
Auth:         Django Auth + django-session-timeout
Contenedor:   Docker Compose
Tests:        pytest + pytest-django + factory-boy + freezegun
Formatter:    Black
```

**NO sugerir:**
- React, Vue, Next.js (el frontend es Django Templates para esta versión)
- FastAPI o Flask (el proyecto usa Django)
- MongoDB, SQLite (el proyecto usa PostgreSQL 16)
- SQLAlchemy (usar el ORM de Django)
- Celery o Redis (sin tareas asíncronas en v1.0)
- Docker Swarm o Kubernetes (local app)

---

## 3. REGLAS DE CÓDIGO CRÍTICAS

### 3.1 SIEMPRE usar Decimal para montos — NUNCA float

```python
# CORRECTO
from decimal import Decimal, ROUND_HALF_UP
capital = Decimal("10000000")
tasa    = Decimal("0.018769")
cuota   = (capital * tasa / (1 - (1 + tasa) ** -12)).quantize(
    Decimal("1"), rounding=ROUND_HALF_UP
)

# INCORRECTO — produce errores de redondeo acumulativos
capital = 10000000.0
tasa    = 0.018769
cuota   = capital * tasa / (1 - (1 + tasa) ** -12)
```

### 3.2 Los parámetros normativos van en BD, NUNCA hardcodeados

```python
# CORRECTO — leer de ConfiguracionFiscal en BD
config = ConfiguracionFiscal.objects.get(anio=2025)
salud = salario * config.tasa_salud_empleado

# INCORRECTO — se rompe en enero cuando cambia el SMLV
salud = salario * Decimal("0.04")  # nunca así
```

### 3.3 Las vistas Django deben ser delgadas — la lógica va en services.py

```
apps/
└── deudas/
    ├── models.py      # solo definición de modelos, sin lógica de negocio
    ├── services.py    # toda la lógica financiera aquí
    ├── views.py       # solo orquestación: recibe request → llama service → retorna response
    ├── forms.py       # validación de inputs
    └── tests/
        └── test_services.py  # los tests van contra services.py, no views.py
```

### 3.4 Toda función financiera crítica debe tener docstring con la fórmula

```python
def calcular_cuota_mensual(capital: Decimal, tasa_ea: Decimal, plazo_meses: int) -> Decimal:
    """
    Calcula la cuota mensual de un crédito usando el sistema francés (cuota fija).

    Fórmula:
        i = (1 + EA)^(1/12) - 1          (conversión tasa EA a mensual)
        Cuota = (P × i) / (1 - (1+i)^-n) (French)

    Referencias:
        - Superfinanciera Colombia — Circular Básica Contable
        - Validado contra simulador Bancolombia (ver tests/apps/deudas/test_services.py)

    Args:
        capital:      monto desembolsado en COP (Decimal)
        tasa_ea:      tasa efectiva anual como decimal (ej: 0.25 para 25%)
        plazo_meses:  número de cuotas mensuales

    Returns:
        cuota mensual en COP redondeada al peso (Decimal)

    Raises:
        ValueError: si capital <= 0, tasa_ea <= 0, o plazo_meses <= 0
    """
```

### 3.5 Variables de entorno — NUNCA credenciales en código

```python
# CORRECTO
import os
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")

# INCORRECTO
DB_PASSWORD = "mi_password_123"  # nunca
```

### 3.6 Fechas con zona horaria colombiana

```python
# CORRECTO
from django.utils import timezone
from zoneinfo import ZoneInfo

BOGOTA_TZ = ZoneInfo("America/Bogota")
ahora = timezone.now().astimezone(BOGOTA_TZ)

# INCORRECTO — datetime naive causa bugs en fechas de corte y provisiones
from datetime import datetime
ahora = datetime.now()
```

---

## 4. ESTRUCTURA DJANGO — APPS Y RESPONSABILIDADES

```
apps/
├── accounts/       # Autenticación, perfil de usuario, ConfiguracionFiscal
│                   # Modelos: UserProfile, ConfiguracionFiscal
│
├── ingresos/       # Nómina colombiana, prestaciones, otros ingresos
│                   # Modelos: RegistroNomina, OtroIngreso
│                   # Services: calcular_nomina(), calcular_prestaciones()
│
├── gastos/         # Categorías, rubros, transacciones de gasto
│                   # Modelos: Categoria, Rubro, Gasto
│
├── deudas/         # Créditos de consumo y tarjetas de crédito
│                   # Modelos: Credito, CuotaCredito, TarjetaCredito, CompraTC
│                   # Services: calcular_cuota_mensual(), generar_tabla_amortizacion()
│
├── provisiones/    # Pagos periódicos futuros y fondo de emergencia
│                   # Modelos: Provision, AporteProvision, FondoEmergencia
│                   # Services: calcular_provision(), evaluar_alcanzabilidad()
│
├── indicadores/    # Salud financiera — cálculos e histórico
│                   # Sin modelos propios (lee de las otras apps)
│                   # Services: calcular_indicadores_mes()
│
└── reportes/       # Generación PDF y exportación CSV
                    # Sin modelos propios
                    # Services: generar_pdf_mes(), exportar_csv()
```

### Relaciones entre apps

```
accounts ←── todos los modelos tienen FK a UserProfile
ingresos ──┐
gastos   ──┤
deudas   ──┼──→ indicadores (lee, no escribe)
provisiones┘
```

---

## 5. BASE DE DATOS — CONVENCIONES

### 5.1 Tipos de campo para montos

```python
# SIEMPRE DecimalField con max_digits=14, decimal_places=2
monto = models.DecimalField(max_digits=14, decimal_places=2)

# Justificación: max_digits=14 soporta hasta $99.999.999.999,99
# — suficiente para cualquier hogar colombiano por décadas
```

### 5.2 Tipos de campo para porcentajes y tasas

```python
# Porcentajes almacenados como decimal (0.25 = 25%, NO como 25)
tasa_ea = models.DecimalField(
    max_digits=8, decimal_places=6,
    help_text="Tasa efectiva anual como decimal. Ej: 0.25 para 25% EA"
)
```

### 5.3 Campos de auditoría en todos los modelos

```python
class BaseModel(models.Model):
    """Modelo base con auditoría — todos los modelos deben heredar de este."""
    creado_en    = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

### 5.4 Nombres de campos en español

```python
# CORRECTO — proyecto en español
salario_bruto   = models.DecimalField(...)
fecha_desembolso = models.DateField(...)
plazo_meses     = models.IntegerField(...)

# INCORRECTO — mezcla de idiomas
gross_salary    = models.DecimalField(...)   # no
disbursement_date = models.DateField(...)    # no
```

### 5.5 Tabla ConfiguracionFiscal — parámetros editables por año

```python
class ConfiguracionFiscal(models.Model):
    anio                    = models.IntegerField(unique=True)
    smlv                    = models.DecimalField(max_digits=14, decimal_places=2)
    auxilio_transporte      = models.DecimalField(max_digits=14, decimal_places=2)
    uvt                     = models.DecimalField(max_digits=14, decimal_places=4)
    tasa_salud_empleado     = models.DecimalField(max_digits=6, decimal_places=4)
    tasa_pension_empleado   = models.DecimalField(max_digits=6, decimal_places=4)
    # ... demás parámetros
```

---

## 6. DOMINIO: FINANZAS COLOMBIANAS

### 6.1 Fórmula French (créditos)

```
i = (1 + EA)^(1/12) - 1
Cuota = (P × i) / (1 - (1+i)^-n)

Donde:
  P = capital (COP)
  i = tasa mensual equivalente
  n = plazo en meses
  EA = tasa efectiva anual (decimal: 0.25 para 25%)

Caso de referencia validado:
  P=10.000.000, EA=25%, n=12 → i≈1.8769%, Cuota≈$938.450
```

### 6.2 Nómina colombiana — deducciones del empleado

```
Salud:      4% del salario base
Pensión:    4% del salario base
Solidaridad: 1% si salario > 4 SMLV (tiers superiores: ver ConfiguracionFiscal)
Retención:  tabla DIAN — 0% si salario < 95 UVT/mes (≈$4.730.905 en 2025)

Salario Neto = Bruto - Salud - Pensión - Solidaridad - Retención

Auxilio de transporte: solo si salario base ≤ 2 SMLV
```

### 6.3 Prestaciones sociales (provisión mensual)

```
Prima de servicios:     8.33% mensual → pago jun-30 y dic-20
Cesantías:              8.33% mensual → consignación feb-14
Intereses cesantías:    12% anual sobre cesantías → pago ene-31
Vacaciones:             4.17% mensual → cuando el trabajador solicite
```

### 6.4 Provisiones para pagos futuros

```
Ahorro mensual recomendado = (Monto total - Acumulado) / Meses restantes
Ahorro máximo alcanzable   = Ahorro mensual disponible × Meses restantes
Déficit                    = Monto total - (Acumulado + Máximo alcanzable)
Alerta déficit             = cuando Máximo alcanzable < (Monto total - Acumulado)
Progreso                   = (Acumulado / Monto total) × 100
```

### 6.5 Indicadores de salud financiera — umbrales

```
Ratio endeudamiento = (Cuotas créditos + Mínimos TC) / Ingreso neto × 100
  verde: < 30%  |  amarillo: 30-40%  |  rojo: > 40%

Tasa ahorro = Ahorro neto / Ingreso neto × 100
  verde: ≥ 20%  |  amarillo: 10-20%  |  rojo: < 10%

Cobertura fondo emergencia = Saldo fondo / Gasto esencial mensual (en meses)
  verde: ≥ 3 meses  |  amarillo: 1-3 meses  |  rojo: < 1 mes

Presión gastos fijos = Gastos fijos / Ingreso neto × 100
  referencia: idealmente < 50%
```

---

## 7. TESTING — CONVENCIONES

### 7.1 El harness de tests está en tests/conftest.py

El archivo `tests/conftest.py` contiene:
- `PARAMS_COLOMBIA_2025` — parámetros normativos de referencia
- `CASOS_CREDITO_FRENCH` — casos validados externamente con tolerancias
- `CASOS_NOMINA` — casos de nómina con valores conocidos
- `CASOS_PROVISION` — casos de provisiones
- `CASOS_INDICADORES` — escenarios de salud financiera
- Factories: `PerfilFactory`, `IngresoFactory`, `CategoriaFactory`, `GastoFactory`, `CreditoFactory`, `TarjetaCreditoFactory`, `ProvisionFactory`
- Helpers: `assert_cop()`, `assert_pct()`, `assert_tabla_amortizacion()`, `calcular_nomina_referencia()`

### 7.2 Tests de lógica financiera van contra services.py

```python
# CORRECTO — testear la función pura de cálculo
from apps.deudas.services import calcular_cuota_mensual
from tests.conftest import assert_cop, CASOS_CREDITO_FRENCH

@pytest.mark.financiero
@pytest.mark.creditos
@pytest.mark.parametrize("caso", CASOS_CREDITO_FRENCH,
                          ids=[c["descripcion"] for c in CASOS_CREDITO_FRENCH])
def test_cuota_mensual(caso):
    cuota = calcular_cuota_mensual(**caso["inputs"])
    assert_cop(cuota, caso["esperado"]["cuota_mensual"],
               tolerancia=caso["tolerancia_cop"])

# INCORRECTO — no testear a través de la vista HTTP para lógica financiera
def test_cuota_via_post():
    response = client.post("/creditos/nuevo/", {...})  # no para lógica financiera
```

### 7.3 Usar Decimal en los tests, nunca int ni float

```python
# CORRECTO
assert_cop(resultado, Decimal("938450"))

# INCORRECTO
assert resultado == 938450      # int
assert resultado == 938450.0    # float
```

### 7.4 Marcar tests incompletos con pytest.xfail, no borrarlos

```python
def test_retencion_salario_alto(caso_nomina):
    if caso_nomina.get("incompleto"):
        pytest.xfail("Pendiente: validar tabla retención DIAN para > 95 UVT")
    # ... resto del test
```

---

## 8. FRONTEND — CONVENCIONES

### 8.1 Alpine.js para interactividad — no JavaScript vanilla complejo

```html
<!-- CORRECTO — Alpine.js para estado simple -->
<div x-data="{ mostrar_tabla: false }">
  <button @click="mostrar_tabla = !mostrar_tabla">Ver tabla</button>
  <div x-show="mostrar_tabla">...</div>
</div>

<!-- INCORRECTO para este proyecto -->
<script>
  document.querySelector(...).addEventListener(...)  // no para interacciones complejas
</script>
```

### 8.2 Chart.js para gráficos — instancias en bloques script al final del template

```html
{% block scripts %}
<script>
  const ctx = document.getElementById('grafico-gastos').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: {{ categorias_json|safe }},
      datasets: [{ data: {{ montos_json|safe }} }]
    }
  });
</script>
{% endblock %}
```

### 8.3 Montos en COP — siempre con formato colombiano

```python
# En el template tag o filtro
# $1.250.000  ← separador de miles: punto
# $1.250.000,50  ← decimales: coma (solo si se necesitan centavos)
```

---

## 9. DOCKER — CONVENCIONES

### 9.1 El volumen de datos NO se elimina con docker compose down

```bash
docker compose down       # seguro — el volumen finanzas_postgres_data persiste
docker compose down -v    # DESTRUCTIVO — solo para reset total
```

### 9.2 Aplicar migraciones dentro del contenedor

```bash
docker exec finanzas_web python manage.py makemigrations
docker exec finanzas_web python manage.py migrate
```

### 9.3 Backup antes de migraciones destructivas

```bash
docker exec finanzas_db pg_dump -U finanzas_user finanzas_hogar \
  > ./backups/pre_migration_$(date +%Y%m%d_%H%M).sql
```

### 9.4 Scripts de backup/restore

```bash
# Backup manual
./scripts/backup.sh

# Restaurar desde backup
./scripts/restore.sh backups/finanzas_hogar_20260617_060000.dump

# Backup automático diario (agregar a crontab -e):
# 0 6 * * * /home/aiks/mipresupuestoapp/scripts/backup.sh
```

Los backups se guardan en `backups/` con formato `.dump` (comprimido).
Se conservan los últimos 30 días automáticamente.

---

## 10. ESTADO ACTUAL DEL PROYECTO

```
Sprint actual: S12 — Exportar PDF + CSV · Pulido UI · Documentación · Release (HU-015)
Última actualización: 2026-06-17

COMPLETADO:
  ✅ Especificaciones v2.1
  ✅ Test harness (tests/conftest.py)
  ✅ AI harness (AI.md)
  ✅ README.md

COMPLETADO:
  ✅ S1: Docker Compose + estructura Django + PostgreSQL
  ✅ S2: Auth, sesiones, perfil con config SMLV/UVT
  ✅ S3: Módulo ingresos + nómina colombiana
  ✅ S4: Categorías, rubros, gastos
  ✅ S5: Ahorro + fondo emergencia + dashboard básico
  ✅ S6: Créditos de consumo (French amortization)
  ✅ S7: Tarjetas de crédito (HU-011, RF-060 a RF-067)
  ✅ S8: Provisiones + catálogo Colombia (HU-012)
  ✅ S9: Indicadores salud financiera + Prestaciones (HU-018, HU-019)
  ✅ S10: Dashboard integrado con todos los módulos (HU-014)
  ✅ S11: Proyecciones y escenarios (HU-013)
  ✅ S12: Exportar PDF + CSV · Pulido UI · Documentación · Release (HU-015)

### S9: Indicadores Salud Financiera + Prestaciones (HU-018, HU-019)

**HU-018 — Indicadores de Salud Financiera (RF-091 a RF-096)**
- RF-091: Ratio de Endeudamiento con semáforo verde/amarillo/rojo
- RF-092: Tasa de Ahorro con semáforo vs meta configurable
- RF-093: Cobertura Fondo Emergencia con semáforo (>3m, 1-3m, <1m)
- RF-094: Presión de Gastos Fijos con referencia < 50%
- RF-095: Dashboard con 4 indicadores, semáforos y tendencia (↑ ↓ →)
- RF-096: Diagnóstico automático mensual (máximo 3 líneas)

**Componentes creados:**
- `apps/indicadores/` — app completa con modelos, servicios, vistas, templates y tests
- `HistorialIndicador` — modelo para snapshot mensual de indicadores
- `services.py` — funciones puras de cálculo + orquestación con BD
- Vista `historial_indicadores` — tabla de evolución últimos 12 meses
- Template `indicadores/historial.html` — 4 tarjetas con semáforo + historial
- Tests: 20 tests unitarios parametrizados (todos pasan)

**HU-019 — Prestaciones Sociales Proyectadas**
- Fechas de pago dinámicas (no hardcodeadas 2026/2027)
- `calcular_alerta_prestacion()` — alerta 45 días antes del vencimiento
- `verificar_alertas_prestaciones()` — lista de prestaciones próximas
- Vista `marcar_prestacion_pagada()` — confirmar pago vs. proyectado
- Dashboard widget "Prestaciones Proyectadas — Próximas"
- Alertas visuales en tarjetas (critico/proximo/urgente)

**Dashboard integrado:**
- Dashboard migrado a usar `indicadores.services` (consolidación)
- 4to indicador añadido: Ratio de Endeudamiento
- Flechas de tendencia (↑ ↓ →) para cada indicador
- Link a página de historial completo
- Widget de prestaciones próximas con alertas
```

### S11: Proyecciones y Escenarios (HU-013)

**HU-013 — Proyecciones Financieras (RF-100 a RF-105)**
- RF-100: Proyección de ingresos y gastos a 6, 12 y 24 meses
- RF-101: Tres escenarios: optimista, realista, conservador
- RF-102: Factor de ajuste por escenario (ej: +10% ingreso en optimista)
- RF-103: Proyección de ahorro acumulado en el horizonte
- RF-104: Proyección de cierre de provisiones activas
- RF-105: API JSON para gráficos en el frontend

### S12: Exportar PDF + CSV · Pulido UI · Documentación · Release (HU-015)

**HU-015 — Exportar Reportes (RF-120 a RF-123)**
- RF-120: Reporte PDF mensual con WeasyPrint — resumen, indicadores, gastos por categoría, ingresos, deudas, provisiones
- RF-121: Exportar datos a CSV con filtro por mes
- RF-122: Exportar datos a Excel (openpyxl) con hojas: Resumen, Ingresos, Gastos, Deudas, Provisiones, Fondo Emergencia
- RF-123: Marca de fecha de generación en todos los archivos exportados

**Componentes creados:**
- `apps/reportes/services.py` — 3 servicios: `generar_pdf_mes()`, `exportar_csv()`, `exportar_excel()`
- `apps/reportes/views.py` — 3 vistas decoradas con `@login_required`
- `apps/reportes/urls.py` — rutas `/reportes/pdf/`, `/reportes/csv/`, `/reportes/excel/`
- Template `reportes/reporte_mensual.html` — diseñado para WeasyPrint (sin JS, CSS inline)
- Navbar con enlace "Reportes"
- Dashboard con botones PDF/CSV/Excel contextuales al mes/año visible
- 17 tests unitarios para servicios y vistas de exportación

**Pulido UI:**
- Navbar: enlace "Reportes" agregado entre Proyecciones e Indicadores
- Dashboard: botones de exportación PDF, CSV y Excel con filtro mes/año

**Release v1.0:**
- Dependencias WeasyPrint agregadas al Dockerfile (libpango, libcairo, libgdk-pixbuf)
- `black .` ejecutado
- 150 tests pasando, 1 xfail esperado
- Documentación actualizada (AI.md, README.md)

---
### S10: Dashboard Integrado con todos los módulos (HU-014)

**RF-112 — Gráfico de línea: tendencia ingresos vs. gastos últimos 6 meses**
- Nueva función `obtener_tendencia_ingresos_gastos()` en `indicadores/services.py`
- Chart.js line chart con 2 datasets: Ingresos (verde) y Gastos (rojo)
- Tooltip con formato COP en eje Y

**RF-115 — Resumen de deudas: total cuotas mensuales + total saldos (créditos + tarjetas)**
- Nueva función `obtener_resumen_deudas()` en `indicadores/services.py`
- Widget en dashboard: créditos activos, tarjetas activas, total cuotas/mes, deuda total
- Lista compacta de tarjetas con semáforo de uso (● verde/amarillo/rojo) y disponibilidad

**RF-116 — Lista de provisiones activas con barra de progreso y próximas en vencer**
- Nueva función `obtener_provisiones_activas()` en `indicadores/services.py`
- Widget en dashboard: top 5 provisiones con barra de progreso coloreada, alerta visual si próxima a vencer con < 80%

**RF-118 — Dashboard actualizado al registrar transacciones**
- Redirects post-guardado en gastos, ingresos, deudas y provisiones apuntan al dashboard

**Tests creados:**
- `tests/apps/test_dashboard.py` — 14 tests: vista dashboard, widgets, servicios y redirects
```

### Decisiones tomadas (no reabrir)

| Decisión | Elegido | Descartado |
|----------|---------|------------|
| Backend | Django 5.x | FastAPI, Flask |
| Frontend v1.0 | Django Templates + Alpine.js | React, Vue |
| Base de datos | PostgreSQL 16 | SQLite, MySQL |
| PDF | WeasyPrint | ReportLab, xhtml2pdf |
| Contenedor | Docker Compose con volúmenes | entorno virtual sin Docker |
| Idioma UI | Español colombiano | Inglés |
| Redondeo montos | ROUND_HALF_UP | ROUND_HALF_EVEN (banker's) |

### Decisiones abiertas (consultar antes de implementar)

- Autenticación 2FA: ¿implementar en v1.0 o v2.0?
- Tema visual: ¿paleta de colores definitiva?
- Módulo de impuestos (renta): ¿v1.0 o backlog?
- Formato de exportación PDF: ¿landscape o portrait para tabla de amortización?

---

## 11. QUÉ NO HACER (reglas absolutas)

```
❌ No usar float para montos — siempre Decimal
❌ No hardcodear SMLV, UVT, ni tasas — siempre desde ConfiguracionFiscal
❌ No poner lógica de negocio en views.py — va en services.py
❌ No mezclar inglés y español en nombres de campos del modelo
❌ No eliminar casos de test con pytest.xfail — marcarlos como incompletos
❌ No commitear .env — solo .env.example
❌ No usar docker compose down -v en desarrollo activo
❌ No proponer cambios de stack sin issue documentado
❌ No usar datetime.now() — usar timezone.now() con ZoneInfo("America/Bogota")
❌ No escribir SQL crudo — usar el ORM de Django
```

---

## 12. CONTEXTO DEL DESARROLLADOR

- Lenguaje más fuerte: Python. También Java/Spring Boot, JavaScript básico.
- Experiencia relevante: MySQL/PostgreSQL, Docker, Django (en formación), GitHub Actions.
- Tiempo disponible: ~8-10 horas/semana (trabajo full-time + universidad parcial).
- Entorno de desarrollo: WSL2 (Ubuntu 24, usuario `aiks`), VS Code, Chrome como browser primario.
- Preferencia de feedback: directo, sin suavizar, con código concreto cuando aplique.
- Anti-patrón conocido: planificación exhaustiva sin ejecutar. Si se detecta análisis excesivo sin código, interrumpir y pedir el primer commit.

---

*Última actualización: 2026-06-17*
*Mantener actualizado al inicio de cada sprint.*
