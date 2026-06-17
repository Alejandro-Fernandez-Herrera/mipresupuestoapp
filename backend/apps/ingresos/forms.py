from django import forms
from decimal import Decimal
from .models import RegistroNomina, OtroIngreso


class RegistroNominaForm(forms.ModelForm):
    MESES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]

    mes = forms.ChoiceField(choices=MESES, label="Mes")
    anio = forms.IntegerField(min_value=2020, max_value=2035, initial=2026, label="Año")
    salario_bruto = forms.DecimalField(
        min_value=Decimal('0'), label="Salario bruto (COP)",
        widget=forms.NumberInput(attrs={
            'step': '1', 'min': '0',
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Ej: 1423500',
        })
    )
    recurrente = forms.BooleanField(
        required=False, initial=True,
        label="Repetir mensualmente",
    )

    class Meta:
        model = RegistroNomina
        fields = ['salario_bruto', 'mes', 'anio', 'recurrente']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('mes', 'anio'):
            self.fields[field_name].widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            })
        self.fields['recurrente'].widget.attrs.update({
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
        })


class OtroIngresoForm(forms.ModelForm):
    MESES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]

    mes = forms.ChoiceField(choices=MESES, label="Mes")
    anio = forms.IntegerField(min_value=2020, max_value=2035, initial=2026, label="Año")
    monto = forms.DecimalField(
        min_value=Decimal('0'), label="Monto (COP)",
        widget=forms.NumberInput(attrs={
            'step': '1', 'min': '0',
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Ej: 500000',
        })
    )
    recurrente = forms.BooleanField(
        required=False, label="Repetir mensualmente",
    )

    class Meta:
        model = OtroIngreso
        fields = ['tipo', 'monto', 'mes', 'anio', 'descripcion', 'recurrente']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 2,
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Descripción opcional',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        mes = cleaned_data.get('mes')

        if tipo == 'prima_junio' and mes != '6':
            self.add_error('mes', 'La prima de junio solo puede registrarse en el mes de junio.')
        if tipo == 'prima_diciembre' and mes != '12':
            self.add_error('mes', 'La prima de diciembre solo puede registrarse en el mes de diciembre.')

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('mes', 'anio'):
            self.fields[field_name].widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            })
        self.fields['recurrente'].widget.attrs.update({
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
        })
