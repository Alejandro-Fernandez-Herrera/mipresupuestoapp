from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from .models import RegistroNomina, OtroIngreso, PrestacionSocial
from .forms import RegistroNominaForm, OtroIngresoForm
from .services import (
    calcular_nomina,
    calcular_prima,
    calcular_cesantias,
    calcular_intereses_cesantias,
    calcular_vacaciones,
)
from datetime import date


MESES_NOMBRE = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


@login_required
def listar_ingresos(request):
    mes = int(request.GET.get('mes', date.today().month))
    anio = int(request.GET.get('anio', date.today().year))

    nominas = RegistroNomina.objects.filter(
        usuario=request.user, mes=mes, anio=anio
    )
    otros_ingresos = OtroIngreso.objects.filter(
        usuario=request.user, mes=mes, anio=anio
    )

    total_nomina = nominas.aggregate(s=Sum('neto_con_auxilio'))['s'] or Decimal('0')
    total_otros = otros_ingresos.aggregate(s=Sum('monto'))['s'] or Decimal('0')
    total_ingresos = total_nomina + total_otros

    # Prestaciones proyectadas para el año
    prestaciones = PrestacionSocial.objects.filter(
        usuario=request.user, anio=anio, pagada=False
    ).order_by('fecha_pago_esperada')

    # Generar prestaciones si hay nómina activa y no existen aún
    nomina_activa = nominas.first()
    if nomina_activa and not prestaciones.exists():
        config = request.user.get_config_fiscal()
        if config:
            meses_transcurridos = max(1, mes)
            prestaciones_data = {
                'prima_servicios': {
                    'monto': calcular_prima(nomina_activa.salario_bruto, meses_transcurridos, config),
                    'fecha_pago_1': date(anio, 6, 30),
                    'fecha_pago_2': date(anio, 12, 20),
                },
                'cesantias': {
                    'monto': calcular_cesantias(nomina_activa.salario_bruto, meses_transcurridos, config),
                    'fecha_pago': date(anio + 1, 2, 14),
                },
                'intereses_cesantias': {
                    'monto': calcular_intereses_cesantias(
                        calcular_cesantias(nomina_activa.salario_bruto, meses_transcurridos, config),
                        meses_transcurridos, config
                    ),
                    'fecha_pago': date(anio + 1, 1, 31),
                },
            }

            prestaciones_list = []
            for tipo, datos in prestaciones_data.items():
                if tipo == 'prima_servicios':
                    for fecha_pago in [datos['fecha_pago_1'], datos['fecha_pago_2']]:
                        prestaciones_list.append({
                            'tipo': tipo,
                            'monto': datos['monto'],
                            'fecha_pago': fecha_pago,
                        })
                else:
                    prestaciones_list.append({
                        'tipo': tipo,
                        'monto': datos['monto'],
                        'fecha_pago': datos['fecha_pago'],
                    })

            prestaciones = prestaciones_list

    return render(request, 'ingresos/lista.html', {
        'mes': mes,
        'anio': anio,
        'mes_nombre': MESES_NOMBRE[mes],
        'nominas': nominas,
        'otros_ingresos': otros_ingresos,
        'total_nomina': total_nomina,
        'total_otros': total_otros,
        'total_ingresos': total_ingresos,
        'prestaciones': prestaciones,
    })


@login_required
def registrar_nomina(request):
    mes = int(request.GET.get('mes', date.today().month))
    anio = int(request.GET.get('anio', date.today().year))

    existente = RegistroNomina.objects.filter(
        usuario=request.user, mes=mes, anio=anio
    ).first()
    if existente:
        messages.info(
            request,
            f'Ya existe una nómina registrada para {MESES_NOMBRE[mes]} {anio}. '
            f'Puedes editarla a continuación.'
        )
        return redirect('ingresos:editar_nomina', nomina_id=existente.id)

    if request.method == 'POST':
        form = RegistroNominaForm(request.POST)
        if form.is_valid():
            config = request.user.get_config_fiscal()
            if not config:
                messages.error(
                    request,
                    'No hay configuración fiscal registrada. '
                    'Crea una en tu perfil antes de registrar nómina.'
                )
                return redirect('accounts:configuracion_fiscal')

            nomina = form.save(commit=False)
            nomina.usuario = request.user

            resultado = calcular_nomina(form.cleaned_data['salario_bruto'], config)
            nomina.deduccion_salud = resultado['deduccion_salud']
            nomina.deduccion_pension = resultado['deduccion_pension']
            nomina.deduccion_solidaridad = resultado['deduccion_solidaridad']
            nomina.retencion_fuente = resultado['retencion_fuente'] or Decimal('0')
            nomina.salario_neto = resultado['salario_neto']
            nomina.aplica_auxilio = resultado['aplica_auxilio']
            nomina.auxilio_transporte = resultado['auxilio_transporte']
            nomina.neto_con_auxilio = resultado['neto_con_auxilio']

            nomina.save()

            messages.success(request, 'Nómina registrada correctamente.')
            return redirect(f'/ingresos/?mes={nomina.mes}&anio={nomina.anio}')
    else:
        form = RegistroNominaForm(initial={'mes': mes, 'anio': anio})

    return render(request, 'ingresos/registrar_nomina.html', {
        'form': form,
        'titulo': 'Registrar Nómina',
    })


