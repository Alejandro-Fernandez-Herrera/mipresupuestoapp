# 📋 Especificaciones — App Finanzas Hogar y Personales
## Versión 2.1 — Colombia · Uso General
> Aplicación de finanzas personales y del hogar para familias colombianas. Parámetros normativos (SMLV, UVT, deducciones) configurables anualmente. Categorías, rubros y provisiones sugeridas como punto de partida editable por cada usuario.

---

## 0. STACK TECNOLÓGICO E INFRAESTRUCTURA

### 0.1 Decisión de Stack

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| **Backend** | Django 5.x + Python 3.12 | Auth, ORM, admin y formularios incluidos; amplio ecosistema financiero |
| **Base de Datos** | PostgreSQL 16 (Docker con volumen nombrado) | `Decimal` exacto para montos; sin pérdida de datos entre reinicios; migrable a cloud sin refactor |
| **Frontend** | Django Templates + Alpine.js + Chart.js | Sin overhead de React para v1.0 local; interactividad suficiente sin build pipeline |
| **PDF** | WeasyPrint | HTML/CSS → PDF; más mantenible que ReportLab para reportes con tablas y gráficos |
| **Excel/CSV** | openpyxl | Estándar Python para xlsx |
| **Auth** | Django Auth + django-session-timeout | Sesión individual con expiración a 30 min, sin configuración adicional |
| **Contenedor local** | Docker Compose + Named Volumes | PostgreSQL + Django en un solo `docker-compose up`; datos persistentes entre reinicios |

---

### 0.2 Configuración Docker con Volúmenes

#### docker-compose.yml

```yaml
version: '3.9'

services:

  db:
    image: postgres:16-alpine
    container_name: finanzas_db
    environment:
      POSTGRES_DB:       ${POSTGRES_DB:-finanzas_hogar}
      POSTGRES_USER:     ${POSTGRES_USER:-finanzas_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data   # volumen nombrado — persiste entre reinicios
      - ./backups:/backups                        # directorio local para dumps manuales
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-finanzas_user} -d ${POSTGRES_DB:-finanzas_hogar}"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: ./backend
    container_name: finanzas_web
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app              # hot reload en desarrollo
      - static_files:/app/staticfiles
      - media_files:/app/media      # exports PDF/CSV generados
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:                    # datos PostgreSQL — NO se eliminan con docker compose down
    name: finanzas_postgres_data
  static_files:                     # archivos estáticos Django collectstatic
    name: finanzas_static
  media_files:                      # archivos generados (PDF, CSV)
    name: finanzas_media
```

#### Variables de entorno (.env)

```env
# Base de datos
POSTGRES_DB=finanzas_hogar
POSTGRES_USER=finanzas_user
POSTGRES_PASSWORD=cambia_esto_por_una_password_segura

# Django
SECRET_KEY=genera_una_clave_larga_y_aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Zona horaria
TZ=America/Bogota
```

#### Comandos de gestión del volumen

```bash
# Levantar todo (crea los volúmenes si no existen)
docker compose up -d

# Ver estado de los volúmenes
docker volume ls | grep finanzas

# Backup manual de la base de datos
docker exec finanzas_db pg_dump -U finanzas_user finanzas_hogar > ./backups/backup_$(date +%Y%m%d).sql

# Restaurar desde backup
docker exec -i finanzas_db psql -U finanzas_user finanzas_hogar < ./backups/backup_20260101.sql

# Bajar contenedores SIN eliminar datos (el volumen persiste)
docker compose down

# Bajar contenedores Y eliminar datos (DESTRUCTIVO — usar solo para reset total)
docker compose down -v
```

> **Regla crítica:** `docker compose down` sin `-v` es seguro. Los datos en `finanzas_postgres_data` sobreviven. `docker compose down -v` elimina todo — úsalo solo cuando quieras reiniciar el proyecto desde cero.

---

### 0.3 Estructura de Proyecto

```
finanzas_hogar/
├── docker-compose.yml
├── .env                     # NO commitear al repositorio
├── .env.example             # plantilla sin valores reales — sí commitear
├── backups/                 # dumps SQL manuales
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/              # settings, urls, wsgi
│   └── apps/
│       ├── accounts/        # auth, perfil usuario, configuración SMLV/UVT
│       ├── ingresos/        # nómina, prestaciones, otros ingresos
│       ├── gastos/          # categorías, rubros, transacciones
│       ├── deudas/          # créditos de consumo, tarjetas de crédito
│       ├── provisiones/     # pagos anuales/periódicos
│       ├── proyecciones/    # escenarios futuros
│       └── reportes/        # generación PDF, exportación CSV
└── static/
    ├── js/                  # Alpine.js, Chart.js (CDN en dev)
    └── css/
```

---

### 0.4 Justificación de Construir vs. Usar App Existente

Opciones disponibles en Colombia: Finerio, Monefy, YNAB (en inglés), Siigo (orientado a empresa). Ninguna tiene:
- Módulo de nómina colombiana con cálculo automático de deducciones legales
- Prestaciones sociales con proyección y alerta de fechas de pago
- Provisiones para el ciclo de gastos colombiano (SOAT, tecno-mecánica, matrículas)
- Parámetros normativos editables (SMLV, UVT) que cambian cada enero

**Construir es la decisión correcta.** Es un proyecto de portafolio con problema real, es la intersección entre formación financiera y formación técnica, y tiene potencial de crecer a micro-SaaS para hogares colombianos.

---

## 1. MÓDULOS FUNCIONALES

### 1.1 Autenticación y Sesiones

