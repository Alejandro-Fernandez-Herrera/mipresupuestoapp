from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from decimal import Decimal


class BaseModel(models.Model):
    """Modelo base con auditoría — todos los modelos deben heredar de este."""
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ConfiguracionFiscal(BaseModel):
    """Parámetros normativos editables por año. No hardcodear en código."""
    anio = models.IntegerField(unique=True, verbose_name="Año vigente")

    smlv = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="SMLV mensual (COP)"
    )
    auxilio_transporte = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Auxilio de transporte (COP)"
    )
    uvt = models.DecimalField(
        max_digits=14, decimal_places=4,
        verbose_name="UVT (COP)"
    )
    umbral_retencion_uvt = models.DecimalField(
        max_digits=6, decimal_places=2,
        default=Decimal('95'),
        verbose_name="Umbral retención (UVT/mes)"
    )

    tasa_salud_empleado = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.04'),
        verbose_name="Tasa salud empleado (%)"
    )
    tasa_pension_empleado = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.04'),
        verbose_name="Tasa pensión empleado (%)"
    )

    umbral_solidaridad_smlv = models.DecimalField(
        max_digits=4, decimal_places=1,
        default=Decimal('4'),
        verbose_name="Umbral solidaridad (SMLV)"
    )
    tasa_solidaridad_4_16 = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.01'),
        verbose_name="Solidaridad 4–16 SMLV (%)"
    )
    tasa_solidaridad_16_17 = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.012'),
        verbose_name="Solidaridad 16–17 SMLV (%)"
    )
    tasa_solidaridad_17_18 = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.014'),
        verbose_name="Solidaridad 17–18 SMLV (%)"
    )
    tasa_solidaridad_18_19 = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.016'),
        verbose_name="Solidaridad 18–19 SMLV (%)"
    )
    tasa_solidaridad_19_20 = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.018'),
        verbose_name="Solidaridad 19–20 SMLV (%)"
    )
    tasa_solidaridad_mas_20 = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.02'),
        verbose_name="Solidaridad >20 SMLV (%)"
    )

    factor_prima_mensual = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.0833'),
        verbose_name="Factor prima mensual (%)"
    )
    factor_cesantias_mensual = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.0833'),
        verbose_name="Factor cesantías mensual (%)"
    )
    tasa_intereses_cesantias = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.12'),
        verbose_name="Tasa intereses cesantías anual (%)"
    )
    factor_vacaciones_mensual = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('0.0417'),
        verbose_name="Factor vacaciones mensual (%)"
    )

    cuota_minima_tc_pct = models.DecimalField(
        max_digits=5, decimal_places=4,
        default=Decimal('0.05'),
        verbose_name="Cuota mínima TC (% del saldo)"
    )

    class Meta:
        verbose_name = "Configuración Fiscal"
        verbose_name_plural = "Configuraciones Fiscales"
        ordering = ['-anio']

    def __str__(self):
        return f"Configuración Fiscal {self.anio}"


class UserProfile(AbstractUser, BaseModel):
    """Perfil de usuario extendido con configuración personal."""
    email = models.EmailField(unique=True, verbose_name="Email")
    nombre_completo = models.CharField(max_length=150, verbose_name="Nombre completo")
    ciudad = models.CharField(max_length=100, default="Bogotá", verbose_name="Ciudad")

    smlv_vigente = models.DecimalField(
        max_digits=14, decimal_places=2,
        default=Decimal('1423500'),
        verbose_name="SMLV vigente (COP)"
    )
    uvt_vigente = models.DecimalField(
        max_digits=14, decimal_places=4,
        default=Decimal('49799'),
        verbose_name="UVT vigente (COP)"
    )
    auxilio_transporte = models.DecimalField(
        max_digits=14, decimal_places=2,
        default=Decimal('200000'),
        verbose_name="Auxilio transporte (COP)"
    )
    meta_tasa_ahorro = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('20.0'),
        verbose_name="Meta tasa ahorro (%)"
    )

    configuracion_fiscal = models.ForeignKey(
        ConfiguracionFiscal,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name="Configuración fiscal activa"
    )

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        return self.nombre_completo or self.username

    def get_config_fiscal(self):
        """Retorna la configuración fiscal del usuario o la más reciente."""
        if self.configuracion_fiscal:
            return self.configuracion_fiscal
        return ConfiguracionFiscal.objects.order_by('-anio').first()

    def save(self, *args, **kwargs):
        if not self.configuracion_fiscal:
            self.configuracion_fiscal = ConfiguracionFiscal.objects.order_by('-anio').first()
        super().save(*args, **kwargs)