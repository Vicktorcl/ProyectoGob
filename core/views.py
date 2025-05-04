from datetime import date
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse
from django.core.mail import send_mail
from .models import Perfil, Pregunta, Respuesta
from .forms import (GobernanzaForm,
    IngresarForm, UsuarioForm, PerfilForm,
    RegistroUsuarioForm, RegistroPerfilForm
)
from .tools import eliminar_registro, show_form_errors

# ------------------------------------------------------------------------------------------------------
# Funciones auxiliares para autorización
# ------------------------------------------------------------------------------------------------------

def es_superusuario_activo(user):
    return user.is_superuser and user.is_authenticated and user.is_active

def es_usuario_anonimo(user):
    return user.is_anonymous

# ------------------------------------------------------------------------------------------------------
# Vistas públicas (anónimos)
# ------------------------------------------------------------------------------------------------------

@user_passes_test(es_usuario_anonimo, login_url='nosotros')
def inicio(request):
    """Página de inicio: muestra formulario de login o recibe POST para autenticar."""
    if request.method == "POST":
        form = IngresarForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                login(request, user)
                messages.success(request, f'¡Bienvenido(a) {user.first_name} {user.last_name}!')
                return redirect('nosotros')
            messages.error(request, 'Credenciales incorrectas o cuenta desactivada')
        else:
            messages.error(request, 'No se pudo procesar el formulario')
            show_form_errors(request, [form])
    else:
        form = IngresarForm()

    return render(request, 'core/inicio.html', { 'form': form })

@login_required
def formulario_gobernanza(request):
    preguntas = Pregunta.objects.all()
    if request.method == 'POST':
        form = GobernanzaForm(request.POST, preguntas=preguntas)
        if form.is_valid():
            for pregunta in preguntas:
                valor = form.cleaned_data[f'respuesta_{pregunta.id}']
                Respuesta.objects.update_or_create(
                    usuario=request.user,
                    pregunta=pregunta,
                    defaults={'valor': valor}
                )
            messages.success(request, 'Respuestas guardadas con éxito.')
            return redirect('formulario_gobernanza')
    else:
        form = GobernanzaForm(preguntas=preguntas)

    return render(request, 'core/gobernanza.html', {
        'form': form,
        'preguntas': preguntas,
    })

@login_required
def guardar_gobernanza(request):
    """Procesa y guarda las respuestas enviadas desde el formulario."""
    if request.method == 'POST':
        for pregunta in Pregunta.objects.all():
            valor = request.POST.get(f'respuesta_{pregunta.id}')
            if valor in ['si', 'no']:
                Respuesta.objects.update_or_create(
                    usuario=request.user,
                    pregunta=pregunta,
                    defaults={'valor': valor}
                )
        messages.success(request, 'Respuestas guardadas con éxito.')
    return redirect('formulario_gobernanza')

@user_passes_test(es_usuario_anonimo, login_url='inicio')
def ingresar(request):
    if request.method == "POST":
        form = IngresarForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                login(request, user)
                messages.success(request, f'¡Bienvenido(a) {user.first_name} {user.last_name}!')
                return redirect('inicio')
            messages.error(request, 'Credenciales incorrectas o cuenta desactivada')
        else:
            messages.error(request, 'No se pudo procesar el formulario')
            show_form_errors(request, [form])
    else:
        form = IngresarForm()

    return render(request, 'core/ingresar.html', { 'form': form })

@user_passes_test(es_usuario_anonimo, login_url='inicio')
def registro(request):
    if request.method == 'POST':
        form_usuario = RegistroUsuarioForm(request.POST)
        form_perfil = RegistroPerfilForm(request.POST, request.FILES)
        if form_usuario.is_valid() and form_perfil.is_valid():
            usuario = form_usuario.save()
            perfil = form_perfil.save(commit=False)
            perfil.usuario_id = usuario.id
            perfil.save()
            messages.success(request, f'Cuenta "{usuario.username}" creada exitosamente.')
            return redirect('ingresar')
        else:
            messages.error(request, 'Error al crear la cuenta')
            show_form_errors(request, [form_usuario, form_perfil])
    else:
        form_usuario = RegistroUsuarioForm()
        form_perfil = RegistroPerfilForm()

    return render(request, 'core/registro.html', {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
    })