| ID | Requisito Funcional |
|----|---------------------|
| RF-001 | El sistema debe permitir registro con nombre completo, email único y contraseña mínimo 8 caracteres |
| RF-002 | El sistema debe permitir autenticación con email y contraseña |
| RF-003 | Las sesiones deben expirar automáticamente a los 30 minutos de inactividad |
| RF-004 | El sistema debe permitir recuperación de contraseña por email |
| RF-005 | El perfil de usuario debe incluir: nombre, email, ciudad, moneda (COP por defecto), SMLV vigente (editable cada enero), UVT vigente (editable cada año) |
| RF-006 | El sistema debe soportar múltiples perfiles en la misma instalación local (un perfil por persona del hogar) con sesiones separadas e independientes |

---

### 1.2 Módulo de Ingresos — Contexto Colombia

#### 1.2.1 Nómina Colombiana

| ID | Requisito Funcional |
|----|---------------------|
| RF-010 | El sistema debe permitir ingresar salario base mensual devengado |
| RF-010a | El sistema debe calcular automáticamente las deducciones legales del empleado: Salud (4% del salario base), Pensión (4% del salario base), Fondo de Solidaridad Pensional (0.5% si salario base > 4 SMLV, escala progresiva hasta 2%) |
| RF-010b | El sistema debe calcular Retención en la Fuente según tabla DIAN vigente (0% si ingreso laboral ≤ 95 UVT/mes; progresiva en adelante). El usuario puede ingresar el porcentaje calculado por su empleador si prefiere no usar la tabla automática |
| RF-010c | El sistema debe mostrar desglose neto: Salario Bruto − Salud − Pensión − Fondo Solidaridad − Retención = **Salario Neto** |
| RF-010d | El sistema debe permitir actualizar anualmente los valores de SMLV y UVT en configuración (cambian cada enero por decreto) |
| RF-010e | El auxilio de transporte solo aplica si el salario base es ≤ 2 SMLV; el sistema debe validar esto automáticamente y mostrar aviso al usuario |

#### 1.2.2 Provisión de Prestaciones Sociales

> Estas no son ingresos mensuales sino proyecciones de lo que el empleador pagará. El sistema las muestra como "ingresos esperados" en el mes correspondiente y como provisión acumulada mes a mes para planificación.

| ID | Requisito Funcional |
|----|---------------------|
| RF-011a | **Prima de Servicios**: calcular 8.33% mensual del salario base. Pago proyectado: junio 30 y diciembre 20. El sistema debe mostrar acumulado proyectado y alerta 45 días antes de la fecha de pago |
| RF-011b | **Cesantías**: calcular 8.33% mensual. Consignación al fondo proyectada para 14 de febrero. El sistema debe mostrar monto proyectado y permitir registrar confirmación de consignación |
| RF-011c | **Intereses de Cesantías**: 12% anual sobre cesantías acumuladas, pagaderos 31 de enero. Calcular automáticamente y mostrar monto esperado |
| RF-011d | **Vacaciones**: provisión del 4.17% mensual del salario base. El usuario puede registrar cuándo tomará vacaciones y el sistema calcula el pago esperado |
| RF-011e | El dashboard debe mostrar una sección "Prestaciones Proyectadas" con el acumulado de cada concepto y el mes de pago esperado |

#### 1.2.3 Otros Ingresos

| ID | Requisito Funcional |
|----|---------------------|
| RF-012 | El sistema debe permitir registrar ingresos adicionales por tipo: Auxilio de transporte (con valor referencial legal vigente), Horas extra diurnas (+25%), Horas extra nocturnas (+75%), Dominicales y festivos (+75%), Comisiones, Bonificaciones no salariales, Honorarios/Freelance, Ingresos pasivos (arriendos, dividendos), Otros |
| RF-013 | El sistema debe permitir marcar cualquier ingreso como recurrente mensual (se replica automáticamente) |
| RF-014 | El sistema debe calcular total ingresos netos del mes = Salario Neto + Todos los demás ingresos |
| RF-015 | El sistema debe mantener historial mes a mes de todos los ingresos |
| RF-016 | El sistema debe permitir proyecciones de ingresos para meses futuros |

---

### 1.3 Gestión de Categorías y Rubros

> Ver Sección 3 para el catálogo completo de categorías y rubros sugeridos.

| ID | Requisito Funcional |
|----|---------------------|
| RF-020 | El sistema debe cargar al crear el perfil las categorías y rubros sugeridos de la Sección 3 como punto de partida |
| RF-021 | El sistema debe permitir crear categorías personalizadas adicionales (nombre, color, ícono opcional) |
| RF-022 | El sistema debe permitir crear rubros/subcategorías dentro de cualquier categoría |
| RF-023 | El sistema debe permitir ocultar (no eliminar) categorías sugeridas que no apliquen al usuario |
| RF-024 | El sistema debe permitir editar y eliminar categorías y rubros personalizados (solo si no tienen gastos asociados) |
| RF-025 | El sistema debe asignar color diferenciador a cada categoría para visualización en gráficos |
| RF-026 | El sistema debe mostrar las categorías ordenadas por monto gastado en el mes (mayor a menor) por defecto |

---

### 1.4 Gestión de Gastos

| ID | Requisito Funcional |
|----|---------------------|
| RF-030 | El sistema debe permitir registrar gasto con: categoría, rubro, monto (COP con 2 decimales), fecha, descripción opcional, método de pago (efectivo, débito, crédito, transferencia, Nequi/Daviplata), tipo (fijo/variable) |
| RF-031 | El sistema debe permitir marcar gasto como recurrente mensual |
| RF-032 | El sistema debe calcular total de gastos por categoría, por rubro y total mensual |
| RF-033 | El sistema debe permitir registrar proyecciones de gastos para meses futuros |
| RF-034 | Los formularios deben tener validación en tiempo real |
| RF-035 | El sistema debe permitir duplicar un gasto de un mes anterior (útil para gastos recurrentes con monto variable) |

---

### 1.5 Cálculo de Ahorros

