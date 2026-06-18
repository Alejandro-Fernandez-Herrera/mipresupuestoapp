from django import forms
from decimal import Decimal
from .models import Provision


class ProvisionForm(forms.ModelForm):
    class Meta:
        model = Provision
        fields = [
            "concepto",
            "monto_total",
            "fecha_pago",
            "ahorro_acumulado",
            "ahorro_mensual_disponible",
        ]
        widgets = {
            "concepto": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: SOAT vehículo",
                }
            ),
            "monto_total": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 250000",
                }
            ),
            "fecha_pago": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "ahorro_acumulado": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 50000",
                }
            ),
            "ahorro_mensual_disponible": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 100000",
                }
            ),
        }
        labels = {
            "concepto": "Concepto",
            "monto_total": "Monto total estimado (COP)",
            "fecha_pago": "Fecha de pago",
            "ahorro_acumulado": "Ahorro acumulado (COP)",
            "ahorro_mensual_disponible": "Ahorro mensual disponible (COP)",
        }


class AporteProvisionForm(forms.Form):
    monto = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("1"),
        label="Monto del aporte (COP)",
        widget=forms.NumberInput(
            attrs={
                "step": "1",
                "min": "1",
                "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                "placeholder": "Ej: 50000",
            }
        ),
    )
    fecha = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
            }
        ),
    )
