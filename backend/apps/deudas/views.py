from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from datetime import date
from .models import Credito, CuotaCredito, TarjetaCredito, CompraTC
from .forms import CreditoForm, TarjetaCreditoForm, CompraTCForm, PagoTCForm
from .services import (
    calcular_cuota_mensual,
    generar_tabla_amortizacion,
    calcular_interes_total,
    calcular_tasa_mensual,
    calcular_cuota_minima,
    calcular_intereses_tc,
    obtener_semaforo_uso,
    calcular_disponible,
    calcular_dias_proximo_corte,
    calcular_pago_diferido,
)


@login_required
def listar_creditos(request):
    creditos = Credito.objects.filter(usuario=request.user).order_by("-creado_en")

    resultados = []
    total_carga_mensual = Decimal("0")
    total_saldo = Decimal("0")

    for c in creditos:
        cuota = calcular_cuota_mensual(c.capital, c.tasa_ea, c.plazo_meses)
        cuotas_pagadas = c.cuotas.filter(pagada=True).count()
        interes_total = calcular_interes_total(c.capital, c.tasa_ea, c.plazo_meses)
        saldo_actual = _calcular_saldo_actual(c)

        if c.activo:
            total_carga_mensual += cuota
            total_saldo += saldo_actual

        resultados.append(
            {
                "credito": c,
                "cuota_mensual": cuota,
                "interes_total": interes_total,
                "saldo_actual": saldo_actual,
                "cuotas_pagadas": cuotas_pagadas,
            }
        )

    return render(
        request,
        "deudas/lista.html",
        {
            "resultados": resultados,
            "total_carga_mensual": total_carga_mensual,
            "total_saldo": total_saldo,
        },
    )


def _calcular_saldo_actual(credito):
    ultima_cuota = credito.cuotas.filter(pagada=True).order_by("-numero").first()
    if not ultima_cuota:
        cuota = calcular_cuota_mensual(
            credito.capital, credito.tasa_ea, credito.plazo_meses
        )
        return credito.capital
    return ultima_cuota.saldo_capital


@login_required
def registrar_credito(request):
    if request.method == "POST":
        form = CreditoForm(request.POST)
        if form.is_valid():
            credito = form.save(commit=False)
            credito.usuario = request.user
            credito.save()

            tabla = generar_tabla_amortizacion(credito)
            cuotas = []
            for fila in tabla:
                cuotas.append(
                    CuotaCredito(
                        credito=credito,
                        numero=fila["numero"],
                        fecha_pago=fila["fecha_pago"],
                        cuota_total=fila["cuota_total"],
                        interes=fila["interes"],
                        capital_amortizado=fila["capital_amortizado"],
                        saldo_capital=fila["saldo_capital"],
                    )
                )
            CuotaCredito.objects.bulk_create(cuotas)

            messages.success(request, "Crédito registrado correctamente.")
            return redirect("dashboard")
    else:
        form = CreditoForm()

    return render(
        request,
        "deudas/registrar.html",
        {
            "form": form,
            "titulo": "Registrar Crédito",
        },
    )


@login_required
def detalle_credito(request, credito_id):
    credito = get_object_or_404(Credito, id=credito_id, usuario=request.user)
    cuotas = credito.cuotas.all().order_by("numero")

    cuota = calcular_cuota_mensual(
        credito.capital, credito.tasa_ea, credito.plazo_meses
    )
    interes_total = calcular_interes_total(
        credito.capital, credito.tasa_ea, credito.plazo_meses
    )
    tasa_mensual = calcular_tasa_mensual(credito.tasa_ea)
    saldo_actual = _calcular_saldo_actual(credito)
    cuotas_pagadas = cuotas.filter(pagada=True).count()

    return render(
        request,
        "deudas/detalle.html",
        {
            "credito": credito,
            "cuotas": cuotas,
            "cuota_mensual": cuota,
            "interes_total": interes_total,
            "tasa_mensual": tasa_mensual,
            "saldo_actual": saldo_actual,
            "cuotas_pagadas": cuotas_pagadas,
            "progreso": (
                int((cuotas_pagadas / credito.plazo_meses) * 100)
                if credito.plazo_meses > 0
                else 0
            ),
        },
    )


