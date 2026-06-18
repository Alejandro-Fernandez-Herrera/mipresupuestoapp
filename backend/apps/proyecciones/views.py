from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from datetime import date

from .models import Escenario, ProyeccionIngreso, ProyeccionGasto
from .forms import EscenarioForm, ProyeccionIngresoForm, ProyeccionGastoForm
from .services import (
    calcular_ahorro_proyectado,
    calcular_mes_meta_emergencia,
    proyectar_cierre_provisiones,
)

MESES_NOMBRE = [
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

HORIZONTES = [6, 12, 24]


@login_required
def ver_proyecciones(request):
    hoy = date.today()
    escenarios = Escenario.objects.filter(usuario=request.user, activo=True)
    escenario_id = request.GET.get("escenario")
    horizonte = int(request.GET.get("horizonte", 12))
    if horizonte not in HORIZONTES:
        horizonte = 12

    escenario = None
    if escenario_id:
        escenario = get_object_or_404(Escenario, id=escenario_id, usuario=request.user)

    if not escenarios.exists():
        _crear_escenarios_defecto(request.user)
        escenarios = Escenario.objects.filter(usuario=request.user, activo=True)
        escenario = escenarios.first()

    resultados = calcular_ahorro_proyectado(request.user, horizonte, escenario)
    meta_emergencia = calcular_mes_meta_emergencia(request.user, escenario)
    cierre_provisiones = proyectar_cierre_provisiones(request.user, escenario)

    return render(
        request,
        "proyecciones/ver_proyecciones.html",
        {
            "escenarios": escenarios,
            "escenario_id": escenario.id if escenario else None,
            "escenario_actual": escenario,
            "horizonte": horizonte,
            "horizontes": HORIZONTES,
            "resultados": resultados,
            "meta_emergencia": meta_emergencia,
            "cierre_provisiones": cierre_provisiones,
            "meses_nombre": MESES_NOMBRE,
            "hoy": hoy,
        },
    )


@login_required
def configurar_escenarios(request):
    escenarios = Escenario.objects.filter(usuario=request.user)

    if request.method == "POST":
        form = EscenarioForm(request.POST)
        if form.is_valid():
            escenario = form.save(commit=False)
            escenario.usuario = request.user
            escenario.save()
            messages.success(request, "Escenario guardado correctamente.")
            return redirect("proyecciones:configurar")
    else:
        form = EscenarioForm()

    return render(
        request,
        "proyecciones/configurar_escenarios.html",
        {
            "escenarios": escenarios,
            "form": form,
        },
    )


@login_required
def api_resultados(request):
    hoy = date.today()
    escenario_id = request.GET.get("escenario")
    horizonte = int(request.GET.get("horizonte", 12))
    if horizonte not in HORIZONTES:
        horizonte = 12

    escenario = None
    if escenario_id:
        escenario = get_object_or_404(Escenario, id=escenario_id, usuario=request.user)

    resultados = calcular_ahorro_proyectado(request.user, horizonte, escenario)
    meta_emergencia = calcular_mes_meta_emergencia(request.user, escenario)
    cierre_provisiones = proyectar_cierre_provisiones(request.user, escenario)

    data = {
        "resultados": {
            "ahorro_mensual_promedio": str(resultados["ahorro_mensual_promedio"]),
            "ahorro_acumulado": str(resultados["ahorro_acumulado"]),
            "total_ingresos_acumulado": str(resultados["total_ingresos_acumulado"]),
            "total_gastos_acumulado": str(resultados["total_gastos_acumulado"]),
            "detalle_meses": [
                {
                    "mes": d["mes"],
                    "anio": d["anio"],
                    "ingresos": str(d["ingresos"]),
                    "gastos": str(d["gastos"]),
                    "ahorro": str(d["ahorro"]),
                    "mes_nombre": MESES_NOMBRE[d["mes"]],
                }
                for d in resultados["detalle_meses"]
            ],
        },
        "meta_emergencia": {
            nivel: {
                "alcanza": info["alcanza"],
                "mes": info["mes"],
                "anio": info["anio"],
                "meses_necesarios": info["meses_necesarios"],
            }
            for nivel, info in meta_emergencia.items()
        },
        "cierre_provisiones": [
            {
                "concepto": p["concepto"],
                "progreso": float(p["progreso"]),
                "alcanza": p["alcanza"],
                "meses_restantes": p["meses_restantes"],
                "deficit": str(p["deficit"]),
            }
            for p in cierre_provisiones
        ],
    }
    return JsonResponse(data)


# ============================================================
# CRUD Proyecciones de Ingreso
# ============================================================


@login_required
def listar_proyecciones_ingreso(request):
    proyecciones = (
        ProyeccionIngreso.objects.filter(usuario=request.user)
        .select_related("escenario")
        .order_by("-anio", "-mes", "fuente")
    )
    return render(
        request,
        "proyecciones/listar_ingresos.html",
        {
            "proyecciones": proyecciones,
            "meses_nombre": MESES_NOMBRE,
        },
    )


@login_required
def registrar_proyeccion_ingreso(request):
    if request.method == "POST":
        form = ProyeccionIngresoForm(request.POST, user=request.user)
        if form.is_valid():
            p = form.save(commit=False)
            p.usuario = request.user
            p.save()
            messages.success(request, "Proyección de ingreso guardada.")
            return redirect("proyecciones:ingresos")
    else:
        form = ProyeccionIngresoForm(user=request.user)
    return render(
        request, "proyecciones/form_ingreso.html", {"form": form, "accion": "Registrar"}
    )


@login_required
def editar_proyeccion_ingreso(request, pk):
    p = get_object_or_404(ProyeccionIngreso, pk=pk, usuario=request.user)
    if request.method == "POST":
        form = ProyeccionIngresoForm(request.POST, instance=p, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Proyección de ingreso actualizada.")
            return redirect("proyecciones:ingresos")
    else:
        form = ProyeccionIngresoForm(instance=p, user=request.user)
    return render(
        request, "proyecciones/form_ingreso.html", {"form": form, "accion": "Editar"}
    )


@login_required
def eliminar_proyeccion_ingreso(request, pk):
    p = get_object_or_404(ProyeccionIngreso, pk=pk, usuario=request.user)
    if request.method == "POST":
        p.delete()
        messages.success(request, "Proyección de ingreso eliminada.")
        return redirect("proyecciones:ingresos")
    return render(
        request,
        "proyecciones/confirmar_eliminar.html",
        {
            "objeto": p,
            "url_confirmar": "proyecciones:eliminar_ingreso",
            "url_cancelar": "proyecciones:ingresos",
        },
    )


# ============================================================
# CRUD Proyecciones de Gasto
# ============================================================


@login_required
def listar_proyecciones_gasto(request):
    proyecciones = (
        ProyeccionGasto.objects.filter(usuario=request.user)
        .select_related("escenario", "categoria")
        .order_by("-anio", "-mes")
    )
    return render(
        request,
        "proyecciones/listar_gastos.html",
        {
            "proyecciones": proyecciones,
            "meses_nombre": MESES_NOMBRE,
        },
    )


@login_required
def registrar_proyeccion_gasto(request):
    if request.method == "POST":
        form = ProyeccionGastoForm(request.POST, user=request.user)
        if form.is_valid():
            p = form.save(commit=False)
            p.usuario = request.user
            p.save()
            messages.success(request, "Proyección de gasto guardada.")
            return redirect("proyecciones:gastos")
    else:
        form = ProyeccionGastoForm(user=request.user)
    return render(
        request, "proyecciones/form_gasto.html", {"form": form, "accion": "Registrar"}
    )


@login_required
def editar_proyeccion_gasto(request, pk):
    p = get_object_or_404(ProyeccionGasto, pk=pk, usuario=request.user)
    if request.method == "POST":
        form = ProyeccionGastoForm(request.POST, instance=p, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Proyección de gasto actualizada.")
            return redirect("proyecciones:gastos")
    else:
        form = ProyeccionGastoForm(instance=p, user=request.user)
    return render(
        request, "proyecciones/form_gasto.html", {"form": form, "accion": "Editar"}
    )


@login_required
def eliminar_proyeccion_gasto(request, pk):
    p = get_object_or_404(ProyeccionGasto, pk=pk, usuario=request.user)
    if request.method == "POST":
        p.delete()
        messages.success(request, "Proyección de gasto eliminada.")
        return redirect("proyecciones:gastos")
    return render(
        request,
        "proyecciones/confirmar_eliminar.html",
        {
            "objeto": p,
            "url_confirmar": "proyecciones:eliminar_gasto",
            "url_cancelar": "proyecciones:gastos",
        },
    )


# ============================================================
# HELPERS
# ============================================================


def _crear_escenarios_defecto(usuario):
    """Crea los 3 escenarios por defecto para un usuario."""
    defaults = [
        ("optimista", Decimal("1.1000"), Decimal("0.9500")),
        ("realista", Decimal("1.0000"), Decimal("1.0000")),
        ("conservador", Decimal("0.9000"), Decimal("1.1000")),
    ]
    for nombre, factor_ing, factor_gas in defaults:
        Escenario.objects.get_or_create(
            usuario=usuario,
            nombre=nombre,
            defaults={
                "factor_ingreso": factor_ing,
                "factor_gasto": factor_gas,
                "activo": True,
            },
        )
