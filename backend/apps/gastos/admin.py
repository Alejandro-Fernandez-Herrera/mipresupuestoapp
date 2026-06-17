from django.contrib import admin
from .models import Categoria, Rubro, Gasto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'color', 'es_sugerida', 'visible', 'orden']
    list_filter = ['es_sugerida', 'visible']
    search_fields = ['nombre']


@admin.register(Rubro)
class RubroAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'tipo', 'visible']
    list_filter = ['tipo', 'visible']
    search_fields = ['nombre', 'categoria__nombre']


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'categoria', 'rubro', 'monto', 'metodo_pago', 'tipo', 'usuario']
    list_filter = ['tipo', 'metodo_pago', 'categoria', 'mes', 'anio']
    search_fields = ['descripcion', 'categoria__nombre', 'rubro__nombre']