| ID | Requisito Funcional |
|----|---------------------|
| RF-040 | Ahorro neto mensual = Ingresos Netos Totales − Gastos Totales |
| RF-041 | Tasa de ahorro = (Ahorro / Ingresos Netos) × 100 |
| RF-042 | Ahorro acumulado histórico = suma de ahorros mensuales positivos |
| RF-043 | El sistema debe alertar en rojo cuando el ahorro mensual sea negativo |
| RF-044 | El sistema debe mostrar comparativa de tasa de ahorro vs. meta configurada por el usuario (meta sugerida por defecto: 20%) |
| RF-045 | El sistema debe mostrar historial de ahorro mes a mes en gráfico de barras |

---

### 1.6 Créditos de Consumo

| ID | Requisito Funcional |
|----|---------------------|
| RF-050 | El sistema debe permitir registrar crédito con: nombre/entidad, tipo (bancario, cooperativa, libranza, fintech, otro), monto, tasa EA (%), plazo en meses, fecha de desembolso, descripción |
| RF-051 | Calcular cuota mensual con fórmula French: `Cuota = (P × i) / (1 − (1+i)^−n)` donde `i = (1 + EA)^(1/12) − 1` |
| RF-052 | Generar tabla de amortización completa: número cuota, fecha de pago, cuota total, intereses, capital amortizado, saldo capital |
| RF-053 | Calcular interés total pagado en la vida del crédito = Suma cuotas − Capital |
| RF-054 | Mostrar saldo vigente actualizado y cuota del mes |
| RF-055 | Permitir registrar pagos realizados y recalcular saldo automáticamente |
| RF-056 | Mostrar total de carga mensual de créditos (suma de todas las cuotas activas) |
| RF-057 | El sistema debe ofrecer tipos de entidad predefinidos en el formulario de crédito: Banco, Cooperativa/Fondos de empleados, Libranza, Fintech/Digital (Rappi Pay, Addi, etc.), Familiar/Informal, Otro — el usuario selecciona el que aplica |

---

### 1.7 Tarjetas de Crédito

| ID | Requisito Funcional |
|----|---------------------|
| RF-060 | Registrar tarjeta con: nombre/banco, límite, tasa mensual (%), saldo actual, fecha de corte, fecha límite de pago |
| RF-061 | Registrar compras con: monto, fecha, descripción, categoría, número de cuotas (1 = contado, n = diferido) |
| RF-062 | Calcular cuota mínima (el mayor entre: 5% del saldo o el mínimo definido por el banco — configurable por tarjeta) |
| RF-063 | Calcular intereses mensuales sobre saldo no pagado (tasa mensual × saldo) |
| RF-064 | Mostrar disponibilidad restante y semáforo de uso: verde (<60%), amarillo (60–80%), rojo (>80%) |
| RF-065 | Registrar pagos y actualizar saldo automáticamente |
| RF-066 | Mostrar resumen total de deuda en tarjetas |
| RF-067 | Mostrar fecha de corte y días para próximo corte |

---

### 1.8 Provisiones para Pagos Futuros

> Ver Sección 4 para el catálogo completo de provisiones sugeridas para Colombia.

| ID | Requisito Funcional |
|----|---------------------|
| RF-070 | Registrar provisión con: concepto, monto total estimado, fecha de pago, ahorro acumulado actual |
| RF-071 | Calcular automáticamente: meses restantes, ahorro mensual recomendado = (Monto − Acumulado) / Meses restantes |
| RF-072 | Calcular ahorro máximo alcanzable = ahorro mensual disponible × meses restantes |
| RF-073 | Alertar en rojo cuando el ahorro máximo alcanzable < Monto total (meta inalcanzable al ritmo actual) |
| RF-074 | Mostrar déficit proyectado cuando no se alcanza |
| RF-075 | Permitir registrar aportes mensuales y actualizar acumulado automáticamente |
| RF-076 | Mostrar barra de progreso: (Acumulado / Monto total) × 100 |
| RF-077 | Emitir recordatorio visual 2 meses antes de la fecha de pago si la provisión está por debajo del 80% del objetivo |
| RF-078 | El sistema debe cargar por defecto las provisiones sugeridas de la Sección 4 como plantillas con monto $0 para que el usuario configure las que le apliquen |

---

### 1.9 Fondo de Emergencia

| ID | Requisito Funcional |
|----|---------------------|
| RF-085 | El sistema debe calcular automáticamente el **gasto mensual esencial** del usuario (suma de categorías marcadas como "esencial": Vivienda, Alimentación, Transporte básico, Salud, Deudas obligatorias) |
| RF-086 | El sistema debe mostrar la meta del fondo de emergencia en tres niveles: mínimo (1 mes de gastos esenciales), recomendado (3 meses), ideal (6 meses) |
| RF-087 | El usuario debe poder registrar el saldo actual de su fondo de emergencia |
| RF-088 | El usuario debe poder registrar aportes mensuales al fondo |
| RF-089 | El sistema debe calcular cuántos meses faltan para alcanzar cada nivel al ritmo de aporte actual |
| RF-090 | El fondo de emergencia debe aparecer como "no disponible para gasto" en los cálculos de ahorro disponible |

---

### 1.10 Indicadores de Salud Financiera

| ID | Requisito Funcional |
|----|---------------------|
| RF-091 | **Ratio de Endeudamiento**: (Total cuotas mensuales de créditos + mínimos tarjetas) / Ingreso neto mensual × 100. Semáforo: verde (<30%), amarillo (30–40%), rojo (>40%) |
| RF-092 | **Tasa de Ahorro**: Ahorro neto / Ingreso neto × 100. Meta configurable por el usuario, sugerida 20%. Semáforo: verde (>20%), amarillo (10–20%), rojo (<10%) |
| RF-093 | **Cobertura Fondo Emergencia**: Saldo fondo / Gasto mensual esencial. Semáforo: verde (>3 meses), amarillo (1–3 meses), rojo (<1 mes) |
| RF-094 | **Presión de Gastos Fijos**: Gastos fijos mensuales / Ingreso neto × 100. Referencia: idealmente < 50% |
| RF-095 | El dashboard debe mostrar estos 4 indicadores con semáforo y tendencia respecto al mes anterior |
| RF-096 | El sistema debe generar un **diagnóstico mensual** en texto simple: máximo 3 líneas con el indicador más crítico y una recomendación concreta |

