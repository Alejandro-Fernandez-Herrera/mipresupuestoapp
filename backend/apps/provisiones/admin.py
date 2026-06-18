from django.contrib import admin
from .models import FondoEmergencia, AporteFondo, Provision, AporteProvision


@admin.register(Provision)
class ProvisionAdmin(admin.ModelAdmin):
    list_display = ['concepto', 'usuario', 'monto_total', 'fecha_pago', 'ahorro_acumulado', 'activa']
    list_filter = ['activa', 'es_sugerida']
    search_fields = ['concepto']


@admin.register(AporteProvision)
class AporteProvisionAdmin(admin.ModelAdmin):
    list_display = ['provision', 'monto', 'fecha']
    list_filter = ['fecha']


@admin.register(FondoEmergencia)
class FondoEmergenciaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'saldo_actual', 'actualizado_en']


@admin.register(AporteFondo)
class AporteFondoAdmin(admin.ModelAdmin):
    list_display = ['fondo', 'monto', 'fecha', 'mes', 'anio']
    list_filter = ['mes', 'anio']
