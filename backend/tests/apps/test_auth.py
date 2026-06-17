import pytest
from django.urls import reverse
from django.test import Client
from apps.accounts.models import UserProfile


@pytest.mark.django_db
class TestRegistro:

    def test_registro_exitoso(self):
        client = Client()
        response = client.post(reverse('accounts:registro'), {
            'username': 'testuser',
            'email': 'test@example.co',
            'nombre_completo': 'Test User',
            'ciudad': 'Cali',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        assert response.status_code == 302
        assert UserProfile.objects.filter(email='test@example.co').exists()

    def test_registro_email_duplicado(self):
        UserProfile.objects.create_user(
            username='existing', email='dup@example.co', password='pass123',
            nombre_completo='Existing'
        )
        client = Client()
        response = client.post(reverse('accounts:registro'), {
            'username': 'newuser',
            'email': 'dup@example.co',
            'nombre_completo': 'New User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        assert response.status_code == 200
        assert 'email' in response.context['form'].errors

    def test_registro_password_corto(self):
        client = Client()
        response = client.post(reverse('accounts:registro'), {
            'username': 'testuser',
            'email': 'test@example.co',
            'nombre_completo': 'Test User',
            'password1': '123',
            'password2': '123',
        })
        assert response.status_code == 200
        assert 'password2' in response.context['form'].errors


@pytest.mark.django_db
class TestLogin:

    def test_login_por_username(self):
        UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        client = Client()
        response = client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'pass123',
        })
        assert response.status_code == 302
        assert '_auth_user_id' in client.session

    def test_login_por_email(self):
        UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        client = Client()
        response = client.post(reverse('accounts:login'), {
            'username': 'test@example.co',
            'password': 'pass123',
        })
        assert response.status_code == 302
        assert '_auth_user_id' in client.session

    def test_login_incorrecto(self):
        client = Client()
        response = client.post(reverse('accounts:login'), {
            'username': 'noexiste',
            'password': 'wrongpass',
        })
        assert response.status_code == 200
        assert 'form' in response.context


@pytest.mark.django_db
class TestPerfil:

    def test_perfil_requiere_auth(self):
        response = Client().get(reverse('accounts:perfil'))
        assert response.status_code == 302

    def test_perfil_muestra_datos(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test User', ciudad='Medellín'
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse('accounts:perfil'))
        assert response.status_code == 200
        assert 'Test User' in response.content.decode()
        assert 'Medellín' in response.content.decode()


@pytest.mark.django_db
class TestPasswordReset:

    def test_password_reset_get(self):
        response = Client().get(reverse('accounts:password_reset'))
        assert response.status_code == 200

    def test_password_reset_post(self):
        UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        client = Client()
        response = client.post(reverse('accounts:password_reset'), {
            'email': 'test@example.co',
        })
        assert response.status_code == 302


@pytest.mark.django_db
class TestCerrarSesion:

    def test_logout_get_muestra_confirmacion(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse('accounts:logout'))
        assert response.status_code == 200
        assert 'cerrar' in response.content.decode().lower()

    def test_logout_post_cierra_sesion(self):
        user = UserProfile.objects.create_user(
            username='testuser', email='test@example.co', password='pass123',
            nombre_completo='Test'
        )
        client = Client()
        client.force_login(user)
        response = client.post(reverse('accounts:logout'))
        assert response.status_code == 200
        assert '_auth_user_id' not in client.session