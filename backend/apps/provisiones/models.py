from django.db import models
from django.conf import settings
from decimal import Decimal


class FondoEmergencia(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name="Usuario",
    )
    saldo_actual = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Saldo actual (COP)",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fondo de Emergencia"
        verbose_name_plural = "Fondos de Emergencia"

    def __str__(self):
        return f"Fondo emergencia — ${self.saldo_actual:,.0f}"


class AporteFondo(models.Model):
    fondo = models.ForeignKey(
        FondoEmergencia, on_delete=models.CASCADE, related_name='aportes',
        verbose_name="Fondo",
    )
    monto = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name="Monto (COP)",
    )
    fecha = models.DateField(verbose_name="Fecha")
    mes = models.IntegerField(verbose_name="Mes")
    anio = models.IntegerField(verbose_name="Año")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Aporte al Fondo"
        verbose_name_plural = "Aportes al Fondo"
        ordering = ['-fecha']

    def __str__(self):
        return f"Aporte ${self.monto:,.0f} ({self.fecha})"
