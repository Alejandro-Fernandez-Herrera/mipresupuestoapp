# 💰 Finanzas Hogar y Personales

Aplicación web local para la gestión de finanzas personales y del hogar, diseñada para familias colombianas. Calcula nómina con deducciones legales, gestiona gastos por categorías, amortiza créditos bajo sistema francés, y entrega indicadores de salud financiera en tiempo real.

---

## ✨ Funcionalidades

### v1.0 (completado)
- [x] Especificaciones y arquitectura
- [x] Test harness (`tests/conftest.py`)
- [x] Autenticación con sesiones individuales (30 min de inactividad)
- [x] **Módulo de nómina colombiana** — bruto → neto con deducciones legales (salud, pensión, fondo solidaridad, retención DIAN)
- [x] Registro de ingresos adicionales (horas extra, comisiones, honorarios, ingresos pasivos)
- [x] Proyección de prestaciones sociales (prima, cesantías, intereses, vacaciones)
- [x] Categorías y rubros de gastos (14 categorías sugeridas, totalmente editables)
- [x] Registro de gastos con historial mes a mes
- [x] Cálculo automático de ahorro mensual y tasa de ahorro
- [x] Fondo de emergencia con progreso hacia 1, 3 y 6 meses de cobertura
- [x] **Créditos de consumo** con tabla de amortización French completa

### v1.0 (completado)
- [x] Tarjetas de crédito (cuota mínima, semáforo de uso, intereses)
- [x] Provisiones para pagos futuros (SOAT, matrículas, vacaciones, etc.)
- [x] Indicadores de salud financiera con semáforo (ratio endeudamiento, tasa ahorro, cobertura emergencia)
- [x] Proyecciones a 6, 12 y 24 meses con escenarios optimista/realista/conservador
- [x] Dashboard con gráficos interactivos
- [x] Exportar reportes a PDF, CSV y Excel

### Backlog futuro
- [ ] Importación de extractos bancarios CSV
- [ ] Multiusuario familiar con permisos
- [ ] Modo PWA / offline
- [ ] Migración a cloud (Render / Railway)

---

## 🛠 Stack

| Capa | Tecnología |
|------|------------|
| Backend | Django 5.x + Python 3.12 |
| Base de datos | PostgreSQL 16 |
| Frontend | Django Templates + Alpine.js + Chart.js |
| PDF | WeasyPrint |
| Excel/CSV | openpyxl |
| Contenedor | Docker Compose con volúmenes nombrados |
| Tests | pytest + pytest-django + factory-boy + freezegun |

---

## 📋 Requisitos

