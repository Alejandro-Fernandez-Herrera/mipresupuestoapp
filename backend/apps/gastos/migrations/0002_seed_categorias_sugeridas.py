from django.db import migrations

CATEGORIAS_Y_RUBROS = [
    ("Vivienda", "#FF5722", True, [
        ("Arriendo / Cuota hipotecaria", "fijo"),
        ("Energía eléctrica", "fijo"),
        ("Agua y alcantarillado", "fijo"),
        ("Gas natural / cilindro", "fijo"),
        ("Internet", "fijo"),
        ("Televisión por suscripción", "fijo"),
        ("Teléfono fijo", "fijo"),
        ("Administración edificio/conjunto", "fijo"),
        ("Seguro hogar", "fijo"),
        ("Reparaciones y mantenimiento", "variable"),
        ("Utensilios y menaje", "variable"),
    ]),
    ("Alimentación", "#4CAF50", True, [
        ("Mercado (supermercado / galería / plaza)", "variable"),
        ("Tienda del barrio", "variable"),
        ("Restaurantes", "variable"),
        ("Domicilios (Rappi / iFood / etc.)", "variable"),
        ("Almuerzo / cafetería trabajo", "variable"),
        ("Snacks y bebidas", "variable"),
        ("Alimentación bebés y niños", "variable"),
    ]),
    ("Transporte", "#2196F3", True, [
        ("Gasolina vehículo / moto", "variable"),
        ("Transporte público (metro, MIO, bus, Transmilenio)", "variable"),
        ("Taxi / Uber / InDriver", "variable"),
        ("Parqueaderos", "variable"),
        ("Mantenimiento preventivo", "variable"),
        ("Mantenimiento correctivo", "variable"),
        ("Repuestos y accesorios", "variable"),
    ]),
    ("Salud", "#E91E63", True, [
        ("Copagos / cuotas moderadoras EPS", "variable"),
        ("Medicamentos (POS)", "variable"),
        ("Medicamentos (particular / fuera de POS)", "variable"),
        ("Consultas médicas particulares", "variable"),
        ("Laboratorios y exámenes", "variable"),
        ("Óptica (gafas, lentes)", "variable"),
        ("Odontología", "variable"),
        ("Psicología / Terapias", "variable"),
        ("Emergencias médicas", "variable"),
        ("Salud familiares dependientes", "variable"),
    ]),
    ("Educación Propia", "#9C27B0", False, [
        ("Matrícula educación superior", "variable"),
        ("Libros y materiales de estudio", "variable"),
        ("Papelería y útiles propios", "variable"),
        ("Cursos online y certificaciones", "variable"),
        ("Congresos y eventos técnicos", "variable"),
    ]),
    ("Educación Familia", "#673AB7", False, [
        ("Matrícula jardín / colegio / universidad", "variable"),
        ("Útiles escolares", "variable"),
        ("Libros escolares", "variable"),
        ("Uniforme y calzado escolar", "variable"),
        ("Transporte escolar", "fijo"),
        ("Actividades extracurriculares", "variable"),
    ]),
    ("Deudas y Créditos", "#F44336", True, [
        ("Cuota crédito bancario", "fijo"),
        ("Cuota cooperativa / libranza", "fijo"),
        ("Cuota fintech / digital", "fijo"),
        ("Cuota tarjeta de crédito (mínimo)", "fijo"),
        ("Cuota tarjeta de crédito (total)", "variable"),
        ("Crédito educativo", "fijo"),
        ("Otros créditos", "fijo"),
    ]),
    ("Familia y Dependientes", "#FF9800", False, [
        ("Artículos bebé (pañales, fórmula, etc.)", "variable"),
        ("Ropa y calzado hijos", "variable"),
        ("Juguetes y material educativo", "variable"),
        ("Actividades recreativas familiares", "variable"),
        ("Apoyo económico a padres / familiares", "variable"),
        ("Medicamentos familiares dependientes", "variable"),
        ("Controles médicos familiares", "variable"),
        ("Celebraciones familiares", "variable"),
    ]),
    ("Telecomunicaciones", "#00BCD4", False, [
        ("Plan celular / datos móviles", "fijo"),
        ("Netflix", "fijo"),
        ("Spotify / música", "fijo"),
        ("Amazon Prime / Disney+ / otros streaming", "fijo"),
        ("Otras suscripciones digitales", "fijo"),
    ]),
    ("Ocio y Entretenimiento", "#8BC34A", False, [
        ("Cine y eventos culturales", "variable"),
        ("Salidas y recreación", "variable"),
        ("Deporte (mensualidad, equipo, torneos)", "variable"),
        ("Libros y revistas", "variable"),
        ("Videojuegos / apps de pago", "variable"),
        ("Viajes cortos y paseos", "variable"),
    ]),
    ("Cuidado Personal y Vestuario", "#FFEB3B", False, [
        ("Peluquería / barbería / estética", "variable"),
        ("Cosméticos e higiene personal", "variable"),
        ("Ropa adultos", "variable"),
        ("Calzado adultos", "variable"),
        ("Accesorios", "variable"),
    ]),
    ("Mascotas", "#795548", False, [
        ("Alimento / concentrado", "fijo"),
        ("Veterinario y vacunas", "variable"),
        ("Medicamentos mascotas", "variable"),
        ("Arena sanitaria / accesorios higiene", "fijo"),
        ("Accesorios y juguetes", "variable"),
    ]),
    ("Ahorro e Inversión", "#009688", True, [
        ("Fondo de emergencia", "fijo"),
        ("Ahorro programado / CDT", "fijo"),
        ("AFC (Ahorro para Fomento de la Construcción)", "fijo"),
        ("Pensión voluntaria", "fijo"),
        ("Inversión en activos", "variable"),
    ]),
    ("Otros Gastos", "#9E9E9E", False, [
        ("Regalos (cumpleaños, navidad)", "variable"),
        ("Donaciones", "variable"),
        ("Gastos imprevistos varios", "variable"),
        ("Trámites y documentos", "variable"),
    ]),
]


def seed_categorias(apps, schema_editor):
    Categoria = apps.get_model("gastos", "Categoria")
    Rubro = apps.get_model("gastos", "Rubro")

    for orden, (cat_nombre, cat_color, es_esencial, rubros) in enumerate(CATEGORIAS_Y_RUBROS, start=1):
        categoria = Categoria.objects.create(
            nombre=cat_nombre,
            color=cat_color,
            es_sugerida=True,
            es_esencial=es_esencial,
            visible=True,
            orden=orden,
        )
        for rubro_nombre, rubro_tipo in rubros:
            Rubro.objects.create(
                categoria=categoria,
                nombre=rubro_nombre,
                tipo=rubro_tipo,
                es_sugerida=True,
                visible=True,
            )


def reverse_seed(apps, schema_editor):
    Categoria = apps.get_model("gastos", "Categoria")
    Rubro = apps.get_model("gastos", "Rubro")
    Rubro.objects.filter(es_sugerida=True).delete()
    Categoria.objects.filter(es_sugerida=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("gastos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categorias, reverse_seed),
    ]
