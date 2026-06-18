from django import forms
from decimal import Decimal
from .models import Credito, CuotaCredito, TarjetaCredito, CompraTC


class TarjetaCreditoForm(forms.ModelForm):
    class Meta:
        model = TarjetaCredito
        fields = [
            "nombre",
            "banco",
            "limite",
            "tasa_mensual",
            "saldo_actual",
            "fecha_corte",
            "fecha_limite_pago",
            "cuota_minima_pct",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: Visa Clásica",
                }
            ),
            "banco": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: Bancolombia",
                }
            ),
            "limite": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 5000000",
                }
            ),
            "tasa_mensual": forms.NumberInput(
                attrs={
                    "step": "0.000001",
                    "min": "0",
                    "max": "1",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 0.0234 para 2.34% mensual",
                }
            ),
            "saldo_actual": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 1500000",
                }
            ),
            "fecha_corte": forms.NumberInput(
                attrs={
                    "min": "1",
                    "max": "31",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "fecha_limite_pago": forms.NumberInput(
                attrs={
                    "min": "1",
                    "max": "31",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "cuota_minima_pct": forms.NumberInput(
                attrs={
                    "step": "0.0001",
                    "min": "0",
                    "max": "1",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 0.05 para 5%",
                }
            ),
        }
        labels = {
            "nombre": "Nombre de la tarjeta",
            "banco": "Banco / Entidad",
            "limite": "Límite (COP)",
            "tasa_mensual": "Tasa mensual (decimal)",
            "saldo_actual": "Saldo actual (COP)",
            "fecha_corte": "Día de corte",
            "fecha_limite_pago": "Día límite de pago",
            "cuota_minima_pct": "% cuota mínima (decimal)",
        }


class CompraTCForm(forms.ModelForm):
    class Meta:
        model = CompraTC
        fields = ["monto", "fecha", "descripcion", "categoria", "numero_cuotas"]
        widgets = {
            "monto": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 250000",
                }
            ),
            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "descripcion": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: Mercado mensual",
                }
            ),
            "categoria": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: Alimentación",
                }
            ),
            "numero_cuotas": forms.NumberInput(
                attrs={
                    "min": "1",
                    "max": "120",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
        }
        labels = {
            "monto": "Monto (COP)",
            "fecha": "Fecha de compra",
            "descripcion": "Descripción",
            "categoria": "Categoría",
            "numero_cuotas": "Número de cuotas",
        }


class PagoTCForm(forms.Form):
    monto_pago = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("1"),
        label="Monto a pagar (COP)",
        widget=forms.NumberInput(
            attrs={
                "step": "1",
                "min": "1",
                "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                "placeholder": "Ej: 500000",
            }
        ),
    )


class CreditoForm(forms.ModelForm):
    class Meta:
        model = Credito
        fields = [
            "nombre",
            "entidad_tipo",
            "capital",
            "tasa_ea",
            "plazo_meses",
            "fecha_desembolso",
            "descripcion",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: Credito Bancolombia",
                }
            ),
            "entidad_tipo": forms.Select(
                attrs={
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "capital": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 10000000",
                }
            ),
            "tasa_ea": forms.NumberInput(
                attrs={
                    "step": "0.000001",
                    "min": "0",
                    "max": "1",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 0.25 para 25% EA",
                }
            ),
            "plazo_meses": forms.NumberInput(
                attrs={
                    "min": "1",
                    "max": "480",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Ej: 12",
                }
            ),
            "fecha_desembolso": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Descripción opcional",
                }
            ),
        }
        labels = {
            "nombre": "Nombre / Entidad",
            "entidad_tipo": "Tipo de entidad",
            "capital": "Monto del crédito (COP)",
            "tasa_ea": "Tasa EA (decimal)",
            "plazo_meses": "Plazo (meses)",
            "fecha_desembolso": "Fecha de desembolso",
            "descripcion": "Descripción",
        }