---

### 1.11 Proyecciones y Escenarios

| ID | Requisito Funcional |
|----|---------------------|
| RF-100 | Ingresar proyecciones de ingresos para meses futuros (1–24 meses) |
| RF-101 | Ingresar proyecciones de gastos por categoría para meses futuros |
| RF-102 | Calcular proyección de ahorro mensual y acumulado a 6, 12, 24 meses |
| RF-103 | Permitir crear 3 escenarios: optimista, realista, conservador |
| RF-104 | Mostrar en qué mes se alcanza la meta del fondo de emergencia según escenario seleccionado |
| RF-105 | Mostrar proyección de cierre de cada provisión activa según ritmo actual de ahorro |

---

### 1.12 Dashboard Principal

| ID | Requisito Funcional |
|----|---------------------|
| RF-110 | Resumen mensual en tarjetas: Ingresos Netos, Gastos Totales, Ahorro, Tasa de Ahorro |
| RF-111 | Gráfico de dona: distribución de gastos por categoría |
| RF-112 | Gráfico de línea: tendencia ingresos vs. gastos últimos 6 meses |
| RF-113 | Panel de 4 indicadores de salud financiera con semáforos |
| RF-114 | Lista de últimos 10 gastos registrados |
| RF-115 | Resumen de deudas: total cuotas mensuales + total saldos (créditos + tarjetas) |
| RF-116 | Lista de provisiones activas con barra de progreso y próximas en vencer |
| RF-117 | Filtro por mes/año |
| RF-118 | El dashboard debe actualizarse al registrar cualquier transacción |
| RF-119 | Widget "Prestaciones Proyectadas": prima, cesantías e intereses esperados en los próximos 12 meses |

---

### 1.13 Exportar Reportes

| ID | Requisito Funcional |
|----|---------------------|
| RF-120 | Reporte PDF mensual: resumen, gráficos, tabla de gastos, tabla de ingresos, deudas, provisiones, indicadores de salud |
| RF-121 | Exportar datos a CSV/Excel con filtro por mes o rango de fechas |
| RF-122 | El PDF debe generarse en < 3 segundos para un mes estándar |
| RF-123 | Los archivos exportados deben incluir marca de fecha de generación |

---

## 2. ESPECIFICACIONES NO FUNCIONALES

### 2.1 Rendimiento

| ID | Requisito |
|----|-----------|
| RNF-001 | Respuesta en < 2 segundos para consultas de dashboard |
| RNF-002 | Cálculos financieros (amortización, provisiones) en < 1 segundo |
| RNF-003 | Soportar hasta 10.000 registros de gastos sin degradación |
| RNF-004 | Generación de PDF en < 3 segundos |

### 2.2 Seguridad

| ID | Requisito |
|----|-----------|
| RNF-010 | Contraseñas cifradas con bcrypt (cost ≥ 12) |
| RNF-011 | Sesiones con expiración automática a 30 min de inactividad |
| RNF-012 | Protección Django integrada activa: CSRF, XSS, SQL injection (middleware de seguridad en settings) |
| RNF-013 | Datos sensibles (montos, passwords) fuera de logs |
| RNF-014 | HTTPS en producción (al migrar a cloud) |
| RNF-015 | El archivo `.env` debe estar en `.gitignore`; el repo solo incluye `.env.example` |

### 2.3 Usabilidad

| ID | Requisito |
|----|-----------|
| RNF-020 | Máximo 3 clics para registrar un gasto |
| RNF-021 | Diseño desktop-first; mobile-compatible (no roto en pantallas < 768px) |
| RNF-022 | 100% en español; montos formateados en COP (ej: $1.250.000) |
| RNF-023 | Validación en tiempo real en todos los formularios con mensajes claros |

### 2.4 Compatibilidad (v1.0 local)

| ID | Requisito |
|----|-----------|
| RNF-050 | Chrome 90+ — navegador objetivo primario |
| RNF-051 | Firefox 88+ — secundario (pruebas básicas) |
| RNF-052 | PostgreSQL 16+ |
| RNF-053 | Linux/Ubuntu 20+ o WSL2 como entorno de desarrollo |

### 2.5 Escalabilidad y Datos

| ID | Requisito |
|----|-----------|
| RNF-060 | Arquitectura Django por apps modulares; migrable a cloud (Render, Railway) sin refactor estructural |
| RNF-061 | BD soportar hasta 100.000 registros sin reestructuración |
| RNF-062 | El volumen Docker nombrado (`finanzas_postgres_data`) debe persistir ante `docker compose down` sin flag `-v` |

### 2.6 Mantenibilidad

| ID | Requisito |
|----|-----------|
| RNF-070 | PEP 8 con Black formatter; ESLint básico en JS si aplica |
| RNF-071 | Logging estructurado para diagnóstico de errores |
| RNF-072 | Variables de entorno en `.env`; ningún valor hardcodeado en el código |

### 2.7 Legal

| ID | Requisito |
|----|-----------|
| RNF-080 | Cumplimiento Ley 1581/2012 (protección de datos personales, Colombia) |
| RNF-081 | El sistema debe permitir eliminación completa de datos del usuario (derecho al olvido) |
| RNF-082 | Los cálculos financieros deben usar fórmulas financieras estándar reconocidas (French para créditos; porcentajes legales para nómina) |

---

## 3. CATÁLOGO DE CATEGORÍAS Y RUBROS SUGERIDOS

> Todas las categorías y rubros son **sugerencias editables**. El usuario puede ocultar, renombrar o agregar según su realidad. Se cargan automáticamente al crear el perfil.

---