@login_required
def editar_nomina(request, nomina_id):
    nomina = get_object_or_404(RegistroNomina, id=nomina_id, usuario=request.user)

    if request.method == 'POST':
        form = RegistroNominaForm(request.POST, instance=nomina)
        if form.is_valid():
            config = request.user.get_config_fiscal()
            if not config:
                messages.error(request, 'No hay configuración fiscal registrada.')
                return redirect('accounts:configuracion_fiscal')

            nomina = form.save(commit=False)
            resultado = calcular_nomina(form.cleaned_data['salario_bruto'], config)
            nomina.deduccion_salud = resultado['deduccion_salud']
            nomina.deduccion_pension = resultado['deduccion_pension']
            nomina.deduccion_solidaridad = resultado['deduccion_solidaridad']
            nomina.retencion_fuente = resultado['retencion_fuente'] or Decimal('0')
            nomina.salario_neto = resultado['salario_neto']
            nomina.aplica_auxilio = resultado['aplica_auxilio']
            nomina.auxilio_transporte = resultado['auxilio_transporte']
            nomina.neto_con_auxilio = resultado['neto_con_auxilio']
            nomina.save()

            messages.success(request, 'Nómina actualizada correctamente.')
            return redirect(f'/ingresos/?mes={nomina.mes}&anio={nomina.anio}')
    else:
        form = RegistroNominaForm(instance=nomina, initial={
            'mes': nomina.mes,
            'anio': nomina.anio,
        })

    return render(request, 'ingresos/registrar_nomina.html', {
        'form': form,
        'titulo': 'Editar Nómina',
    })


@login_required
def eliminar_nomina(request, nomina_id):
    nomina = get_object_or_404(RegistroNomina, id=nomina_id, usuario=request.user)
    mes, anio = nomina.mes, nomina.anio
    nomina.delete()
    messages.success(request, 'Nómina eliminada.')
    return redirect(f'/ingresos/?mes={mes}&anio={anio}')


@login_required
def detalle_nomina(request, nomina_id):
    nomina = get_object_or_404(RegistroNomina, id=nomina_id, usuario=request.user)
    return render(request, 'ingresos/detalle_nomina.html', {
        'nomina': nomina,
        'mes_nombre': MESES_NOMBRE[nomina.mes],
    })


@login_required
def registrar_otro_ingreso(request):
    mes = int(request.GET.get('mes', date.today().month))
    anio = int(request.GET.get('anio', date.today().year))

    if request.method == 'POST':
        form = OtroIngresoForm(request.POST)
        if form.is_valid():
            ingreso = form.save(commit=False)
            ingreso.usuario = request.user
            ingreso.save()

            messages.success(request, 'Ingreso registrado correctamente.')
            return redirect(f'/ingresos/?mes={ingreso.mes}&anio={ingreso.anio}')
    else:
        form = OtroIngresoForm(initial={'mes': mes, 'anio': anio})

    return render(request, 'ingresos/registrar_otro_ingreso.html', {
        'form': form,
    })


@login_required
def editar_otro_ingreso(request, ingreso_id):
    ingreso = get_object_or_404(OtroIngreso, id=ingreso_id, usuario=request.user)

    if request.method == 'POST':
        form = OtroIngresoForm(request.POST, instance=ingreso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ingreso actualizado correctamente.')
            return redirect(f'/ingresos/?mes={ingreso.mes}&anio={ingreso.anio}')
    else:
        form = OtroIngresoForm(instance=ingreso, initial={
            'mes': ingreso.mes,
            'anio': ingreso.anio,
        })

    return render(request, 'ingresos/registrar_otro_ingreso.html', {
        'form': form,
        'editando': True,
    })


@login_required
def eliminar_otro_ingreso(request, ingreso_id):
    ingreso = get_object_or_404(OtroIngreso, id=ingreso_id, usuario=request.user)
    mes, anio = ingreso.mes, ingreso.anio
    ingreso.delete()
    messages.success(request, 'Ingreso eliminado.')
    return redirect(f'/ingresos/?mes={mes}&anio={anio}')


@login_required
def prestaciones_proyectadas(request):
    anio = int(request.GET.get('anio', date.today().year))

    prestaciones_bd = PrestacionSocial.objects.filter(
        usuario=request.user, anio=anio
    ).order_by('fecha_pago_esperada')

    return render(request, 'ingresos/prestaciones.html', {
        'anio': anio,
        'prestaciones': prestaciones_bd,
    })
