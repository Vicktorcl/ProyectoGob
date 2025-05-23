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
from django.urls import reverse
from django.db.models.functions import TruncDate
from collections import defaultdict
from .models import Perfil, Pregunta, Respuesta, Encuesta, EncuestaGD, PreguntaGD, RespuestaGD
from .forms import (
    GobernanzaForm, PreguntaForm, 
    IngresarForm, UsuarioForm, PerfilForm,
    RegistroUsuarioForm, RegistroPerfilForm, EncuestaGDForm
)
from .tools import eliminar_registro, show_form_errors
# Importar función de poblamiento
from core.zpoblar import poblar_bd
from core.zpoblar2 import poblar_gd
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
    """Procesa y guarda las respuestas como una nueva Encuesta."""
    if request.method == 'POST':
        # 1) Creamos una nueva encuesta para este usuario
        encuesta = Encuesta.objects.create(usuario=request.user)

        # 2) Por cada pregunta, creamos una Respuesta ligada a esa encuesta
        for pregunta in Pregunta.objects.all():
            valor = request.POST.get(f'respuesta_{pregunta.id}')
            if valor in ['si', 'no']:
                Respuesta.objects.create(
                    encuesta=encuesta,
                    pregunta=pregunta,
                    valor=valor
                )

        messages.success(request, 'Encuesta guardada con éxito.')
        # Redirigimos a la selección de encuesta para poder verla
        return redirect('seleccionar_encuesta')

    # Si se accede por GET, redirigimos al formulario
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
def seleccionar_encuesta(request, user_id=None):
    if user_id and request.user.is_superuser:
        target = get_object_or_404(User, pk=user_id)
    else:
        target = request.user

    # Ahora traemos las Encuesta en lugar de fechas desde Respuesta
    surveys = Encuesta.objects.filter(usuario=target).order_by('-fecha')

    return render(request, 'core/seleccionar_encuesta.html', {
        'target':  target,
        'surveys': surveys,
    })