### 🏠 VIVIENDA
*Gastos de habitación, servicios y mantenimiento del hogar*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Arriendo / Cuota hipotecaria | Fijo | |
| Energía eléctrica | Fijo | EPM, EMCALI u otro operador local |
| Agua y alcantarillado | Fijo | |
| Gas natural / cilindro | Fijo | |
| Internet | Fijo | |
| Televisión por suscripción | Fijo | Cable, Direct TV, etc. |
| Teléfono fijo | Fijo | Si aplica |
| Administración edificio/conjunto | Fijo | Si aplica |
| Seguro hogar | Fijo | Si aplica |
| Reparaciones y mantenimiento | Variable | Plomería, electricista, etc. |
| Utensilios y menaje | Variable | Elementos domésticos |

---

### 🥗 ALIMENTACIÓN
*Todo lo relacionado con comida y bebidas*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Mercado (supermercado / galería / plaza) | Variable | |
| Tienda del barrio | Variable | Compras cotidianas |
| Restaurantes | Variable | |
| Domicilios (Rappi / iFood / etc.) | Variable | |
| Almuerzo / cafetería trabajo | Variable | Si aplica |
| Snacks y bebidas | Variable | |
| Alimentación bebés y niños | Variable | Fórmula, papillas, etc. |

---

### 🚗 TRANSPORTE
*Vehículo propio, transporte público y otros medios*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Gasolina vehículo / moto | Variable | |
| SOAT | Anual → Provisión | Ver Sección 4 |
| Revisión técnico-mecánica + gases | Bienal → Provisión | Ver Sección 4 |
| Mantenimiento preventivo | Semestral → Provisión | Aceite, filtros, ajustes |
| Mantenimiento correctivo | Variable | Reparaciones imprevistas |
| Repuestos y accesorios | Variable | |
| Seguro todo riesgo vehículo | Anual → Provisión | Si aplica |
| Transporte público (metro, MIO, bus, Transmilenio) | Variable | |
| Taxi / Uber / InDriver | Variable | |
| Parqueaderos | Variable | |

---

### 🏥 SALUD
*Atención médica, medicamentos y bienestar*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Copagos / cuotas moderadoras EPS | Variable | |
| Medicamentos (POS) | Variable | |
| Medicamentos (particular / fuera de POS) | Variable | |
| Consultas médicas particulares | Variable | |
| Laboratorios y exámenes | Variable | |
| Óptica (gafas, lentes) | Variable | |
| Odontología | Variable | |
| Psicología / Terapias | Variable | |
| Emergencias médicas | Variable | |
| Salud familiares dependientes | Variable | Padres, hijos, otros |

---

### 🎓 EDUCACIÓN PROPIA
*Estudios, cursos y desarrollo profesional del titular*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Matrícula educación superior | Semestral → Provisión | Ver Sección 4 |
| Libros y materiales de estudio | Semestral → Provisión | |
| Papelería y útiles propios | Variable | |
| Cursos online y certificaciones | Variable | Plataformas digitales, bootcamps |
| Congresos y eventos técnicos | Variable | |

---

### 📚 EDUCACIÓN FAMILIA
*Educación y desarrollo de hijos u otros dependientes*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Matrícula jardín / colegio / universidad | Anual → Provisión | Ver Sección 4 |
| Útiles escolares | Anual → Provisión | |
| Libros escolares | Anual → Provisión | |
| Uniforme y calzado escolar | Anual → Provisión | |
| Transporte escolar | Fijo | Si aplica |
| Actividades extracurriculares | Variable | |

---

### 💳 DEUDAS Y CRÉDITOS
*Cuotas de créditos activos — enlazadas automáticamente con el módulo de Créditos y Tarjetas*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Cuota crédito bancario | Fijo | Enlazado con módulo Créditos |
| Cuota cooperativa / libranza | Fijo | Enlazado con módulo Créditos |
| Cuota fintech / digital | Fijo | Addi, Rappi Pay, etc. |
| Cuota tarjeta de crédito (mínimo) | Fijo | Enlazado con módulo Tarjetas |
| Cuota tarjeta de crédito (total) | Variable | Si paga más del mínimo |
| Crédito educativo | Fijo | ICETEX u otro |
| Otros créditos | Fijo | |

> **Nota de implementación:** Los rubros de deudas se sincronizan automáticamente con los módulos de Créditos y Tarjetas para evitar doble registro.

---

### 👨‍👩‍👧 FAMILIA Y DEPENDIENTES
*Gastos específicos de hijos, padres u otros dependientes*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Artículos bebé (pañales, fórmula, etc.) | Variable | |
| Ropa y calzado hijos | Variable | |
| Juguetes y material educativo | Variable | |
| Actividades recreativas familiares | Variable | |
| Apoyo económico a padres / familiares | Variable/Fijo | |
| Medicamentos familiares dependientes | Variable | |
| Controles médicos familiares | Variable | |
| Celebraciones familiares | Variable | Ver provisiones |

---

### 📱 TELECOMUNICACIONES
*Celular, internet móvil y servicios digitales*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Plan celular / datos móviles | Fijo | |
| Netflix | Fijo | |
| Spotify / música | Fijo | |
| Amazon Prime / Disney+ / otros streaming | Fijo | |
| Otras suscripciones digitales | Fijo | Herramientas de trabajo, apps de pago |

---

### 🎭 OCIO Y ENTRETENIMIENTO
*Tiempo libre, deporte y recreación*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Cine y eventos culturales | Variable | |
| Salidas y recreación | Variable | |
| Deporte (mensualidad, equipo, torneos) | Variable | |
| Libros y revistas | Variable | |
| Videojuegos / apps de pago | Variable | |
| Viajes cortos y paseos | Variable | Ver provisiones para vacaciones |

---

