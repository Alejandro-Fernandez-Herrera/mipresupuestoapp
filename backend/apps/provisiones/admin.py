from django.contrib import admin
from .models import FondoEmergencia, AporteFondo


@admin.register(FondoEmergencia)
class FondoEmergenciaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'saldo_actual', 'actualizado_en']


@admin.register(AporteFondo)
class AporteFondoAdmin(admin.ModelAdmin):
    list_display = ['fondo', 'monto', 'fecha', 'mes', 'anio']
    list_filter = ['mes', 'anio']
