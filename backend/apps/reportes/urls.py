from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    path("pdf/", views.reporte_pdf, name="reporte_pdf"),
    path("csv/", views.exportar_csv_view, name="exportar_csv"),
    path("excel/", views.exportar_excel_view, name="exportar_excel"),
]