### 🧴 CUIDADO PERSONAL Y VESTUARIO
*Presentación personal y ropa*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Peluquería / barbería / estética | Variable | |
| Cosméticos e higiene personal | Variable | |
| Ropa adultos | Variable | |
| Calzado adultos | Variable | |
| Accesorios | Variable | |

---

### 🐾 MASCOTAS
*Animales del hogar*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Alimento / concentrado | Fijo | |
| Veterinario y vacunas | Variable | Ver provisiones para vacunas anuales |
| Medicamentos mascotas | Variable | |
| Arena sanitaria / accesorios higiene | Fijo | Si aplica |
| Accesorios y juguetes | Variable | |

---

### 🏦 AHORRO E INVERSIÓN
*Metas de ahorro y generación de patrimonio*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Fondo de emergencia | Fijo | Prioridad #1; ver módulo dedicado |
| Ahorro programado / CDT | Fijo | |
| AFC (Ahorro para Fomento de la Construcción) | Fijo | Beneficio tributario |
| Pensión voluntaria | Fijo | Beneficio tributario |
| Inversión en activos | Variable | Largo plazo |

---

### 📦 OTROS GASTOS
*Gastos que no encajan en otras categorías*

| Rubro | Tipo | Notas |
|-------|------|-------|
| Regalos (cumpleaños, navidad) | Variable | Ver provisiones |
| Donaciones | Variable | |
| Gastos imprevistos varios | Variable | |
| Trámites y documentos | Variable | Certificados, notaría, etc. |

---

## 4. PROVISIONES SUGERIDAS — COLOMBIA

> Se cargan como plantillas con monto $0 al crear el perfil. El usuario activa y configura solo las que le aplican. Los montos referenciales son orientativos; el usuario los actualiza con sus costos reales.

| # | Concepto | Periodicidad | Mes(es) de Pago | Rango Referencial COP | Categoría |
|---|---------|-------------|-----------------|----------------------|-----------|
| 1 | SOAT vehículo / moto | Anual | Según vencimiento de placa | $180.000 – $400.000 | Transporte |
| 2 | Revisión técnico-mecánica + gases | Bienal | Según vencimiento | $90.000 – $180.000 | Transporte |
| 3 | Mantenimiento preventivo vehículo | Semestral | Jun / Dic (sugerido) | $150.000 – $500.000 | Transporte |
| 4 | Seguro todo riesgo vehículo | Anual | Según póliza | Variable | Transporte |
| 5 | Matrícula educación superior | Semestral | Ene / Jun | Variable | Educación Propia |
| 6 | Libros y materiales estudio | Semestral | Ene / Jun | $200.000 – $700.000 | Educación Propia |
| 7 | Matrícula jardín / colegio (dependiente) | Anual | Enero | Variable | Educación Familia |
| 8 | Útiles y libros escolares | Anual | Enero | $150.000 – $500.000 | Educación Familia |
| 9 | Uniformes y calzado escolar | Anual / Semestral | Ene / Jun | $200.000 – $600.000 | Educación Familia |
| 10 | Regalos navidad y fin de año | Anual | Diciembre | Variable | Otros |
| 11 | Cumpleaños (persona relevante 1) | Anual | Mes de cumpleaños | Variable | Familia |
| 12 | Cumpleaños (persona relevante 2) | Anual | Mes de cumpleaños | Variable | Familia |
| 13 | Vacaciones familiares | Anual | Variable | Variable | Ocio |
| 14 | Vacunas anuales mascotas | Anual | Variable | $80.000 – $200.000 | Mascotas |
| 15 | Seguro de vida / accidentes personales | Anual | Según póliza | Variable | Salud |
| 16 | Impuesto predial (propietarios) | Anual | Abr – Jun (bimestre) | Variable | Vivienda |
| 17 | Renovación cámara de comercio (si aplica) | Anual | Enero – Mar | Variable | Otros |

> *El usuario puede agregar sus propias provisiones con cualquier concepto, monto y fecha.*

---

## 5. HISTORIAS DE USUARIO ADICIONALES

> Las HU-001 a HU-015 del documento base son válidas. Se adicionan:

### HU-016: Calcular Salario Neto desde Bruto

```
Título: Desglose nómina colombiana

Como: empleado colombiano
Quiero: ingresar mi salario bruto y que el sistema calcule mi neto automáticamente
Para: basar mis proyecciones en el dinero que realmente llega a mi cuenta

Criterios de Aceptación:
✓ Entrada: salario base bruto
✓ Salida: deducciones detalladas (salud 4%, pensión 4%, fondo solidaridad si aplica, retención)
✓ El usuario puede ingresar la retención manualmente si su empresa ya la calcula
✓ El sistema valida si el salario ≤ 2 SMLV para determinar si aplica auxilio de transporte
✓ El sistema muestra aviso cuando se deba actualizar el SMLV (enero de cada año)

Definition of Done:
- Fórmulas validadas contra liquidador DIAN
- UI muestra tabla: bruto → cada deducción → neto
- Tests con al menos 3 casos: 1 SMLV, 3 SMLV, 6 SMLV
```

### HU-017: Gestionar Fondo de Emergencia

```
Título: Seguimiento fondo de emergencia

Como: usuario que quiere seguridad financiera
Quiero: ver qué tan cubierto está mi fondo vs. mis gastos esenciales
Para: saber cuándo priorizar el fondo sobre otras metas de ahorro

Criterios de Aceptación:
✓ El sistema calcula el gasto esencial mensual automáticamente
✓ El usuario registra el saldo actual de su fondo
✓ El sistema muestra cobertura en meses y progreso hacia 1, 3 y 6 meses
✓ El sistema proyecta cuándo se alcanza cada nivel al ritmo de aporte actual
✓ El fondo aparece en dashboard como indicador de salud financiera

Definition of Done:
- Cálculo automático de gastos esenciales funciona correctamente
- Progress bar con tres niveles implementado
- Integrado con los 4 indicadores de salud financiera
```

### HU-018: Ver Indicadores de Salud Financiera

