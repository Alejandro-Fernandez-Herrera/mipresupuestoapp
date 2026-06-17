from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import UserProfile, ConfiguracionFiscal


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario o Email",
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Usuario o correo electrónico',
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Contraseña',
        })
    )


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True, label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'correo@ejemplo.co',
        })
    )
    nombre_completo = forms.CharField(
        max_length=150, required=True, label="Nombre completo",
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Tu nombre completo',
        })
    )
    ciudad = forms.CharField(
        max_length=100, required=False, initial="Bogotá", label="Ciudad",
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        })
    )

    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'nombre_completo', 'ciudad', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserProfile.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('username', 'password1', 'password2'):
            self.fields[field_name].widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nombre_completo = self.cleaned_data['nombre_completo']
        user.ciudad = self.cleaned_data.get('ciudad', 'Bogotá')
        if commit:
            user.save()
        return user


class PerfilForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nombre_completo', 'email', 'ciudad', 'smlv_vigente', 'uvt_vigente', 'auxilio_transporte', 'meta_tasa_ahorro']
        widgets = {
            'smlv_vigente': forms.NumberInput(attrs={'step': '1', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'uvt_vigente': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'auxilio_transporte': forms.NumberInput(attrs={'step': '1', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'meta_tasa_ahorro': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '100', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'email': forms.EmailInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'ciudad': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
        }
        labels = {
            'nombre_completo': 'Nombre completo',
            'email': 'Email',
            'ciudad': 'Ciudad',
            'smlv_vigente': 'SMLV vigente (COP)',
            'uvt_vigente': 'UVT vigente (COP)',
            'auxilio_transporte': 'Auxilio transporte (COP)',
            'meta_tasa_ahorro': 'Meta tasa ahorro (%)',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserProfile.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este correo electrónico ya está en uso.')
        return email


class ConfiguracionFiscalForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionFiscal
        fields = '__all__'
        widgets = {
            'anio': forms.NumberInput(attrs={'min': '2020', 'max': '2030', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'smlv': forms.NumberInput(attrs={'step': '1', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'auxilio_transporte': forms.NumberInput(attrs={'step': '1', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'uvt': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'umbral_retencion_uvt': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'tasa_salud_empleado': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'tasa_pension_empleado': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'umbral_solidaridad_smlv': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'tasa_solidaridad_4_16': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'tasa_solidaridad_16_17': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'tasa_solidaridad_17_18': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'tasa_solidaridad_18_19': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'tasa_solidaridad_19_20': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'tasa_solidaridad_mas_20': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'factor_prima_mensual': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'factor_cesantias_mensual': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'tasa_intereses_cesantias': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'factor_vacaciones_mensual': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
            'cuota_minima_tc_pct': forms.NumberInput(attrs={'step': '0.0001', 'min': '0', 'max': '1', 'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm'}),
        }