@login_required
def respuestas_view(request):
    """
    Muestra el reporte de una encuesta concreta, indicada por GET.encuesta_id.
    Si no se recibe encuesta_id, redirige a seleccionar_encuesta.
    Un superusuario puede ver cualquier encuesta; un usuario normal solo la suya.
    """
    enc_id = request.GET.get('encuesta_id')
    if not enc_id:
        # no se indicó cuál, volvemos a la selección
        return redirect('seleccionar_encuesta')

    # 1) Obtener la encuesta y verificar permisos
    encuesta = get_object_or_404(Encuesta, id=enc_id)
    if not request.user.is_superuser and encuesta.usuario != request.user:
        messages.error(request, "No tienes permiso para ver esa encuesta.")
        return redirect('seleccionar_encuesta')

    # 2) Cargar las respuestas de esa encuesta
    qs = Respuesta.objects.filter(encuesta=encuesta).select_related('pregunta')

    # 3) Cálculo por dimensión
    scores = defaultdict(lambda: {'si': 0, 'total': 0})
    for r in qs:
        dim = r.pregunta.dimension
        scores[dim]['total'] += 1
        if r.valor == 'si':
            scores[dim]['si'] += 1

    # 4) Raw y porcentaje por dimensión
    dimension_scores = {}
    for dim, v in scores.items():
        si = v['si']
        total = v['total']
        pct = (si / total * 100) if total else 0
        dimension_scores[dim] = {'raw': si, 'pct': pct}

    # 5) Totales globales
    total_raw    = sum(d['raw'] for d in dimension_scores.values())
    total_maxraw = sum(v['total'] for v in scores.values())
    total_pct    = (total_raw / total_maxraw * 100) if total_maxraw else 0

    # 6) Puntaje ponderado (fijo a 260 de ejemplo)
    max_weighted   = 260
    total_weighted = total_raw * (max_weighted / total_maxraw) if total_maxraw else 0

    # 7) Nivel global
    if total_pct < 25:
        nivel_global = 'Insuficiente'
    elif total_pct < 50:
        nivel_global = 'Básico'
    elif total_pct < 75:
        nivel_global = 'Medio'
    else:
        nivel_global = 'Avanzado'

    # 8) Datos para el radar
    dim_labels = list(dimension_scores.keys())
    dim_user   = [round(d['pct'], 1) for d in dimension_scores.values()]
    dim_max    = [100] * len(dim_labels)

    return render(request, 'core/respuestas.html', {
        'target_user':      encuesta.usuario,
        'encuesta':         encuesta,
        'respuestas':       qs,
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


@login_required
@user_passes_test(es_superusuario_activo)
def mantenedor_respuestas(request, accion='listar', id=0):
    """
    CRUD para el mantenedor de respuestas:
     - 'listar': lista usuarios con al menos una encuesta
     - 'ver': redirige a respuestas_view pasando user_id y encuesta_id
     - 'eliminar': borra todas las respuestas de un usuario
    """
    usuario = get_object_or_404(User, pk=id) if int(id) > 0 else None

    # VER reporte para un usuario y encuesta concreta
    if accion == 'ver' and usuario:
        encuesta_id = request.GET.get('encuesta_id')
        return redirect(f"{ reverse('respuestas') }?user_id={usuario.id}&encuesta_id={encuesta_id}")

    # ELIMINAR todas sus respuestas
    if accion == 'eliminar' and usuario:
        Respuesta.objects.filter(encuesta__usuario=usuario).delete()
        messages.success(request, f'Todas las respuestas de "{usuario.username}" han sido eliminadas.')
        return redirect('mantenedor_respuestas')

    # LISTAR usuarios que tienen al menos una encuesta
    users_with_surveys = (
        User.objects
            .filter(encuesta__isnull=False)
            .distinct()
            .select_related('perfil')
    )

    user_data = []
    for u in users_with_surveys:
        # obtenemos todas las encuestas que haya hecho este usuario
        encs = Encuesta.objects.filter(usuario=u).order_by('-fecha')
        # armamos lista de dicts con id y fecha para cada encuesta
        surveys = [
            { 'id': e.id, 'date': e.fecha.date().isoformat() }
            for e in encs
        ]
        user_data.append({
            'user': u,
            'surveys': surveys
        })

    return render(request, 'core/mantenedor_respuestas.html', {
        'user_data': user_data,
        'accion':    accion,
        'usuario':   usuario,
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

@login_required
def seleccionar_encuesta_gd(request, user_id=None):
    if user_id and es_superusuario_activo(request.user):
        target = get_object_or_404(request.user.__class__, pk=user_id)
    else:
        target = request.user

    # traer todas las encuestas GD de ese usuario
    encuestas = (
        EncuestaGD.objects
                 .filter(usuario=target)
                 .order_by('-fecha')
    )
    return render(request, 'core/seleccionar_encuesta_gd.html', {
        'target':   target,
        'encuestas': encuestas,
    })

# 2) Creación de una nueva encuesta GD
@login_required
def nueva_encuesta_gd(request):
    # Ordena por grupo y categoría para mostrarlas agrupadas en el template
    preguntas = PreguntaGD.objects.all().order_by('grupo', 'categoria', 'area', 'numero')

    if request.method == 'POST':
        # Creas la nueva encuesta
        encuesta = EncuestaGD.objects.create(usuario=request.user)
        # Iteras sobre cada pregunta y guardas la respuesta
        for pregunta in preguntas:
            valor = request.POST.get(f'p_{pregunta.id}')
            if valor:
                RespuestaGD.objects.create(
                    encuesta=encuesta,
                    pregunta=pregunta,
                    valoracion=int(valor)
                )
        return redirect('reporte_gd', encuesta_id=encuesta.id)

    # Para el GET, agrupamos en un dict por grupo→categoría
    preguntas_agrupadas = {}
    for pq in preguntas:
        preguntas_agrupadas\
            .setdefault(pq.grupo, {})\
            .setdefault(pq.categoria, [])\
            .append(pq)

    return render(request, 'core/nueva_encuesta_gd.html', {
        'preguntas_agrupadas': preguntas_agrupadas,
    })
    

@login_required
@user_passes_test(es_superusuario_activo)
def zpoblar2_view(request):
    """
    Ejecuta zpoblar_gd.poblar_gd() para poblar las preguntas GD
    y redirige con un mensaje de éxito.
    """
    poblar_gd()
    messages.success(request, "Preguntas GD pobladas correctamente.")
    return redirect('nueva_encuesta_gd')

@login_required
def reporte_gd(request, encuesta_id):
    encuesta = get_object_or_404(EncuestaGD, pk=encuesta_id)
    # Sólo su autor o el superusuario
    if encuesta.usuario != request.user and not es_superusuario_activo(request.user):
        return redirect('seleccionar_encuesta_gd')

    # 1) Traer todas las respuestas de esa encuesta
    respuestas = RespuestaGD.objects.filter(encuesta=encuesta).select_related('pregunta')

    # 2) Extraer grupos únicos para el dropdown/accordion
    groups = sorted({ r.pregunta.grupo for r in respuestas })

    # 3) Cálculo por “dimensión” = grupo
    scores = defaultdict(lambda: {'acum': 0.0, 'peso_total': 0.0})
    for r in respuestas:
        grp     = r.pregunta.grupo
        peso    = float(r.pregunta.peso_area)
        scores[grp]['acum']       += peso
        scores[grp]['peso_total'] += peso

    dimension_scores = {}
    for grp, v in scores.items():
        acum      = v['acum']
        peso_tot  = v['peso_total']
        pct       = (acum / peso_tot * 100) if peso_tot else 0
        dimension_scores[grp] = {
            'score':     acum,
            'max_score': peso_tot,
            'pct':       pct,
        }

    # 4) Totales globales
    total_score     = sum(d['score']     for d in dimension_scores.values())
    total_max_score = sum(d['max_score'] for d in dimension_scores.values())
    total_pct       = (total_score / total_max_score * 100) if total_max_score else 0

    # 5) Datos para radar chart
    radar_labels    = list(dimension_scores.keys())
    radar_user_data = [round(d['pct'], 1) for d in dimension_scores.values()]
    radar_max_data  = [100] * len(radar_labels)

    return render(request, 'core/reporte_gd.html', {
        'encuesta':          encuesta,
        'respuestas':        respuestas,
        'groups':            groups,
        'dimension_scores':  dimension_scores,
        'total_score':       total_score,
        'total_max_score':   total_max_score,
        'total_pct':         total_pct,
        'radar_labels':      radar_labels,
        'radar_user_data':   radar_user_data,
        'radar_max_data':    radar_max_data,
    })