```
Título: Panel de salud financiera mensual

Como: usuario que quiere mejorar sus finanzas
Quiero: ver un diagnóstico claro de mi situación financiera cada mes
Para: tomar decisiones informadas sobre deuda, ahorro y consumo

Criterios de Aceptación:
✓ 4 indicadores visibles: Ratio endeudamiento, Tasa ahorro, Cobertura emergencia, Presión gastos fijos
✓ Semáforo verde / amarillo / rojo para cada indicador
✓ Tendencia respecto al mes anterior (↑ ↓ →)
✓ Diagnóstico en texto con recomendación concreta (máximo 3 líneas)
✓ El usuario puede ver la evolución histórica de cada indicador

Definition of Done:
- Los 4 indicadores calculan correctamente
- Semáforos con umbrales configurables por el usuario
- Diagnóstico generado automáticamente con reglas en código
- Tests con 3 escenarios: situación sana, deuda alta, sin fondo de emergencia
```

### HU-019: Proyección de Prestaciones Sociales

```
Título: Ver prestaciones proyectadas

Como: empleado colombiano
Quiero: saber cuánto recibiré de prima, cesantías e intereses
Para: planificar el uso de ese dinero antes de que llegue

Criterios de Aceptación:
✓ El sistema calcula mensualmente el acumulado proyectado de cada prestación
✓ El usuario ve el monto esperado para cada fecha de pago
✓ El sistema muestra alerta 45 días antes de cada fecha de pago
✓ El usuario puede registrar cuando la prestación fue pagada y comparar vs. proyectado

Definition of Done:
- Cálculos validados con liquidador de prestaciones social
- Alertas funcionando
- Integrado con dashboard (widget "Prestaciones Proyectadas")
```

---

## 6. DEFINICIÓN DE HECHO (DoD) — DESARROLLADOR SOLO

> Esta es la versión honesta del DoD para un proyecto de desarrollo individual con tiempo parcial. No hay peer reviewer, no hay QA dedicado, no hay product owner externo. La compensación es disciplina de proceso y pruebas enfocadas.

---

### DoD Universal — Aplica a TODA historia de usuario

```
CRITERIOS OBLIGATORIOS (sin excepción):

□ La funcionalidad cumple TODOS los criterios de aceptación de la HU
□ Código en feature branch mergeado a main via PR (aunque lo hagas tú mismo — deja registro)
□ Black formatter ejecutado: `black .` sin errores
□ Sin datos sensibles en el código (credenciales, passwords, tokens → solo en .env)
□ .env listado en .gitignore; .env.example actualizado si se agregó nueva variable
□ Sin errores de consola en Chrome al usar la funcionalidad
□ Los formularios tienen validación: campos requeridos, tipos de dato, mensajes de error claros
□ Sin bugs bloqueantes conocidos
□ Bugs menores identificados → anotados en el backlog con descripción
□ Las migraciones Django están creadas y aplicadas (`makemigrations` + `migrate`)
□ El volumen Docker sigue funcionando después de aplicar las migraciones
```

```
REVISIÓN PERSONAL ANTES DE MERGEAR (reemplaza peer review):

□ Leer el diff del PR al día siguiente, con "ojos frescos" — no el mismo día que lo escribiste
□ Probar la funcionalidad en ventana incógnito (limpia la sesión, simula usuario nuevo)
□ Verificar que el dashboard no se rompe con los nuevos datos
```

---

### DoD Extendido — Solo para módulos de LÓGICA FINANCIERA
*Aplica a: créditos (RF-050–057), nómina (RF-010–010e), provisiones (RF-070–078), indicadores (RF-091–096), fondo emergencia (RF-085–090)*

```
□ La fórmula financiera está documentada en el docstring:
  - Descripción de la fórmula
  - Referencia legal o fuente (ej: "Fórmula French. Referencia: Superfinanciera Colombia")
  - Parámetros de entrada y unidades (%, COP, meses)

□ Se usa Decimal de Python — NUNCA float para montos:
  from decimal import Decimal
  cuota = Decimal('1250000.50')   ← correcto
  cuota = 1250000.50              ← NUNCA en cálculos financieros

□ Tests unitarios para la función de cálculo con MÍNIMO 3 casos:
  - Caso mínimo (salario = 1 SMLV, crédito = monto pequeño)
  - Caso típico (valores medios de uso real)
  - Caso borde (plazo máximo, tasa alta, monto grande)

□ Resultado validado manualmente contra un simulador externo:
  - Créditos: simulador Bancolombia, Davivienda o calculadora SFC
  - Nómina: liquidador DIAN o calculadora Gerencie.com
  - Anota en el docstring el caso de prueba usado para validación
```

---

### Qué NO está en este DoD (y por qué)

| Lo que se quitó | Por qué |
|----------------|---------|
| ≥ 90% de coverage en TODAS las HU | Poco realista en solitario; concentra los tests donde importan (lógica financiera) |
| Tests en Chrome + Firefox + Safari | Chrome es suficiente para v1.0 local; Firefox al final del proyecto |
| Peer review obligatorio | Imposible solo; lo reemplaza la revisión de ojos frescos al día siguiente |
| Demo al product owner / stakeholder | Tú eres el único stakeholder; valida que lo puedes usar en tu vida real |
| Tests de performance por HU | Medir al final de cada sprint, no por historia |
| Tests OWASP por HU | Revisión de seguridad al final del proyecto, antes del release |

---

## 7. CRONOGRAMA — DESARROLLO A TIEMPO PARCIAL

> Premisa: 8–10 horas/semana disponibles. Los sprints son de 2 semanas, no de dedicación completa.

### MVP v0.1 — Valor real en 12 semanas

