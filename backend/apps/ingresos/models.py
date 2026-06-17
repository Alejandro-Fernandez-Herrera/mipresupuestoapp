from django.db import models
from django.conf import settings
from decimal import Decimal


class RegistroNomina(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    salario_bruto = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Salario bruto (COP)",
    )
    mes = models.IntegerField(verbose_name="Mes")
    anio = models.IntegerField(verbose_name="Año")

    deduccion_salud = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Deducción salud (COP)",
    )
    deduccion_pension = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Deducción pensión (COP)",
    )
    deduccion_solidaridad = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Deducción fondo solidaridad (COP)",
    )
    retencion_fuente = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Retención en la fuente (COP)",
    )
    salario_neto = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Salario neto (COP)",
    )
    aplica_auxilio = models.BooleanField(
        default=False,
        verbose_name="Aplica auxilio de transporte",
    )
    auxilio_transporte = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Auxilio de transporte (COP)",
    )
    neto_con_auxilio = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Neto con auxilio (COP)",
    )
    recurrente = models.BooleanField(
        default=False,
        verbose_name="Recurrente mensual",
    )
    calculado_automaticamente = models.BooleanField(
        default=True,
        verbose_name="Calculado automáticamente",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Registro de Nómina"
        verbose_name_plural = "Registros de Nómina"
        ordering = ['-anio', '-mes']
        unique_together = ['usuario', 'mes', 'anio']

    def __str__(self):
        return f"Nómina {self.mes}/{self.anio} — ${self.salario_bruto:,.0f}"


class OtroIngreso(models.Model):
    TIPOS_INGRESO = [
        ('auxilio_transporte', 'Auxilio de transporte'),
        ('hora_extra_diurna', 'Hora extra diurna (+25%)'),
        ('hora_extra_nocturna', 'Hora extra nocturna (+75%)'),
        ('dominical_festivo', 'Dominical y festivo (+75%)'),
        ('comision', 'Comisión'),
        ('bonificacion', 'Bonificación no salarial'),
        ('honorarios', 'Honorarios / Freelance'),
        ('ingreso_pasivo', 'Ingreso pasivo (arriendos, dividendos)'),
        ('prima_junio', 'Prima de Servicios — Junio'),
        ('prima_diciembre', 'Prima de Servicios — Diciembre'),
        ('otro', 'Otro'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    tipo = models.CharField(
        max_length=30, choices=TIPOS_INGRESO,
        verbose_name="Tipo de ingreso",
    )
    monto = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Monto (COP)",
    )
    mes = models.IntegerField(verbose_name="Mes")
    anio = models.IntegerField(verbose_name="Año")
    descripcion = models.TextField(
        blank=True, verbose_name="Descripción",
    )
    recurrente = models.BooleanField(
        default=False,
        verbose_name="Recurrente mensual",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Otro Ingreso"
        verbose_name_plural = "Otros Ingresos"
        ordering = ['-anio', '-mes']

    def __str__(self):
        return f"{self.get_tipo_display()} — ${self.monto:,.0f} ({self.mes}/{self.anio})"


class PrestacionSocial(models.Model):
    TIPOS_PRESTACION = [
        ('prima_servicios', 'Prima de Servicios'),
        ('cesantias', 'Cesantías'),
        ('intereses_cesantias', 'Intereses de Cesantías'),
        ('vacaciones', 'Vacaciones'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    tipo = models.CharField(
        max_length=25, choices=TIPOS_PRESTACION,
        verbose_name="Tipo de prestación",
    )
    salario_base = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Salario base del cálculo (COP)",
    )
    monto_proyectado = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Monto proyectado (COP)",
    )
    meses_acumulados = models.IntegerField(
        default=1,
        verbose_name="Meses acumulados",
    )
    anio = models.IntegerField(verbose_name="Año")
    fecha_pago_esperada = models.DateField(
        verbose_name="Fecha de pago esperada",
    )
    pagada = models.BooleanField(
        default=False,
        verbose_name="Pagada",
    )
    fecha_pago_real = models.DateField(
        null=True, blank=True,
        verbose_name="Fecha de pago real",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Prestación Social"
        verbose_name_plural = "Prestaciones Sociales"
        ordering = ['fecha_pago_esperada']

    def __str__(self):
        return f"{self.get_tipo_display()} — ${self.monto_proyectado:,.0f} ({self.fecha_pago_esperada})"
