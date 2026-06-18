from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from datetime import date
from .models import Categoria, Rubro, Gasto
from .forms import CategoriaForm, RubroForm, GastoForm


MESES_NOMBRE = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


@login_required
def listar_gastos(request):
    mes = int(request.GET.get('mes', date.today().month))
    anio = int(request.GET.get('anio', date.today().year))

    gastos = Gasto.objects.filter(
        usuario=request.user, mes=mes, anio=anio
    ).select_related('categoria', 'rubro').order_by('-fecha', '-creado_en')

    total_mes = gastos.aggregate(s=Sum('monto'))['s'] or Decimal('0')

    gastos_por_categoria = (
        gastos.values('categoria__nombre', 'categoria__color')
        .annotate(total=Sum('monto'))
        .order_by('-total')
    )

    gastos_fijos = gastos.filter(tipo='fijo').aggregate(s=Sum('monto'))['s'] or Decimal('0')
    gastos_variables = gastos.filter(tipo='variable').aggregate(s=Sum('monto'))['s'] or Decimal('0')

    categorias = Categoria.objects.filter(
        visible=True
    ).filter(
        Q(usuario=request.user) | Q(usuario__isnull=True)
    ).order_by('orden', 'nombre')

    return render(request, 'gastos/lista.html', {
        'mes': mes,
        'anio': anio,
        'mes_nombre': MESES_NOMBRE[mes],
        'gastos': gastos,
        'total_mes': total_mes,
        'gastos_por_categoria': gastos_por_categoria,
        'gastos_fijos': gastos_fijos,
        'gastos_variables': gastos_variables,
        'categorias': categorias,
    })


@login_required
def registrar_gasto(request):
    mes = int(request.GET.get('mes', date.today().month))
    anio = int(request.GET.get('anio', date.today().year))

    if request.method == 'POST':
        form = GastoForm(request.POST, usuario=request.user)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.usuario = request.user
            gasto.save()
            messages.success(request, 'Gasto registrado correctamente.')
            return redirect(f'/?mes={gasto.mes}&anio={gasto.anio}')
    else:
        form = GastoForm(usuario=request.user, initial={
            'mes': mes,
            'anio': anio,
            'fecha': date.today(),
        })

    return render(request, 'gastos/registrar_gasto.html', {
        'form': form,
        'titulo': 'Registrar Gasto',
    })


@login_required
def editar_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id, usuario=request.user)

    if request.method == 'POST':
        form = GastoForm(request.POST, instance=gasto, usuario=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto actualizado correctamente.')
            return redirect(f'/gastos/?mes={gasto.mes}&anio={gasto.anio}')
    else:
        form = GastoForm(instance=gasto, usuario=request.user)

    return render(request, 'gastos/registrar_gasto.html', {
        'form': form,
        'titulo': 'Editar Gasto',
    })


@login_required
def eliminar_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id, usuario=request.user)
    mes, anio = gasto.mes, gasto.anio
    gasto.delete()
    messages.success(request, 'Gasto eliminado.')
    return redirect(f'/gastos/?mes={mes}&anio={anio}')


@login_required
def duplicar_gasto(request, gasto_id):
    gasto_original = get_object_or_404(Gasto, id=gasto_id, usuario=request.user)
    mes = int(request.GET.get('mes', date.today().month))
    anio = int(request.GET.get('anio', date.today().year))

    if request.method == 'POST':
        nuevo = Gasto.objects.create(
            usuario=request.user,
            categoria=gasto_original.categoria,
            rubro=gasto_original.rubro,
            monto=gasto_original.monto,
            fecha=date(anio, mes, min(gasto_original.fecha.day, 28)),
            descripcion=gasto_original.descripcion,
            metodo_pago=gasto_original.metodo_pago,
            tipo=gasto_original.tipo,
            recurrente=gasto_original.recurrente,
            mes=mes,
            anio=anio,
        )
        messages.success(request, 'Gasto duplicado correctamente.')
        return redirect(f'/gastos/?mes={mes}&anio={anio}')

    return render(request, 'gastos/duplicar_gasto.html', {
        'gasto': gasto_original,
        'mes': mes,
        'anio': anio,
        'mes_nombre': MESES_NOMBRE[mes],
    })