| Sprint | Semanas | Módulos / Historias | Entregable concreto |
|--------|---------|---------------------|---------------------|
| S1 | 1–2 | Setup: Docker + volúmenes + Django + PostgreSQL + `.env` | `docker compose up` levanta sin errores |
| S2 | 3–4 | HU-001, HU-002: Auth, sesiones, perfil con config SMLV/UVT | Login funcional con sesión y expiración |
| S3 | 5–6 | HU-003, HU-004, HU-016: Ingresos + nómina colombiana | Ingresos con neto calculado y desglose |
| S4 | 7–8 | HU-005 a HU-008: Categorías + Rubros + Gastos | Registro de gastos con catálogo sugerido |
| S5 | 9–10 | HU-009, HU-017: Ahorro + Fondo emergencia | Dashboard básico con indicadores |
| S6 | 11–12 | HU-010: Créditos con tabla de amortización | Primer crédito registrado con tabla French |

**Al final del Sprint 6 la app es usable en la vida real del usuario.**

### v1.0 Completa — 12 semanas adicionales (total ~24 semanas)

| Sprint | Semanas | Módulos / Historias |
|--------|---------|---------------------|
| S7 | 13–14 | HU-011: Tarjetas de crédito |
| S8 | 15–16 | HU-012: Provisiones + catálogo Colombia |
| S9 | 17–18 | HU-018, HU-019: Indicadores salud financiera + prestaciones |
| S10 | 19–20 | HU-014 completo: Dashboard integrado con todos los módulos |
| S11 | 21–22 | HU-013: Proyecciones y escenarios |
| S12 | 23–24 | HU-015: Exportar PDF + CSV · Pulido UI · Documentación · Release |

**Total: ~24 semanas (6 meses) para v1.0 a tiempo parcial.**

---

## 8. CONFIGURACIÓN COLOMBIANA — PARÁMETROS DEL SISTEMA

> Valores en tabla de configuración de la BD. Editables por el usuario cada enero. No hardcodeados en el código.

| Parámetro | Valor Referencial 2025 | Fuente |
|-----------|----------------------|--------|
| SMLV mensual | $1.423.500 COP | Decreto anual gobierno |
| Auxilio de transporte | $200.000 COP | Decreto anual gobierno |
| UVT (Unidad de Valor Tributario) | $49.799 COP | DIAN |
| Umbral retención fuente | 95 UVT/mes ≈ $4.730.905 | DIAN |
| Deducción salud empleado | 4% sobre salario base | Ley 100/93 |
| Deducción pensión empleado | 4% sobre salario base | Ley 100/93 |
| Umbral fondo solidaridad | > 4 SMLV | Ley 100/93 |
| Prima servicios (provisión mensual) | 8.33% del salario | CST Art. 306 |
| Cesantías (provisión mensual) | 8.33% del salario | CST Art. 249 |
| Intereses cesantías | 12% anual sobre cesantías acumuladas | Ley 52/75 |
| Cuota mínima tarjeta crédito (referencial) | 5% del saldo | Circular SFC |

---

## 9. BACKLOG — FUNCIONALIDADES FUTURAS

| ID | Funcionalidad | Prioridad |
|----|---------------|-----------|
| FU-001 | Importación de extractos bancarios CSV (Bancolombia, Davivienda, Nequi) | Alta |
| FU-002 | Multiusuario familiar con permisos (pareja, hijos mayores) | Alta |
| FU-003 | Notificaciones visuales (vencimiento SOAT, fechas de pago, provisiones al 50%) | Media |
| FU-004 | Modo offline / PWA con service workers | Alta |
| FU-005 | Metas financieras con progreso visual (carro, vivienda, viaje) | Media |
| FU-006 | Regla 50/30/20 con comparación vs. real del usuario | Media |
| FU-007 | Migración a cloud (Render / Railway + PostgreSQL gestionado) | Alta |
| FU-008 | Versión móvil optimizada o PWA | Media |
| FU-009 | Análisis automático de patrones: "este mes gastaste 23% más en alimentación que tu promedio" | Baja |
| FU-010 | Integración con APIs de pagos colombianas (Nequi, Daviplata) si abren endpoints públicos | Baja |

---

## 10. DECISIONES DE DISEÑO CRÍTICAS

### 10.1 Usar `Decimal`, nunca `float` en montos

```python
# CORRECTO — sin errores de redondeo
from decimal import Decimal
cuota = Decimal('1250000.50')
tasa_mensual = Decimal('0.019048')  # EA convertida a mensual

# INCORRECTO — produce errores acumulativos en cálculos financieros
cuota = 1250000.50
```

### 10.2 Separar "gasto con tarjeta" de "deuda de tarjeta"

Los gastos realizados con tarjeta se registran en su categoría real (Alimentación, Transporte, etc.), no en "Deudas". La deuda de tarjeta es un pasivo separado. Si no se separa, el mismo gasto aparece dos veces en los reportes de gastos.

### 10.3 Las cuotas de crédito son servicio de deuda, no gasto operativo

La cuota mensual de un crédito sí reduce el efectivo disponible y debe aparecer en el flujo de caja. Pero en el análisis financiero debe distinguirse del gasto operativo. El sistema debe mostrar ambas vistas: flujo de caja (todo) y gasto operativo (sin cuotas de deuda).

### 10.4 Ahorro ≠ lo que sobra

El sistema debe soportar la metodología "págate primero": el ahorro se registra al inicio del mes como una transacción obligatoria hacia el fondo de emergencia u otra meta, no como el residuo de lo no gastado. Esto cambia el comportamiento del dashboard: el ahorro objetivo se descuenta del disponible antes de gastos variables.

### 10.5 Los parámetros normativos van en BD, no en código

El SMLV, UVT y tasas legales cambian cada enero. Si están en el código, cada cambio requiere un despliegue. Si están en la BD (tabla `ConfiguracionFiscal`), el usuario los actualiza desde la UI en enero y todos los cálculos se recalculan automáticamente.

---

*Versión 2.1 — Junio 2026*
*App de finanzas hogar y personales — Colombia*