# ------------------------------------------------------------------------------------------------------
# Vistas para usuarios autenticados
# ------------------------------------------------------------------------------------------------------

@login_required
def salir(request):
    messages.success(request, f'¡Hasta pronto {request.user.first_name} {request.user.last_name}!')
    logout(request)
    return redirect('inicio')

@login_required
def misdatos(request):
    if request.method == 'POST':
        form_usuario = UsuarioForm(request.POST, instance=request.user)
        form_perfil = RegistroPerfilForm(request.POST, request.FILES, instance=request.user.perfil)
        if form_usuario.is_valid() and form_perfil.is_valid():
            usuario = form_usuario.save()
            perfil = form_perfil.save(commit=False)
            perfil.usuario_id = usuario.id
            perfil.save()
            messages.success(request, 'Tus datos han sido actualizados.')
            return redirect('misdatos')
        else:
            messages.error(request, 'No fue posible actualizar tus datos')
            show_form_errors(request, [form_usuario, form_perfil])
    else:
        form_usuario = UsuarioForm(instance=request.user)
        form_perfil = RegistroPerfilForm(instance=request.user.perfil)

    return render(request, 'core/misdatos.html', {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
    })

@login_required
def mipassword(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraseña actualizada. Vuelve a iniciar sesión.')
            logout(request)
            return redirect('ingresar')
        else:
            messages.error(request, 'Error al actualizar la contraseña')
            show_form_errors(request, [form])
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'core/mipassword.html', { 'form': form })

# ------------------------------------------------------------------------------------------------------
# Vistas exclusivas para superusuario
# ------------------------------------------------------------------------------------------------------

@user_passes_test(es_superusuario_activo)
def mantenedor_usuarios(request, accion, id):
    usuario = get_object_or_404(User, id=id) if int(id) > 0 else None
    perfil = getattr(usuario, 'perfil', None)

    if request.method == 'POST':
        form_usuario = UsuarioForm(request.POST, instance=usuario)
        form_perfil = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form_usuario.is_valid() and form_perfil.is_valid():
            usuario = form_usuario.save()
            perfil = form_perfil.save(commit=False)
            perfil.usuario_id = usuario.id
            perfil.save()
            messages.success(request, f'Usuario {usuario.username} guardado.')
            return redirect('mantenedor_usuarios', accion='actualizar', id=usuario.id)
        else:
            messages.error(request, 'No fue posible guardar el usuario')
            show_form_errors(request, [form_usuario, form_perfil])

    elif request.method == 'GET' and accion == 'eliminar':
        eliminado, mensaje = eliminar_registro(User, id)
        messages.success(request, mensaje)
        return redirect('mantenedor_usuarios', accion='crear', id=0)
    else:
        form_usuario = UsuarioForm(instance=usuario)
        form_perfil = PerfilForm(instance=perfil)

    return render(request, 'core/mantenedor_usuarios.html', {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
        'accion': accion,
        'usuario': usuario,
    })

@user_passes_test(es_superusuario_activo)
def cambiar_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if user.is_active:
                new_password = User.objects.make_random_password()
                user.set_password(new_password)
                user.save()
                if enviar_correo_cambio_password(request, user, new_password):
                    messages.success(request, f'Nueva contraseña enviada a {user.username}.')
                else:
                    messages.error(request, f'Error al enviar la nueva contraseña a {user.username}.')
            else:
                messages.error(request, 'La cuenta está desactivada.')
        else:
            messages.error(request, 'El usuario no existe.')
    return redirect('mantenedor_usuarios', accion='crear', id=0)


def enviar_correo_cambio_password(request, user, password):
    try:
        subject = 'Cambio de contraseña'
        login_url = reverse('ingresar')
        html_message = render(request, 'common/formato_correo.html', {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_password': password,
            'link_to_login': request.build_absolute_uri(login_url),
        }).content.decode('utf-8')
        send_mail(
            subject,
            '',
            'info@tuempresa.com',
            [user.email],
            html_message=html_message
        )
        return True
    except Exception:
        return False

# Otras vistas generales


def nosotros(request):
    return render(request, 'core/nosotros.html')


def administrar_tienda(request):
    return render(request, 'core/administrar_tienda.html')
