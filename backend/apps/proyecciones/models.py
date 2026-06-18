from django.db import models
from django.conf import settings
from decimal import Decimal


class Escenario(models.Model):
    NOMBRES_PREDEFINIDOS = [
        ('optimista', 'Optimista'),
        ('realista', 'Realista'),
        ('conservador', 'Conservador'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    nombre = models.CharField(
        max_length=20, choices=NOMBRES_PREDEFINIDOS,
        verbose_name="Nombre del escenario",
    )
    factor_ingreso = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('1.0000'),
        verbose_name="Factor de ingreso (ej: 1.10 = +10%)",
    )
    factor_gasto = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('1.0000'),
        verbose_name="Factor de gasto (ej: 0.95 = -5%)",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Escenario"
        verbose_name_plural = "Escenarios"
        unique_together = ['usuario', 'nombre']
        ordering = ['nombre']

    def __str__(self):
        return f"{self.get_nombre_display()} — Ing: {self.factor_ingreso}x, Gas: {self.factor_gasto}x"


class ProyeccionIngreso(models.Model):
    FUENTES = [
        ('nomina', 'Nómina'),
        ('otro', 'Otro ingreso'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    escenario = models.ForeignKey(
        Escenario, on_delete=models.CASCADE, null=True, blank=True,
        verbose_name="Escenario",
    )
    mes = models.IntegerField(verbose_name="Mes")
    anio = models.IntegerField(verbose_name="Año")
    fuente = models.CharField(
        max_length=10, choices=FUENTES, default='nomina',
        verbose_name="Fuente de ingreso",
    )
    monto_proyectado = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Monto proyectado (COP)",
    )
    nota = models.TextField(blank=True, verbose_name="Nota")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proyección de ingreso"
        verbose_name_plural = "Proyecciones de ingresos"
        ordering = ['anio', 'mes', 'fuente']
        unique_together = ['usuario', 'escenario', 'mes', 'anio', 'fuente']

    def __str__(self):
        return f"{self.get_fuente_display()} — {self.mes}/{self.anio}: ${self.monto_proyectado:,.0f}"


class ProyeccionGasto(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    escenario = models.ForeignKey(
        Escenario, on_delete=models.CASCADE, null=True, blank=True,
        verbose_name="Escenario",
    )
    mes = models.IntegerField(verbose_name="Mes")
    anio = models.IntegerField(verbose_name="Año")
    categoria = models.ForeignKey(
        'gastos.Categoria', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Categoría",
    )
    monto_proyectado = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Monto proyectado (COP)",
    )
    nota = models.TextField(blank=True, verbose_name="Nota")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proyección de gasto"
        verbose_name_plural = "Proyecciones de gastos"
        ordering = ['anio', 'mes']
        unique_together = ['usuario', 'escenario', 'mes', 'anio', 'categoria']

    def __str__(self):
        cat = self.categoria.nombre if self.categoria else "Sin categoría"
        return f"{cat} — {self.mes}/{self.anio}: ${self.monto_proyectado:,.0f}"
