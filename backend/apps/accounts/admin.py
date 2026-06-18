from django.contrib import admin
from .models import UserProfile, ConfiguracionFiscal


@admin.register(ConfiguracionFiscal)
class ConfiguracionFiscalAdmin(admin.ModelAdmin):
    list_display = ["anio", "smlv", "auxilio_transporte", "uvt"]
    search_fields = ["anio"]
    list_filter = ["anio"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["username", "nombre_completo", "email", "ciudad", "smlv_vigente"]
    search_fields = ["username", "nombre_completo", "email"]
    list_filter = ["ciudad"]
    fieldsets = (
        (
            "Datos personales",
            {"fields": ("username", "nombre_completo", "email", "ciudad", "password")},
        ),
        (
            "Parámetros financieros",
            {
                "fields": (
                    "smlv_vigente",
                    "uvt_vigente",
                    "auxilio_transporte",
                    "meta_tasa_ahorro",
                    "configuracion_fiscal",
                )
            },
        ),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
