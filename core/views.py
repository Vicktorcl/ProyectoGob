from datetime import date
from django.contrib.auth.models import User 
from collections import defaultdict
from django.db.models import Count, Max
from django.db.models.functions import TruncDate
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse

from .models import (
    Perfil, Pregunta, OpcionPregunta,
    Respuesta, Encuesta,
    EncuestaGD, PreguntaGD, RespuestaGD
)
from .forms import (
    GobernanzaForm, PreguntaForm,
    IngresarForm, UsuarioForm, PerfilForm,
    RegistroUsuarioForm, RegistroPerfilForm,
    EncuestaGDForm, PreguntaGDForm
)
from .tools import eliminar_registro, show_form_errors
from core.zpoblar import poblar_bd
from core.zpoblar2 import poblar_gd
# ------------------------------------------------------------------------------------------------------
# Funciones auxiliares para autorización
# ------------------------------------------------------------------------------------------------------

# Inline formset para opciones de Pregunta clásica
OpcionFormSet = inlineformset_factory(
    Pregunta, OpcionPregunta,
    fields=('texto', 'puntaje', 'orden'),
    extra=1, can_delete=True
)

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
    """
    GET: muestra las preguntas con todas sus opciones.
    POST: guarda todas las respuestas del usuario en una nueva Encuesta.
    """

    # --- 1) Cargar todas las preguntas ordenadas ---
    preguntas = Pregunta.objects.all().order_by('dimension', 'codigo')

    # --- 2) Traer todas las opciones y agruparlas en un dict { pregunta_pk: [OpcionPregunta, ...] } ---
    todas_opciones = OpcionPregunta.objects.all().order_by('pregunta_id', 'orden')
    opciones_por_pregunta = defaultdict(list)
    for opcion in todas_opciones:
        opciones_por_pregunta[opcion.pregunta_id].append(opcion)

    # --- 3) Asignar a cada pregunta un atributo "lista_opciones" (no tocar 'pregunta.opciones') ---
    for pregunta in preguntas:
        pregunta.lista_opciones = opciones_por_pregunta.get(pregunta.pk, [])

    # --- 4) Si llega un POST, procesamos las respuestas ---
    if request.method == 'POST':
        usuario = request.user
        encuesta = Encuesta.objects.create(usuario=usuario)

        for pregunta in preguntas:
            nombre_campo = f"respuesta_{pregunta.pk}"
            valor = request.POST.get(nombre_campo)
            if not valor:
                continue

            # Si la pregunta tiene opciones en nuestra lista dinámica
            if pregunta.lista_opciones:
                try:
                    opcion_obj = get_object_or_404(OpcionPregunta, pk=int(valor), pregunta=pregunta)
                except ValueError:
                    continue
                Respuesta.objects.create(
                    encuesta=encuesta,
                    pregunta=pregunta,
                    opcion=opcion_obj
                )
            else:
                # Pregunta sin opciones definidas → valor esperado "si" o "no"
                Respuesta.objects.create(
                    encuesta=encuesta,
                    pregunta=pregunta,
                    valor=valor
                )

        messages.success(request, "Respuestas guardadas con éxito.")
        return redirect('formulario_gobernanza')

    # --- 5) GET: renderizamos plantilla pasando 'preguntas', cada una con 'lista_opciones' ---
    return render(request, 'core/gobernanza.html', {
        'preguntas': preguntas
    })

