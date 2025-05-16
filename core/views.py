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
from django.db.models.functions import TruncDate
from collections import defaultdict
from .models import Perfil, Pregunta, Respuesta
from .forms import (
    GobernanzaForm, PreguntaForm, 
    IngresarForm, UsuarioForm, PerfilForm,
    RegistroUsuarioForm, RegistroPerfilForm
)
from .tools import eliminar_registro, show_form_errors
# Importar función de poblamiento
from core.zpoblar import poblar_bd

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

@user_passes_test(es_usuario_anonimo, login_url='formulario_gobernanza')
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
                return redirect('formulario_gobernanza')
            messages.error(request, 'Credenciales incorrectas o cuenta desactivada')
        else:
            messages.error(request, 'No se pudo procesar el formulario')
            show_form_errors(request, [form])
    else:
        form = IngresarForm()

    return render(request, 'core/inicio.html', {'form': form})

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

    return render(request, 'core/ingresar.html', {'form': form})

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
# Vista de reporte de respuestas y puntajes
# ------------------------------------------------------------------------------------------------------

@login_required
@user_passes_test(es_superusuario_activo)
def mantenedor_respuestas(request, accion='listar', id=0):
    """
    CRUD para el mantenedor de respuestas:
     - 'listar' (o cualquier otro valor): lista usuarios con al menos una respuesta
     - 'ver': redirige a la vista de reporte de respuestas para ese usuario
     - 'eliminar': borra todas las respuestas del usuario
    """
    usuario = get_object_or_404(User, pk=id) if int(id) > 0 else None

    # VER reporte
    if accion == 'ver' and usuario:
        # redirige a tu ruta 'respuestas' con el user_id
        return redirect('respuestas', user_id=usuario.id)

    # ELIMINAR todas sus respuestas
    if accion == 'eliminar' and usuario:
        Respuesta.objects.filter(usuario=usuario).delete()
        messages.success(request, f'Todas las respuestas de "{usuario.username}" han sido eliminadas.')
        return redirect('mantenedor_respuestas')

    # LISTAR usuarios que tienen al menos una respuesta
    users_con_respuestas = (
        User.objects
            .filter(respuesta__isnull=False)
            .distinct()
            .select_related('perfil')
    )

    return render(request, 'core/mantenedor_respuestas.html', {
        'users': users_con_respuestas,
        'accion': accion,
        'usuario': usuario,
    })

@login_required
def respuestas_view(request, user_id=None):
    """
    Muestra el reporte de respuestas de un usuario.
    Si eres superusuario y pasas user_id, muestra ese usuario; si no, tu propio reporte.
    """
    # --- Determinar sobre quién consulto ---
    if user_id and request.user.is_superuser:
        target_user = get_object_or_404(User, id=user_id)
    else:
        target_user = request.user

    # --- Obtengo sus respuestas ---
    respuestas = Respuesta.objects.filter(usuario=target_user)

    # 1) Cálculo por dimensión
    scores = defaultdict(lambda: {'si': 0, 'total': 0})
    for r in respuestas:
        dim = r.pregunta.dimension
        scores[dim]['total'] += 1
        if r.valor == 'si':
            scores[dim]['si'] += 1

    # Raw y porcentaje por dimensión
    dimension_scores = {}
    for dim, v in scores.items():
        si = v['si']
        total = v['total']
        pct = (si / total * 100) if total else 0
        dimension_scores[dim] = {
            'raw': si,
            'pct': pct,
        }

    # 2) Totales globales
    total_raw    = sum(v['raw'] for v in dimension_scores.values())
    total_maxraw = sum(v['total'] for v in scores.values())
    total_pct    = (total_raw / total_maxraw * 100) if total_maxraw else 0

    # 3) Puntaje ponderado (ejemplo fijado a 260)
    max_weighted   = 260
    total_weighted = total_raw * (max_weighted / total_maxraw) if total_maxraw else 0

    # 4) Nivel de madurez global
    if total_pct < 25:
        nivel_global = 'Insuficiente'
    elif total_pct < 50:
        nivel_global = 'Básico'
    elif total_pct < 75:
        nivel_global = 'Medio'
    else:
        nivel_global = 'Avanzado'

    # 5) Datos para el radar
    dim_labels = list(dimension_scores.keys())
    dim_user   = [round(d['pct'], 1) for d in dimension_scores.values()]
    dim_max    = [100] * len(dim_labels)

    return render(request, 'core/respuestas.html', {
        'target_user':      target_user,
        'respuestas':       respuestas,
        'dimension_scores': dimension_scores,
        'total_raw':        total_raw,
        'total_weighted':   total_weighted,
        'total_pct':        total_pct,
        'nivel_global':     nivel_global,
        'total_maxraw':     total_maxraw,
        'max_weighted':     max_weighted,
        'dim_labels':       dim_labels,
        'dim_user':         dim_user,
        'dim_max':          dim_max,
    })

# ------------------------------------------------------------------------------------------------------
# Vistas para usuarios autenticados y superusuarios
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

    return render(request, 'core/mipassword.html', {'form': form})

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
def mantenedor_preguntas(request, accion, id):
    pregunta = get_object_or_404(Pregunta, id=id) if int(id) > 0 else None

    if request.method == 'POST':
        form_pregunta = PreguntaForm(request.POST, instance=pregunta)
        if form_pregunta.is_valid():
            form_pregunta.save()
            messages.success(request, 'Pregunta guardada correctamente.')
            return redirect('mantenedor_preguntas', accion='actualizar', id=form_pregunta.instance.id)
        else:
            messages.error(request, 'No fue posible guardar la pregunta.')
            show_form_errors(request, [form_pregunta])

    elif request.method == 'GET' and accion == 'eliminar':
        eliminado, mensaje = eliminar_registro(Pregunta, id)
        messages.success(request, mensaje)
        return redirect('mantenedor_preguntas', accion='crear', id=0)
    else:
        form_pregunta = PreguntaForm(instance=pregunta)

    preguntas = Pregunta.objects.all()
    return render(request, 'core/mantenedor_preguntas.html', {
        'form_pregunta': form_pregunta,
        'accion': accion,
        'pregunta': pregunta,
        'preguntas': preguntas,
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

# Nueva vista para poblar BD
@user_passes_test(es_superusuario_activo)
def poblar_bd_view(request):
    poblar_bd()
    messages.success(request, 'Base de datos poblada con preguntas y respuestas.')
    return redirect('formulario_gobernanza')

# Otras vistas generales

def nosotros(request):
    return render(request, 'core/nosotros.html')