@login_required
def editar_credito(request, credito_id):
    credito = get_object_or_404(Credito, id=credito_id, usuario=request.user)

    if credito.cuotas.filter(pagada=True).exists():
        messages.error(
            request, "No puedes editar un crédito que ya tiene pagos registrados."
        )
        return redirect("deudas:detalle", credito_id=credito.id)

    if request.method == "POST":
        form = CreditoForm(request.POST, instance=credito)
        if form.is_valid():
            credito = form.save()
            credito.cuotas.all().delete()
            tabla = generar_tabla_amortizacion(credito)
            cuotas = []
            for fila in tabla:
                cuotas.append(
                    CuotaCredito(
                        credito=credito,
                        numero=fila["numero"],
                        fecha_pago=fila["fecha_pago"],
                        cuota_total=fila["cuota_total"],
                        interes=fila["interes"],
                        capital_amortizado=fila["capital_amortizado"],
                        saldo_capital=fila["saldo_capital"],
                    )
                )
            CuotaCredito.objects.bulk_create(cuotas)
            messages.success(request, "Crédito actualizado correctamente.")
            return redirect("deudas:detalle", credito_id=credito.id)
    else:
        form = CreditoForm(instance=credito)

    return render(
        request,
        "deudas/registrar.html",
        {
            "form": form,
            "titulo": "Editar Crédito",
        },
    )


@login_required
def eliminar_credito(request, credito_id):
    credito = get_object_or_404(Credito, id=credito_id, usuario=request.user)
    credito.delete()
    messages.success(request, "Crédito eliminado.")
    return redirect("deudas:lista")


@login_required
def registrar_pago(request, credito_id):
    credito = get_object_or_404(Credito, id=credito_id, usuario=request.user)

    if request.method == "POST":
        try:
            cuota_id = int(request.POST.get("cuota_id", "0"))
        except (ValueError, TypeError):
            cuota_id = 0

        cuota = get_object_or_404(CuotaCredito, id=cuota_id, credito=credito)

        if cuota.pagada:
            messages.warning(request, f"La cuota #{cuota.numero} ya estaba pagada.")
            return redirect("deudas:detalle", credito_id=credito.id)

        cuota.pagada = True
        cuota.fecha_pago_real = date.today()
        cuota.save()

        messages.success(request, f"Pago de cuota #{cuota.numero} registrado.")
        return redirect("deudas:detalle", credito_id=credito.id)

    return redirect("deudas:detalle", credito_id=credito.id)


@login_required
def desactivar_credito(request, credito_id):
    credito = get_object_or_404(Credito, id=credito_id, usuario=request.user)
    credito.activo = not credito.activo
    credito.save()
    estado = "activado" if credito.activo else "desactivado"
    messages.success(request, f'Crédito "{credito.nombre}" {estado}.')
    return redirect("deudas:lista")


# ============================================================
# VISTAS TARJETAS DE CRÉDITO
# ============================================================


@login_required
def listar_tarjetas(request):
    tarjetas = TarjetaCredito.objects.filter(usuario=request.user).order_by(
        "-creado_en"
    )

    resultados = []
    total_saldo = Decimal("0")
    total_limite = Decimal("0")
    total_cuota_minima = Decimal("0")

    for t in tarjetas:
        disponible = calcular_disponible(t.limite, t.saldo_actual)
        pct_uso = t.porcentaje_uso
        semaforo = obtener_semaforo_uso(pct_uso)
        cuota_min = calcular_cuota_minima(t.saldo_actual, t.cuota_minima_pct)

        if t.activa:
            total_saldo += t.saldo_actual
            total_limite += t.limite
            total_cuota_minima += cuota_min

        resultados.append(
            {
                "tarjeta": t,
                "disponible": disponible,
                "porcentaje_uso": pct_uso,
                "semaforo": semaforo,
                "cuota_minima": cuota_min,
            }
        )

    return render(
        request,
        "deudas/tarjetas_lista.html",
        {
            "resultados": resultados,
            "total_saldo": total_saldo,
            "total_limite": total_limite,
            "total_cuota_minima": total_cuota_minima,
        },
    )


@login_required
def registrar_tarjeta(request):
    if request.method == "POST":
        form = TarjetaCreditoForm(request.POST)
        if form.is_valid():
            tarjeta = form.save(commit=False)
            tarjeta.usuario = request.user
            tarjeta.save()
            messages.success(request, "Tarjeta registrada correctamente.")
            return redirect("dashboard")
    else:
        form = TarjetaCreditoForm()

    return render(
        request,
        "deudas/tarjetas_registrar.html",
        {
            "form": form,
            "titulo": "Registrar Tarjeta de Crédito",
        },
    )


