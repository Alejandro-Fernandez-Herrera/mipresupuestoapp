from django.contrib import admin
from .models import RegistroNomina, OtroIngreso, PrestacionSocial


@admin.register(RegistroNomina)
class RegistroNominaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'mes', 'anio', 'salario_bruto', 'salario_neto']
    list_filter = ['anio', 'mes', 'usuario']


@admin.register(OtroIngreso)
class OtroIngresoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'monto', 'mes', 'anio']
    list_filter = ['anio', 'mes', 'tipo', 'usuario']


@admin.register(PrestacionSocial)
class PrestacionSocialAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'monto_proyectado', 'fecha_pago_esperada', 'pagada']
    list_filter = ['anio', 'tipo', 'pagada', 'usuario']
