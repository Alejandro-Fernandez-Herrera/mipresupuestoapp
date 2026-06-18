from django import forms
from decimal import Decimal
from .models import Escenario, ProyeccionIngreso, ProyeccionGasto


class EscenarioForm(forms.ModelForm):
    class Meta:
        model = Escenario
        fields = ["nombre", "factor_ingreso", "factor_gasto", "activo"]
        widgets = {
            "nombre": forms.Select(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "factor_ingreso": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0.01",
                    "max": "2.00",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 1.10 para +10%",
                }
            ),
            "factor_gasto": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0.01",
                    "max": "2.00",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 0.90 para -10%",
                }
            ),
            "activo": forms.CheckboxInput(
                attrs={
                    "class": "mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded",
                }
            ),
        }


class ProyeccionIngresoForm(forms.ModelForm):
    class Meta:
        model = ProyeccionIngreso
        fields = ["escenario", "mes", "anio", "fuente", "monto_proyectado", "nota"]
        widgets = {
            "escenario": forms.Select(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "mes": forms.Select(
                choices=[
                    (1, "Enero"),
                    (2, "Febrero"),
                    (3, "Marzo"),
                    (4, "Abril"),
                    (5, "Mayo"),
                    (6, "Junio"),
                    (7, "Julio"),
                    (8, "Agosto"),
                    (9, "Septiembre"),
                    (10, "Octubre"),
                    (11, "Noviembre"),
                    (12, "Diciembre"),
                ],
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                },
            ),
            "anio": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "fuente": forms.Select(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "monto_proyectado": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 3500000",
                }
            ),
            "nota": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Nota opcional",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["escenario"].queryset = Escenario.objects.filter(
                usuario=self.user, activo=True
            )


class ProyeccionGastoForm(forms.ModelForm):
    class Meta:
        model = ProyeccionGasto
        fields = ["escenario", "mes", "anio", "categoria", "monto_proyectado", "nota"]
        widgets = {
            "escenario": forms.Select(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "mes": forms.Select(
                choices=[
                    (1, "Enero"),
                    (2, "Febrero"),
                    (3, "Marzo"),
                    (4, "Abril"),
                    (5, "Mayo"),
                    (6, "Junio"),
                    (7, "Julio"),
                    (8, "Agosto"),
                    (9, "Septiembre"),
                    (10, "Octubre"),
                    (11, "Noviembre"),
                    (12, "Diciembre"),
                ],
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                },
            ),
            "anio": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "categoria": forms.Select(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "monto_proyectado": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 250000",
                }
            ),
            "nota": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Nota opcional",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["escenario"].queryset = Escenario.objects.filter(
                usuario=self.user, activo=True
            )
            from apps.gastos.models import Categoria

            self.fields["categoria"].queryset = Categoria.objects.filter(visible=True)
