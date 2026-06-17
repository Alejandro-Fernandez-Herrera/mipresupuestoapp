from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class TarjetaCredito(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre / Banco")
    banco = models.CharField(max_length=150, verbose_name="Banco / Entidad")
    limite = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Límite (COP)",
    )
    tasa_mensual = models.DecimalField(
        max_digits=8, decimal_places=6,
        verbose_name="Tasa mensual (decimal, ej: 0.0234 para 2.34%)",
    )
    saldo_actual = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Saldo actual (COP)",
    )
    fecha_corte = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Día de corte (1–31)",
    )
    fecha_limite_pago = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Día límite de pago (1–31)",
    )
    cuota_minima_pct = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.05'),
        verbose_name="% cuota mínima sobre saldo",
        help_text="Porcentaje como decimal (ej: 0.05 = 5%%)",
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tarjeta de Crédito"
        verbose_name_plural = "Tarjetas de Crédito"
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.nombre} — {self.banco} (${self.limite:,.0f})"

    @property
    def disponible(self):
        return Decimal('0') if self.saldo_actual >= self.limite else self.limite - self.saldo_actual

    @property
    def porcentaje_uso(self):
        if self.limite <= 0:
            return Decimal('0')
        return (self.saldo_actual / self.limite * Decimal('100')).quantize(Decimal('1'))


class CompraTC(models.Model):
    tarjeta = models.ForeignKey(
        TarjetaCredito, on_delete=models.CASCADE, related_name='compras',
        verbose_name="Tarjeta",
    )
    monto = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Monto (COP)",
    )
    fecha = models.DateField(verbose_name="Fecha de compra")
    descripcion = models.CharField(max_length=250, verbose_name="Descripción")
    categoria = models.CharField(max_length=100, blank=True, verbose_name="Categoría")
    numero_cuotas = models.IntegerField(
        default=1,
        verbose_name="Número de cuotas",
        help_text="1 = contado, >1 = diferido",
    )
    monto_cuota = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Monto por cuota (COP)",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Compra Tarjeta de Crédito"
        verbose_name_plural = "Compras Tarjeta de Crédito"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.descripcion} — ${self.monto:,.0f} ({self.tarjeta.nombre})"


class Credito(models.Model):
    TIPOS_ENTIDAD = [
        ('bancario', 'Banco'),
        ('cooperativa', 'Cooperativa / Fondos de empleados'),
        ('libranza', 'Libranza'),
        ('fintech', 'Fintech / Digital (Rappi Pay, Addi, etc.)'),
        ('familiar', 'Familiar / Informal'),
        ('otro', 'Otro'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre / Entidad")
    entidad_tipo = models.CharField(
        max_length=15, choices=TIPOS_ENTIDAD, default='bancario',
        verbose_name="Tipo de entidad",
    )
    capital = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Monto del crédito (COP)",
    )
    tasa_ea = models.DecimalField(
        max_digits=8, decimal_places=6,
        verbose_name="Tasa EA (como decimal, ej: 0.25 para 25%)",
    )
    plazo_meses = models.IntegerField(verbose_name="Plazo (meses)")
    fecha_desembolso = models.DateField(verbose_name="Fecha de desembolso")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Crédito"
        verbose_name_plural = "Créditos"
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.nombre} — ${self.capital:,.0f} @ {float(self.tasa_ea)*100:.1f}% EA"


class CuotaCredito(models.Model):
    credito = models.ForeignKey(
        Credito, on_delete=models.CASCADE, related_name='cuotas',
        verbose_name="Crédito",
    )
    numero = models.IntegerField(verbose_name="Número de cuota")
    fecha_pago = models.DateField(verbose_name="Fecha de pago")
    cuota_total = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Cuota total (COP)",
    )
    interes = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Interés (COP)",
    )
    capital_amortizado = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Capital amortizado (COP)",
    )
    saldo_capital = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Saldo capital (COP)",
    )
    pagada = models.BooleanField(default=False, verbose_name="Pagada")
    fecha_pago_real = models.DateField(null=True, blank=True, verbose_name="Fecha de pago real")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cuota de Crédito"
        verbose_name_plural = "Cuotas de Crédito"
        ordering = ['credito', 'numero']
        unique_together = ['credito', 'numero']

    def __str__(self):
        return f"Cuota #{self.numero} — ${self.cuota_total:,.0f}"
