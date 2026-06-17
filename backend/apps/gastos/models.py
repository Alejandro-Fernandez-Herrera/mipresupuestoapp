from django.db import models
from django.conf import settings
from decimal import Decimal


class Categoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Usuario",
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    color = models.CharField(max_length=7, default="#2196F3", verbose_name="Color hex")
    icono = models.CharField(max_length=50, blank=True, verbose_name="Icono")
    es_sugerida = models.BooleanField(default=False, verbose_name="Categoría sugerida")
    es_esencial = models.BooleanField(default=False, verbose_name="Esencial para fondo emergencia")
    visible = models.BooleanField(default=True, verbose_name="Visible")
    orden = models.IntegerField(default=0, verbose_name="Orden")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class Rubro(models.Model):
    TIPO_CHOICES = [
        ('fijo', 'Fijo'),
        ('variable', 'Variable'),
    ]

    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, related_name='rubros',
        verbose_name="Categoría",
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    tipo = models.CharField(
        max_length=10, choices=TIPO_CHOICES, default='variable',
        verbose_name="Tipo",
    )
    es_sugerida = models.BooleanField(default=False, verbose_name="Rubro sugerido")
    visible = models.BooleanField(default=True, verbose_name="Visible")
    orden = models.IntegerField(default=0, verbose_name="Orden")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rubro"
        verbose_name_plural = "Rubros"
        ordering = ['categoria', 'orden', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"


class Gasto(models.Model):
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
        ('transferencia', 'Transferencia'),
        ('nequi', 'Nequi/Daviplata'),
    ]

    TIPO_CHOICES = [
        ('fijo', 'Fijo'),
        ('variable', 'Variable'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, verbose_name="Categoría",
    )
    rubro = models.ForeignKey(
        Rubro, on_delete=models.PROTECT, verbose_name="Rubro",
    )
    monto = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Monto (COP)",
    )
    fecha = models.DateField(verbose_name="Fecha")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    metodo_pago = models.CharField(
        max_length=15, choices=METODO_PAGO_CHOICES,
        default='debito', verbose_name="Método de pago",
    )
    tipo = models.CharField(
        max_length=10, choices=TIPO_CHOICES, default='variable',
        verbose_name="Tipo",
    )
    recurrente = models.BooleanField(default=False, verbose_name="Recurrente mensual")
    mes = models.IntegerField(verbose_name="Mes")
    anio = models.IntegerField(verbose_name="Año")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ['-fecha', '-creado_en']

    def __str__(self):
        return f"{self.categoria.nombre} — ${self.monto:,.0f} ({self.fecha})"
