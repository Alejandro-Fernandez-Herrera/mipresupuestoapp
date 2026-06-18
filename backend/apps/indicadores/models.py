from django.db import models
from django.conf import settings
from decimal import Decimal


class HistorialIndicador(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    mes = models.IntegerField(verbose_name="Mes")
    anio = models.IntegerField(verbose_name="Año")

    ratio_endeudamiento = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0'),
        verbose_name="Ratio de endeudamiento (%)",
    )
    semaforo_endeudamiento = models.CharField(
        max_length=10, default='verde',
        verbose_name="Semáforo endeudamiento",
    )
    tasa_ahorro = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0'),
        verbose_name="Tasa de ahorro (%)",
    )
    semaforo_ahorro = models.CharField(
        max_length=10, default='verde',
        verbose_name="Semáforo ahorro",
    )
    cobertura_emergencia = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0'),
        verbose_name="Cobertura fondo emergencia (meses)",
    )
    semaforo_emergencia = models.CharField(
        max_length=10, default='verde',
        verbose_name="Semáforo emergencia",
    )
    presion_gastos_fijos = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0'),
        verbose_name="Presión de gastos fijos (%)",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de Indicador"
        verbose_name_plural = "Historial de Indicadores"
        ordering = ['-anio', '-mes']
        unique_together = ['usuario', 'mes', 'anio']

    def __str__(self):
        return f"Indicadores {self.mes}/{self.anio} — {self.usuario.email}"