@login_required
def guardar_gobernanza(request):
    if request.method == 'POST':
        encuesta = Encuesta.objects.create(usuario=request.user)
        preguntas = Pregunta.objects.all()
        for pregunta in preguntas:
            val = request.POST.get(f'respuesta_{pregunta.pk}')
            if pregunta.opciones.exists():
                # valor es el PK de OpcionPregunta
                option = get_object_or_404(OpcionPregunta, pk=val)
                Respuesta.objects.create(
                    encuesta=encuesta,
                    pregunta=pregunta,
                    opcion=option
                )
            else:
                # las clásicas sí/no
                Respuesta.objects.create(
                    encuesta=encuesta,
                    pregunta=pregunta,
                    valor=val
                )
        messages.success(request, 'Encuesta guardada con éxito.')
        return redirect('seleccionar_encuesta')
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
    Muestra el reporte de una encuesta concreta (GET.encuesta_id). Si no hay encuesta_id,
    redirige a seleccionar_encuesta. El puntaje de cada respuesta proviene de
    OpcionPregunta.puntaje (o, en preguntas clásicas Sí/No, 6 para 'si' y 0 para 'no').
    El puntaje máximo se calcula sólo sobre las preguntas RESPONDIDAS en esta encuesta:
    - Por dimensión, máximo = (# preguntas respondidas en esa dimensión) × 6
    - Global, máximo = suma de todos esos máximos (equivalente a total preguntas respondidas × 6)
    Esto evita que se contabilicen preguntas de otras encuestas y corrige el valor de 1872.
    """

    enc_id = request.GET.get('encuesta_id')
    if not enc_id:
        return redirect('seleccionar_encuesta')

    # 1) Obtener la encuesta y verificar permisos
    encuesta = get_object_or_404(Encuesta, id=enc_id)
    if not request.user.is_superuser and encuesta.usuario != request.user:
        messages.error(request, "No tienes permiso para ver esa encuesta.")
        return redirect('seleccionar_encuesta')

    # 2) Puntaje fijo POR PREGUNTA (para preguntas clásicas): 6
    PTS_PREGUNTA = 6.0

    # 3) Cargar las respuestas de ESTA encuesta
    #    Seleccionamos pregunta y opción para cada Respuesta
    respuestas_qs = (
        Respuesta.objects
                 .filter(encuesta=encuesta)
                 .select_related('pregunta', 'opcion')
    )

    # 4) Agrupar las preguntas RESPONDIDAS por dimensión
    #    Usaremos esto para saber cuántas preguntas se respondieron en cada dimensión
    preguntas_respondidas_por_dim = defaultdict(set)
    #    Y al mismo tiempo iremos sumando el puntaje que obtuvo el usuario
    puntaje_usuario_por_dim = defaultdict(float)

    for respuesta in respuestas_qs:
        pregunta = respuesta.pregunta
        dim = pregunta.dimension
        pid = pregunta.pk

        # 4.1) Agregamos a ese conjunto el ID de la pregunta (para contar más tarde)
        preguntas_respondidas_por_dim[dim].add(pid)

        # 4.2) Calcular el puntaje obtenido en esta respuesta:
        if respuesta.opcion_id:
            # Viene de OpcionPregunta → usamos su puntaje real
            puntaje_usuario_por_dim[dim] += float(respuesta.opcion.puntaje)
        else:
            # Pregunta clásica Sí/No: “si” → 6 puntos, “no” → 0
            puntaje_usuario_por_dim[dim] += (PTS_PREGUNTA if respuesta.valor == 'si' else 0.0)

    # 5) Construir la estructura dimension_scores
    dimension_scores = {}
    for dim, preguntas_set in preguntas_respondidas_por_dim.items():
        user_sum = puntaje_usuario_por_dim[dim]
        count_q = len(preguntas_set)               # número de preguntas respondidas en esta dimensión
        max_sum = count_q * PTS_PREGUNTA           # máximo posible en esa dimensión

        pct = (user_sum / max_sum * 100) if max_sum else 0.0
        dimension_scores[dim] = {
            'user_sum': round(user_sum, 1),
            'max_sum':  round(max_sum, 1),
            'pct':      round(pct, 1),
            'count_q':  count_q
        }

    # 6) Totales globales
    total_user   = sum(v['user_sum'] for v in dimension_scores.values())
    total_maxraw = sum(v['max_sum']  for v in dimension_scores.values())
    total_pct    = (total_user / total_maxraw * 100) if total_maxraw else 0.0

    # 7) Puntaje ponderado (ejemplo: escala fija a 260 puntos totales)
    max_weighted   = 260.0
    total_weighted = total_user * (max_weighted / total_maxraw) if total_maxraw else 0.0

    # 8) Nivel global según porcentaje
    if total_pct < 25:
        nivel_global = 'Insuficiente'
    elif total_pct < 50:
        nivel_global = 'Básico'
    elif total_pct < 75:
        nivel_global = 'Medio'
    else:
        nivel_global = 'Avanzado'

    # 9) Datos para gráfico radar
    dim_labels = list(dimension_scores.keys())
    dim_user   = [dimension_scores[d]['pct'] for d in dim_labels]
    dim_max    = [100.0] * len(dim_labels)

    return render(request, 'core/respuestas.html', {
        'target_user':      encuesta.usuario,
        'encuesta':         encuesta,
        'respuestas':       respuestas_qs,
        'dimension_scores': dimension_scores,
        'total_user':       round(total_user, 1),
        'total_weighted':   round(total_weighted, 1),
        'total_pct':        round(total_pct, 1),
        'nivel_global':     nivel_global,
        'total_maxraw':     round(total_maxraw, 1),
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
     - 'listar': muestra usuarios que tienen encuestas
     - 'eliminar': borra todas las respuestas de un usuario
     - 'eliminar_encuesta': borra una sola encuesta y sus respuestas
     - 'ver': redirige a respuestas_view con user_id y encuesta_id
    """
    usuario = get_object_or_404(User, pk=id) if int(id) > 0 else None

    # Si la acción es 'ver' (opcional: podríamos eliminarlo si ya no lo usamos aquí)
    if accion == 'ver' and usuario:
        encuesta_id = request.GET.get('encuesta_id')
        return redirect(f"{ reverse('respuestas') }?user_id={usuario.id}&encuesta_id={encuesta_id}")

    # ELIMINAR TODAS las respuestas de un usuario
    if accion == 'eliminar' and usuario:
        Respuesta.objects.filter(encuesta__usuario=usuario).delete()
        Encuesta.objects.filter(usuario=usuario).delete()
        messages.success(request, f'Todas las respuestas de "{usuario.username}" han sido eliminadas.')
        return redirect('mantenedor_respuestas')

    # ELIMINAR una sola encuesta (y sus respuestas)
    if accion == 'eliminar_encuesta' and usuario:
        # Tomamos encuesta_id de GET
        encuesta_id = request.GET.get('encuesta_id')
        if encuesta_id:
            encuesta = get_object_or_404(Encuesta, pk=encuesta_id, usuario=usuario)
            # Borra todas las respuestas de esa encuesta, luego la encuesta
            Respuesta.objects.filter(encuesta=encuesta).delete()
            encuesta.delete()
            messages.success(request, f'Encuesta {encuesta_id} de "{usuario.username}" eliminada correctamente.')
        else:
            messages.error(request, "No se especificó encuesta para eliminar.")
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
        encs = Encuesta.objects.filter(usuario=u).order_by('-fecha')
        surveys = [
            {'id': e.id, 'date': e.fecha.date().isoformat()}
            for e in encs
        ]
        user_data.append({
            'user':    u,
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

@login_required
@user_passes_test(es_superusuario_activo)
def mantenedor_preguntas(request, accion, id):
    """
    Mantenedor de preguntas con inline formset de opciones.
    - accion: 'crear', 'actualizar' o 'eliminar'
    - id: 0 para crear, o el PK de la pregunta para editar/borrar.
    """
    # Validar acción
    if accion not in ('crear', 'actualizar', 'eliminar'):
        messages.error(request, 'Acción inválida.')
        return redirect('mantenedor_preguntas', accion='crear', id=0)

    pregunta = None
    if accion in ('actualizar', 'eliminar'):
        pregunta = get_object_or_404(Pregunta, pk=id)

    # Eliminar
    if accion == 'eliminar' and pregunta:
        pregunta.delete()
        messages.success(request, 'Pregunta eliminada correctamente.')
        return redirect('mantenedor_preguntas', accion='crear', id=0)

    # Bind / inicialización
    if request.method == 'POST':
        form    = PreguntaForm(request.POST, instance=pregunta)
        formset = OpcionFormSet(request.POST, instance=pregunta)
        if form.is_valid() and formset.is_valid():
            # 1) Guardar pregunta
            pregunta = form.save(commit=False)
            if accion == 'crear':
                siguiente = Pregunta.objects.aggregate(
                    max_codigo=Max('codigo')
                )['max_codigo'] or 0
                pregunta.codigo = siguiente + 1
            pregunta.save()

            # 2) Reasignar orden automático
            for idx, subform in enumerate(formset.forms, start=1):
                # si no está marcado para borrado
                if not subform.cleaned_data.get('DELETE', False):
                    subform.instance.orden = idx

            # 3) Guardar opciones
            formset.instance = pregunta
            formset.save()

            messages.success(request, 'Pregunta y opciones guardadas correctamente.')
            return redirect('mantenedor_preguntas', accion='actualizar', id=pregunta.pk)
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form    = PreguntaForm(instance=pregunta)
        formset = OpcionFormSet(instance=pregunta)

    preguntas = Pregunta.objects.all()
    return render(request, 'core/mantenedor_preguntas.html', {
        'form':      form,
        'formset':   formset,
        'pregunta':  pregunta,
        'preguntas': preguntas,
        'accion':    accion,
    })
    
@login_required
@user_passes_test(es_superusuario_activo)
def mantenedor_preguntas_gd_gd(request, accion='listar', id=0):
    """
    CRUD para PreguntaGD:
      - 'listar': muestra todas las preguntas GD
      - 'crear':  crea una nueva
      - 'actualizar': edita existente
      - 'eliminar': borra existente
    """
    # Validar acción
    if accion not in ('listar', 'crear', 'actualizar', 'eliminar'):
        messages.error(request, 'Acción inválida.')
        return redirect('mantenedor_preguntas_gd')

    pregunta = None
    if id > 0:
        pregunta = get_object_or_404(PreguntaGD, pk=id)

    # ELIMINAR
    if accion == 'eliminar' and pregunta:
        pregunta.delete()
        messages.success(request, 'Pregunta GD eliminada correctamente.')
        return redirect('mantenedor_preguntas_gd')

    # CREAR / ACTUALIZAR
    if accion in ('crear', 'actualizar'):
        if request.method == 'POST':
            form = PreguntaGDForm(request.POST, instance=pregunta)
            if form.is_valid():
                obj = form.save()
                msg = 'creada' if accion=='crear' else 'actualizada'
                messages.success(request, f'Pregunta GD {msg} correctamente.')
                return redirect('mantenedor_preguntas_gd', accion='actualizar', id=obj.pk)
            else:
                messages.error(request, 'Corrige los errores del formulario.')
        else:
            form = PreguntaGDForm(instance=pregunta)

        # listar preguntas para mostrar al lado del form
        preguntas = PreguntaGD.objects.all().order_by('grupo','categoria','area','numero')
        return render(request, 'core/mantenedor_preguntas_gd.html', {
            'form':      form,
            'pregunta':  pregunta,
            'preguntas': preguntas,
            'accion':    accion,
        })

    # LISTAR (GET en 'listar')
    preguntas = PreguntaGD.objects.all().order_by('grupo','categoria','area','numero')
    return render(request, 'core/mantenedor_preguntas_gd.html', {
        'form':      None,
        'pregunta':  None,
        'preguntas': preguntas,
        'accion':    'listar',
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