- [Docker](https://docs.docker.com/get-docker/) >= 24.x
- [Docker Compose](https://docs.docker.com/compose/) >= 2.x
- Git

> No se requiere Python local ni PostgreSQL local. Todo corre dentro de los contenedores.

---

## 🚀 Inicio rápido

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-usuario>/finanzas-hogar.git
cd finanzas-hogar
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores (mínimo: POSTGRES_PASSWORD y SECRET_KEY)
nano .env
```

### 3. Levantar los contenedores

```bash
docker compose up -d
```

### 4. Aplicar migraciones

```bash
docker exec finanzas_web python manage.py migrate
```

### 5. Crear superusuario (opcional, para el admin de Django)

```bash
docker exec -it finanzas_web python manage.py createsuperuser
```

### 6. Abrir la aplicación

```
http://localhost:8000
```

---

## ⚙️ Variables de entorno

Copiar `.env.example` como `.env` y completar los valores:

```env
# Base de datos PostgreSQL
POSTGRES_DB=finanzas_hogar
POSTGRES_USER=finanzas_user
POSTGRES_PASSWORD=         # requerido — definir antes de levantar

# Django
SECRET_KEY=                # requerido — generar con: python -c "import secrets; print(secrets.token_urlsafe(50))"
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Zona horaria
TZ=America/Bogota
```

> ⚠️ El archivo `.env` está en `.gitignore`. Nunca commitear contraseñas al repositorio.

---

## 🐳 Comandos Docker

```bash
# Levantar (primera vez o tras cambios en docker-compose.yml)
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f web

# Bajar contenedores (los datos persisten en el volumen)
docker compose down

# Reiniciar solo el backend (tras cambios en requirements.txt o Dockerfile)
docker compose restart web

# Aplicar migraciones
docker exec finanzas_web python manage.py makemigrations
docker exec finanzas_web python manage.py migrate

# Shell Django
docker exec -it finanzas_web python manage.py shell

# Backup manual de la BD
docker exec finanzas_db pg_dump -U finanzas_user finanzas_hogar \
  > ./backups/backup_$(date +%Y%m%d).sql

# ⚠️ DESTRUCTIVO — elimina todos los datos (reset total)
docker compose down -v
```

---

## 🧪 Tests

```bash
# Todos los tests
docker exec finanzas_web pytest tests/ -v

# Solo lógica financiera
docker exec finanzas_web pytest tests/ -m financiero -v

# Solo un módulo
docker exec finanzas_web pytest tests/apps/deudas/ -v

# Con cobertura
docker exec finanzas_web pytest tests/ --cov=apps --cov-report=term-missing

# Tests rápidos (excluir tests de integración lentos)
docker exec finanzas_web pytest tests/ -m "not lento" --tb=short
```

### Marcadores disponibles

| Marcador | Qué incluye |
|----------|-------------|
| `financiero` | Toda la lógica financiera colombiana |
| `nomina` | Módulo nómina y prestaciones |
| `creditos` | Créditos y tabla de amortización French |
| `provisiones` | Provisiones de pagos futuros |
| `indicadores` | Indicadores de salud financiera |
| `integracion` | Tests con base de datos real (más lentos) |
| `lento` | Tests de performance |

---

## 📁 Estructura del proyecto

```
finanzas-hogar/
├── docker-compose.yml
├── .env.example               # plantilla — copiar como .env
├── .env                       # ignorado por git
├── CLAUDE.md                  # AI harness — contexto para asistentes de código
├── README.md
├── backups/                   # dumps manuales de la BD
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt   # pytest, factory-boy, freezegun
│   ├── manage.py
│   ├── pytest.ini
│   │
│   ├── config/                # configuración del proyecto Django
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   │
│   ├── apps/
│   │   ├── accounts/          # autenticación, perfil, parámetros fiscales
│   │   ├── ingresos/          # nómina, prestaciones, otros ingresos
│   │   ├── gastos/            # categorías, rubros, transacciones
│   │   ├── deudas/            # créditos de consumo, tarjetas de crédito
│   │   ├── provisiones/       # pagos futuros, fondo de emergencia
│   │   ├── indicadores/       # salud financiera (sin modelos propios)
│   │   └── reportes/          # PDF, CSV (sin modelos propios)
│   │
│   ├── templates/             # Django Templates HTML
│   └── tests/
│       ├── conftest.py        # harness de tests — fixtures, factories, casos
│       └── apps/
│           ├── ingresos/
│           ├── gastos/
│           ├── deudas/
│           ├── provisiones/
│           └── indicadores/
│
└── static/
    ├── js/
    └── css/
```

---

## 🇨🇴 Parámetros Colombia 2025

La app usa parámetros normativos almacenados en base de datos, editables cada enero cuando el gobierno actualiza los decretos.

| Parámetro | Valor 2025 | Fuente |
|-----------|-----------|--------|
| SMLV mensual | $1.423.500 | Decreto anual |
| Auxilio de transporte | $200.000 | Decreto anual |
| UVT | $49.799 | DIAN |
| Umbral retención | 95 UVT/mes ≈ $4.730.905 | DIAN |
| Deducción salud (empleado) | 4% | Ley 100/93 |
| Deducción pensión (empleado) | 4% | Ley 100/93 |
| Fondo solidaridad | 1% si salario > 4 SMLV | Ley 100/93 |
| Prima mensual (factor) | 8.33% | CST Art. 306 |
| Cesantías (factor) | 8.33% | CST Art. 249 |
| Intereses cesantías | 12% anual | Ley 52/75 |

Para actualizar los valores: ir a **Configuración → Parámetros Fiscales** dentro de la app.

---

## 🗺 Roadmap

| Versión | Semanas | Contenido |
|---------|---------|-----------|
| **v0.1 MVP** | 1–12 | Auth, ingresos, categorías, gastos, ahorro, fondo emergencia, créditos |
| **v1.0** | 13–24 | Tarjetas, provisiones, indicadores, dashboard completo, proyecciones, exportar |
| **v1.1** | Post-24 | Importar extractos CSV, multiusuario familiar |
| **v2.0** | Futuro | Migración a cloud, PWA, análisis automático |

Ver especificaciones completas en `docs/specs-finanzas-v2.md`.

---

## 📝 Desarrollo

Este es un proyecto de desarrollo individual. Convenciones de trabajo:

- Una branch por historia de usuario: `feature/HU-010-creditos-french`
- PR a `main` aunque sea el mismo desarrollador (deja registro del diff)
- Revisar el PR al día siguiente con "ojos frescos" antes de mergear
- Bugs menores → issue en el backlog, no bloquean el merge
- Tests obligatorios solo para lógica financiera (créditos, nómina, provisiones, indicadores)

---

## 📄 Licencia

MIT — ver `LICENSE`

---

*Colombia · 2026*
