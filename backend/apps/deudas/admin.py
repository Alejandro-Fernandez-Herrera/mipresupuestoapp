from django.contrib import admin
from .models import Credito, CuotaCredito, TarjetaCredito, CompraTC


@admin.register(TarjetaCredito)
class TarjetaCreditoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'banco', 'usuario', 'limite', 'saldo_actual', 'activa']
    list_filter = ['banco', 'activa']
    search_fields = ['nombre', 'banco']


@admin.register(CompraTC)
class CompraTCAdmin(admin.ModelAdmin):
    list_display = ['tarjeta', 'descripcion', 'monto', 'fecha', 'numero_cuotas']
    list_filter = ['tarjeta', 'fecha']


@admin.register(Credito)
class CreditoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'usuario', 'entidad_tipo', 'capital', 'tasa_ea', 'plazo_meses', 'activo']
    list_filter = ['entidad_tipo', 'activo']
    search_fields = ['nombre', 'descripcion']


@admin.register(CuotaCredito)
class CuotaCreditoAdmin(admin.ModelAdmin):
    list_display = ['credito', 'numero', 'fecha_pago', 'cuota_total', 'interes', 'capital_amortizado', 'saldo_capital', 'pagada']
    list_filter = ['pagada']
