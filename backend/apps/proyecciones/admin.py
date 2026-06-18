from django.contrib import admin
from .models import Escenario, ProyeccionIngreso, ProyeccionGasto


@admin.register(Escenario)
class EscenarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'nombre', 'factor_ingreso', 'factor_gasto', 'activo']
    list_filter = ['nombre', 'activo']
    search_fields = ['usuario__email', 'nombre']


@admin.register(ProyeccionIngreso)
class ProyeccionIngresoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'fuente', 'mes', 'anio', 'monto_proyectado', 'escenario']
    list_filter = ['fuente', 'mes', 'anio']
    search_fields = ['usuario__email']


@admin.register(ProyeccionGasto)
class ProyeccionGastoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'categoria', 'mes', 'anio', 'monto_proyectado', 'escenario']
    list_filter = ['mes', 'anio']
    search_fields = ['usuario__email']
