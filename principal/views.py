from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

from bases.views import BaseView, ModeloBaseTemplateView
from materia_prima.models import MateriaPrima
from materia_prima.tipo_materia_prima.models import TipoMateriaPrima
from produccion.models import Produccion
# from producto_base.models import ProductoBase
# from producto_final.models import ProductoFinal
from usuario.models import CustomUser


# Create your views here.
class GestionView(BaseView):
    pass


# Create your views here.
class PrincipalTemplateView(GestionView, ModeloBaseTemplateView):
    template_name = "index.html"


class LoginTemplateView(GestionView, ModeloBaseTemplateView):
    template_name = "autenticacion/auth-sign-in.html"


class ListExpedientesTemplateView(GestionView, ModeloBaseTemplateView):
    template_name = "gestion/gestion/erta/listExpPendInspTec.html"


@never_cache
def cargar_datos_principal(request):
    usuario_logeado = request.user
    cant_tipo_materia_prima = TipoMateriaPrima.objects.all().count()
    cant_materia_prima = MateriaPrima.objects.all().count()
    # cant_producto_base = ProductoBase.objects.all().count()
    # cant_producto_final = ProductoFinal.objects.all().count()
    cant_produccion = Produccion.objects.all().count()
    # Pasa las variables al contexto del template principal
    context = {
        'cant_tipo_materia_prima': cant_tipo_materia_prima,
        'cant_materia_prima': cant_materia_prima,
        # 'cant_producto_base': cant_producto_base,
        # 'cant_producto_final': cant_producto_final,
        'cant_produccion': cant_produccion,
    }
    # Renderiza el template principal con el contexto
    return render(request, 'base/base.html', context)


def authenticate_user(request, username=None, password=None):
    user = authenticate(request, username=username, password=password)

    if user is None:
        try:
            user = CustomUser.objects.get(username=username)

            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            pass

    return user


@csrf_protect
@ensure_csrf_cookie
def loginPage(request):
    if request.user.is_authenticated:
        return redirect('cargar_datos_principal')
    else:
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']

            user = authenticate_user(request, username=username, password=password)
            if user is not None:
                login(request, user)  # Utilizar la función login de Django para iniciar sesión
                # affected_model = get_model_from_url(request.path)
                # Traza.objects.create(
                #     user=user,
                #     action='Entró al sistema',
                #     affected_model='Sistema'
                # )
                return redirect('cargar_datos_principal')
            else:
                messages.error(request, 'Usuario o contraseña incorrecta')
                ctx = {'error_message': 'Usuario o contraseña incorrecta'}
                return render(request, 'autenticacion/auth-sign-in.html', ctx)

        ctx = {}
        return render(request, 'autenticacion/auth-sign-in.html', ctx)


def logoutUser(request):
    """
    Función para cerrar sesión de un usuario.
    """
    # Cierra la sesión del usuario actual

    logout(request)

    # Redirige al usuario a la página de inicio de sesión
    return HttpResponseRedirect(reverse('login'))
