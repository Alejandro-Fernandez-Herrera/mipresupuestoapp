"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("ingresos/", include("apps.ingresos.urls", namespace="ingresos")),
    path("gastos/", include("apps.gastos.urls", namespace="gastos")),
    path("deudas/", include("apps.deudas.urls", namespace="deudas")),
    path("provisiones/", include("apps.provisiones.urls", namespace="provisiones")),
    path("indicadores/", include("apps.indicadores.urls", namespace="indicadores")),
    path("proyecciones/", include("apps.proyecciones.urls", namespace="proyecciones")),
    path("reportes/", include("apps.reportes.urls", namespace="reportes")),
    path("", accounts_views.dashboard, name="dashboard"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
