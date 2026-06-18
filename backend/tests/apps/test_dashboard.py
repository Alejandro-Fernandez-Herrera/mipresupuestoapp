import pytest
from django.urls import reverse
from django.test import Client
from decimal import Decimal
from datetime import date, timedelta
from apps.accounts.models import UserProfile
from apps.gastos.models import Gasto, Categoria, Rubro
from apps.ingresos.models import RegistroNomina
from apps.deudas.models import Credito, TarjetaCredito
from apps.provisiones.models import Provision, FondoEmergencia


@pytest.mark.django_db
class TestDashboardView:

    def test_dashboard_requiere_auth(self):
        response = Client().get(reverse('dashboard'))
        assert response.status_code == 302

    def test_dashboard_carga_sin_datos(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert 'Dashboard' in response.content.decode()

    def test_dashboard_muestra_ingresos(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test', meta_tasa_ahorro=Decimal('20')
        )
        hoy = date.today()
        RegistroNomina.objects.create(
            usuario=user, salario_bruto=Decimal('2000000'),
            deduccion_salud=Decimal('80000'), deduccion_pension=Decimal('80000'),
            salario_neto=Decimal('1840000'), neto_con_auxilio=Decimal('1840000'),
            mes=hoy.month, anio=hoy.year,
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200

    def test_dashboard_muestra_gastos(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        cat = Categoria.objects.create(
            nombre='TestCat', color='#FF0000', es_esencial=False, visible=True
        )
        rubro = Rubro.objects.create(
            categoria=cat, nombre='TestRubro', visible=True
        )
        Gasto.objects.create(
            usuario=user, categoria=cat, rubro=rubro,
            monto=Decimal('50000'), fecha=date.today(),
            metodo_pago='efectivo', tipo='variable',
            mes=date.today().month, anio=date.today().year,
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200

    def test_dashboard_muestra_indicadores(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test', meta_tasa_ahorro=Decimal('20')
        )
        hoy = date.today()
        RegistroNomina.objects.create(
            usuario=user, salario_bruto=Decimal('3000000'),
            deduccion_salud=Decimal('120000'), deduccion_pension=Decimal('120000'),
            salario_neto=Decimal('2760000'), neto_con_auxilio=Decimal('2760000'),
            mes=hoy.month, anio=hoy.year,
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert 'Indicadores de Salud Financiera' in response.content.decode()

    def test_dashboard_filtro_mes_anio(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        client = Client()
        client.force_login(user)
        response = client.get('/?mes=6&anio=2026')
        assert response.status_code == 200

    def test_dashboard_muestra_tendencia_grafico(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert 'grafico-tendencia' in response.content.decode()

    def test_dashboard_muestra_deudas_widget(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        Credito.objects.create(
            usuario=user, nombre='Test Credito', entidad_tipo='bancario',
            capital=Decimal('5000000'), tasa_ea=Decimal('0.25'),
            plazo_meses=12, fecha_desembolso=date.today(), activo=True,
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert 'Resumen de Deudas' in response.content.decode()

    def test_dashboard_muestra_provisiones_widget(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        Provision.objects.create(
            usuario=user, concepto='SOAT', monto_total=Decimal('500000'),
            ahorro_acumulado=Decimal('100000'), fecha_pago=date.today() + timedelta(days=60),
            activa=True,
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert 'Provisiones Activas' in response.content.decode()


@pytest.mark.django_db
class TestDashboardRedirects:

    def _crear_usuario(self):
        return UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )

    def test_registrar_gasto_redirige_dashboard(self):
        user = self._crear_usuario()
        cat = Categoria.objects.create(
            nombre='TestCat', color='#FF0000', es_esencial=False, visible=True
        )
        rubro = Rubro.objects.create(
            categoria=cat, nombre='TestRubro', visible=True
        )
        client = Client()
        client.force_login(user)
        response = client.post(reverse('gastos:registrar'), {
            'monto': '50000', 'fecha': str(date.today()),
            'categoria': cat.id, 'rubro': rubro.id,
            'metodo_pago': 'efectivo', 'tipo': 'variable',
            'mes': date.today().month, 'anio': date.today().year,
        })
        assert response.status_code == 302
        assert response.url.startswith('/?')

    def test_registrar_credito_redirige_dashboard(self):
        user = self._crear_usuario()
        client = Client()
        client.force_login(user)
        response = client.post(reverse('deudas:registrar'), {
            'nombre': 'Test Prestamo', 'entidad_tipo': 'bancario',
            'capital': '5000000', 'tasa_ea': '0.25',
            'plazo_meses': '12', 'fecha_desembolso': str(date.today()),
        })
        assert response.status_code == 302
        assert response.url == reverse('dashboard')

    def test_registrar_tarjeta_redirige_dashboard(self):
        user = self._crear_usuario()
        client = Client()
        client.force_login(user)
        response = client.post(reverse('deudas:registrar_tarjeta'), {
            'nombre': 'Test Visa', 'banco': 'Test Bank',
            'limite': '3000000', 'tasa_mensual': '0.0234',
            'saldo_actual': '0', 'fecha_corte': '15',
            'fecha_limite_pago': '5', 'cuota_minima_pct': '0.05',
        })
        assert response.status_code == 302
        assert response.url == reverse('dashboard')

    def test_registrar_provision_redirige_dashboard(self):
        user = self._crear_usuario()
        client = Client()
        client.force_login(user)
        response = client.post(reverse('provisiones:registrar'), {
            'concepto': 'Test SOAT', 'monto_total': '500000',
            'fecha_pago': str(date.today()),
            'ahorro_acumulado': '0', 'ahorro_mensual_disponible': '0',
        })
        assert response.status_code == 302
        assert response.url == reverse('dashboard')


@pytest.mark.django_db
class TestServiceObtenerResumenDeudas:

    def test_resumen_sin_deudas(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        from apps.indicadores.services import obtener_resumen_deudas
        resumen = obtener_resumen_deudas(user)
        assert resumen['creditos_activos'] == 0
        assert resumen['tarjetas_activas'] == 0
        assert resumen['total_deuda_total'] == Decimal('0')

    def test_resumen_con_credito(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        Credito.objects.create(
            usuario=user, nombre='Test', entidad_tipo='bancario',
            capital=Decimal('10000000'), tasa_ea=Decimal('0.25'),
            plazo_meses=12, fecha_desembolso=date.today(), activo=True,
        )
        from apps.indicadores.services import obtener_resumen_deudas
        resumen = obtener_resumen_deudas(user)
        assert resumen['creditos_activos'] == 1
        assert resumen['total_saldo_creditos'] == Decimal('10000000')

    def test_resumen_con_tarjeta(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        TarjetaCredito.objects.create(
            usuario=user, nombre='Test Visa', banco='Test',
            limite=Decimal('3000000'), tasa_mensual=Decimal('0.0234'),
            saldo_actual=Decimal('1000000'), fecha_corte=15,
            fecha_limite_pago=5, activa=True,
        )
        from apps.indicadores.services import obtener_resumen_deudas
        resumen = obtener_resumen_deudas(user)
        assert resumen['tarjetas_activas'] == 1
        assert len(resumen['tarjetas_info']) == 1
        assert resumen['tarjetas_info'][0]['nombre'] == 'Test Visa'


@pytest.mark.django_db
class TestServiceObtenerProvisionesActivas:

    def test_sin_provisiones(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        from apps.indicadores.services import obtener_provisiones_activas
        resultado = obtener_provisiones_activas(user)
        assert resultado == []

    def test_con_provision(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        Provision.objects.create(
            usuario=user, concepto='SOAT', monto_total=Decimal('500000'),
            ahorro_acumulado=Decimal('100000'),
            fecha_pago=date.today() + timedelta(days=120),
            activa=True,
        )
        from apps.indicadores.services import obtener_provisiones_activas
        resultado = obtener_provisiones_activas(user)
        assert len(resultado) == 1
        assert resultado[0]['concepto'] == 'SOAT'
        assert resultado[0]['progreso'] == 20


@pytest.mark.django_db
class TestServiceObtenerTendenciaIngresosGastos:

    def test_tendencia_retorna_datos(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        from apps.indicadores.services import obtener_tendencia_ingresos_gastos
        resultado = obtener_tendencia_ingresos_gastos(user, meses=6)
        assert len(resultado['labels']) == 6
        assert len(resultado['ingresos']) == 6
        assert len(resultado['gastos']) == 6