@login_required
def detalle_tarjeta(request, tarjeta_id):
    tarjeta = get_object_or_404(TarjetaCredito, id=tarjeta_id, usuario=request.user)
    compras = tarjeta.compras.all().order_by("-fecha")

    disponible = calcular_disponible(tarjeta.limite, tarjeta.saldo_actual)
    pct_uso = tarjeta.porcentaje_uso
    semaforo = obtener_semaforo_uso(pct_uso)
    cuota_min = calcular_cuota_minima(tarjeta.saldo_actual, tarjeta.cuota_minima_pct)
    intereses = calcular_intereses_tc(tarjeta.saldo_actual, tarjeta.tasa_mensual)
    dias_corte = calcular_dias_proximo_corte(tarjeta.fecha_corte)
    total_compras_mes = compras.filter(
        fecha__month=timezone.now().month,
        fecha__year=timezone.now().year,
    ).aggregate(total=Sum("monto"))["total"] or Decimal("0")

    pago_form = PagoTCForm()

    return render(
        request,
        "deudas/tarjetas_detalle.html",
        {
            "tarjeta": tarjeta,
            "compras": compras,
            "disponible": disponible,
            "porcentaje_uso": pct_uso,
            "semaforo": semaforo,
            "cuota_minima": cuota_min,
            "intereses": intereses,
            "dias_corte": dias_corte,
            "total_compras_mes": total_compras_mes,
            "pago_form": pago_form,
        },
    )


@login_required
def editar_tarjeta(request, tarjeta_id):
    tarjeta = get_object_or_404(TarjetaCredito, id=tarjeta_id, usuario=request.user)

    if request.method == "POST":
        form = TarjetaCreditoForm(request.POST, instance=tarjeta)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarjeta actualizada correctamente.")
            return redirect("deudas:detalle_tarjeta", tarjeta_id=tarjeta.id)
    else:
        form = TarjetaCreditoForm(instance=tarjeta)

    return render(
        request,
        "deudas/tarjetas_registrar.html",
        {
            "form": form,
            "titulo": "Editar Tarjeta de Crédito",
        },
    )


@login_required
def eliminar_tarjeta(request, tarjeta_id):
    tarjeta = get_object_or_404(TarjetaCredito, id=tarjeta_id, usuario=request.user)
    tarjeta.delete()
    messages.success(request, "Tarjeta eliminada.")
    return redirect("deudas:lista_tarjetas")


@login_required
def toggle_tarjeta(request, tarjeta_id):
    tarjeta = get_object_or_404(TarjetaCredito, id=tarjeta_id, usuario=request.user)
    tarjeta.activa = not tarjeta.activa
    tarjeta.save()
    estado = "activada" if tarjeta.activa else "desactivada"
    messages.success(request, f'Tarjeta "{tarjeta.nombre}" {estado}.')
    return redirect("deudas:lista_tarjetas")


@login_required
def registrar_compra_tc(request, tarjeta_id):
    tarjeta = get_object_or_404(TarjetaCredito, id=tarjeta_id, usuario=request.user)

    if request.method == "POST":
        form = CompraTCForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.tarjeta = tarjeta
            if compra.numero_cuotas > 1:
                compra.monto_cuota = calcular_pago_diferido(
                    compra.monto, compra.numero_cuotas
                )
            tarjeta.saldo_actual += compra.monto
            tarjeta.save()
            compra.save()
            messages.success(request, f"Compra registrada: {compra.descripcion}")
            return redirect("dashboard")
    else:
        form = CompraTCForm(initial={"fecha": date.today()})

    return render(
        request,
        "deudas/compras_registrar.html",
        {
            "form": form,
            "tarjeta": tarjeta,
        },
    )


@login_required
def registrar_pago_tc(request, tarjeta_id):
    tarjeta = get_object_or_404(TarjetaCredito, id=tarjeta_id, usuario=request.user)

    if request.method == "POST":
        form = PagoTCForm(request.POST)
        if form.is_valid():
            monto_pago = form.cleaned_data["monto_pago"]
            if monto_pago > tarjeta.saldo_actual:
                messages.warning(
                    request,
                    f"El pago (${monto_pago:,.0f}) supera el saldo actual "
                    f"(${tarjeta.saldo_actual:,.0f}). Se ajustará al saldo.",
                )
                monto_pago = tarjeta.saldo_actual
            tarjeta.saldo_actual -= monto_pago
            tarjeta.save()
            messages.success(
                request, f"Pago de ${monto_pago:,.0f} registrado en {tarjeta.nombre}."
            )
            return redirect("dashboard")
    else:
        form = PagoTCForm()

    return render(
        request,
        "deudas/tarjetas_pago.html",
        {
            "form": form,
            "tarjeta": tarjeta,
        },
    )
