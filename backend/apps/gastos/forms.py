from django import forms
from decimal import Decimal
from .models import Categoria, Rubro, Gasto


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'color', 'icono']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ej: Servicios Públicos',
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'mt-1 block w-full h-10 px-1 py-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            }),
            'icono': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Opcional: nombre del icono',
            }),
        }
        labels = {
            'nombre': 'Nombre de la categoría',
            'color': 'Color',
            'icono': 'Icono (opcional)',
        }


class RubroForm(forms.ModelForm):
    class Meta:
        model = Rubro
        fields = ['categoria', 'nombre', 'tipo']
        widgets = {
            'categoria': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ej: Energía eléctrica',
            }),
            'tipo': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            }),
        }
        labels = {
            'categoria': 'Categoría',
            'nombre': 'Nombre del rubro',
            'tipo': 'Tipo',
        }

    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        if usuario:
            self.fields['categoria'].queryset = Categoria.objects.filter(
                visible=True
            ).filter(
                models.Q(usuario=usuario) | models.Q(usuario__isnull=True)
            )


class GastoForm(forms.ModelForm):
    MESES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]

    mes = forms.ChoiceField(choices=MESES, label="Mes")
    anio = forms.IntegerField(min_value=2020, max_value=2035, initial=2026, label="Año")

    class Meta:
        model = Gasto
        fields = ['categoria', 'rubro', 'monto', 'fecha', 'descripcion', 'metodo_pago', 'tipo', 'recurrente', 'mes', 'anio']
        widgets = {
            'categoria': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            }),
            'rubro': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            }),
            'monto': forms.NumberInput(attrs={
                'step': '1', 'min': '0',
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ej: 150000',
            }),
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 2,
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Descripción opcional',
            }),
            'metodo_pago': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            }),
            'tipo': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            }),
            'recurrente': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            }),
        }
        labels = {
            'categoria': 'Categoría',
            'rubro': 'Rubro',
            'monto': 'Monto (COP)',
            'fecha': 'Fecha',
            'descripcion': 'Descripción',
            'metodo_pago': 'Método de pago',
            'tipo': 'Tipo',
            'recurrente': 'Repetir mensualmente',
        }

    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        for field_name in ('mes', 'anio'):
            self.fields[field_name].widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            })
        self.fields['recurrente'].widget.attrs.update({
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
        })
        if usuario:
            self.fields['categoria'].queryset = Categoria.objects.filter(
                visible=True
            ).filter(
                models.Q(usuario=usuario) | models.Q(usuario__isnull=True)
            )
            self.fields['rubro'].queryset = Rubro.objects.filter(visible=True)