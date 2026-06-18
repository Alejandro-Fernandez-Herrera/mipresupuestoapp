from django.contrib import admin
from .models import HistorialIndicador


@admin.register(HistorialIndicador)
class HistorialIndicadorAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'mes', 'anio', 'tasa_ahorro', 'ratio_endeudamiento',
                    'cobertura_emergencia', 'presion_gastos_fijos']
    list_filter = ['anio', 'mes', 'usuario']