@login_required
def gestionar_categorias(request):
    categorias = Categoria.objects.filter(
        Q(usuario=request.user) | Q(usuario__isnull=True)
    ).order_by('orden', 'nombre')

    return render(request, 'gastos/categorias.html', {
        'categorias': categorias,
    })


@login_required
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.usuario = request.user
            categoria.es_sugerida = False
            categoria.save()
            messages.success(request, 'Categoría creada correctamente.')
            return redirect('gastos:categorias')
    else:
        form = CategoriaForm()

    return render(request, 'gastos/registrar_categoria.html', {
        'form': form,
        'titulo': 'Nueva Categoría',
    })


@login_required
def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if categoria.es_sugerida and categoria.usuario is None:
        messages.error(request, 'No puedes editar categorías sugeridas del sistema.')
        return redirect('gastos:categorias')

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada correctamente.')
            return redirect('gastos:categorias')
    else:
        form = CategoriaForm(instance=categoria)

    return render(request, 'gastos/registrar_categoria.html', {
        'form': form,
        'titulo': 'Editar Categoría',
    })


@login_required
def ocultar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    categoria.visible = not categoria.visible
    categoria.save()
    estado = 'visible' if categoria.visible else 'oculta'
    messages.success(request, f'Categoría "{categoria.nombre}" ahora está {estado}.')
    return redirect('gastos:categorias')


@login_required
def eliminar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if categoria.es_sugerida and categoria.usuario is None:
        messages.error(request, 'No puedes eliminar categorías sugeridas del sistema. Puedes ocultarlas.')
        return redirect('gastos:categorias')

    if Gasto.objects.filter(categoria=categoria).exists():
        messages.error(request, f'No se puede eliminar "{categoria.nombre}" porque tiene gastos asociados.')
        return redirect('gastos:categorias')

    categoria.delete()
    messages.success(request, 'Categoría eliminada.')
    return redirect('gastos:categorias')


@login_required
def crear_rubro(request):
    if request.method == 'POST':
        form = RubroForm(request.POST, usuario=request.user)
        if form.is_valid():
            rubro = form.save(commit=False)
            rubro.es_sugerida = False
            rubro.save()
            messages.success(request, 'Rubro creado correctamente.')
            return redirect('gastos:categorias')
    else:
        form = RubroForm(usuario=request.user)

    return render(request, 'gastos/registrar_rubro.html', {
        'form': form,
        'titulo': 'Nuevo Rubro',
    })


@login_required
def editar_rubro(request, rubro_id):
    rubro = get_object_or_404(Rubro, id=rubro_id)

    if rubro.es_sugerida:
        messages.error(request, 'No puedes editar rubros sugeridos del sistema.')
        return redirect('gastos:categorias')

    if request.method == 'POST':
        form = RubroForm(request.POST, instance=rubro, usuario=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rubro actualizado correctamente.')
            return redirect('gastos:categorias')
    else:
        form = RubroForm(instance=rubro, usuario=request.user)

    return render(request, 'gastos/registrar_rubro.html', {
        'form': form,
        'titulo': 'Editar Rubro',
    })


@login_required
def ocultar_rubro(request, rubro_id):
    rubro = get_object_or_404(Rubro, id=rubro_id)
    rubro.visible = not rubro.visible
    rubro.save()
    estado = 'visible' if rubro.visible else 'oculto'
    messages.success(request, f'Rubro "{rubro.nombre}" ahora está {estado}.')
    return redirect('gastos:categorias')


@login_required
def eliminar_rubro(request, rubro_id):
    rubro = get_object_or_404(Rubro, id=rubro_id)

    if rubro.es_sugerida:
        messages.error(request, 'No puedes eliminar rubros sugeridos del sistema. Puedes ocultarlos.')
        return redirect('gastos:categorias')

    if Gasto.objects.filter(rubro=rubro).exists():
        messages.error(request, f'No se puede eliminar "{rubro.nombre}" porque tiene gastos asociados.')
        return redirect('gastos:categorias')

    rubro.delete()
    messages.success(request, 'Rubro eliminado.')
    return redirect('gastos:categorias')


@login_required
def cargar_rubros(request):
    categoria_id = request.GET.get('categoria_id')
    if categoria_id:
        rubros = Rubro.objects.filter(
            categoria_id=categoria_id, visible=True
        ).order_by('orden', 'nombre')
        from django.http import JsonResponse
        data = [{'id': r.id, 'nombre': r.nombre, 'tipo': r.tipo} for r in rubros]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)
