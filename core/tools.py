from django.core.exceptions import ValidationError
from django.utils.safestring import SafeString
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from .models import Perfil
from .forms import UsuarioForm, PerfilForm, UsuarioForm

def eliminar_registro(modelo, clave_primaria):
    eliminado, mensaje = verificar_eliminar_registro(modelo, clave_primaria, True)
    return eliminado, mensaje

def verificar_eliminar_registro(modelo, clave_primaria, debe_eliminar_registro=False):
    es_eliminar_usuario = True if issubclass(modelo, User) else False

    # Si eliminamos un usuario, redirigimos la lógica al modelo Perfil
    if es_eliminar_usuario:
        registro_usuario = User.objects.get(pk=clave_primaria)
        modelo = Perfil
        clave_primaria = registro_usuario.perfil.pk

    # Primero obtenemos la instancia que queremos eliminar
    if not modelo.objects.filter(pk=clave_primaria).exists():
        return False, f'¡No se puede eliminar {clave_primaria}, no existe en {modelo._meta.verbose_name_plural}.'
    instancia = modelo.objects.get(pk=clave_primaria)
    info_registro = str(instancia)

    # Obtenemos el texto de la acción de eliminar desde la instancia, si existe
    if hasattr(instancia, 'acciones') and callable(instancia.acciones):
        acciones_dict = instancia.acciones()
        accion_eliminar = acciones_dict.get('accion_eliminar', 'eliminar')
    else:
        accion_eliminar = 'eliminar'

    # Verificar relaciones foráneas
    for tabla_relacionada in modelo._meta.related_objects:
        modelo_relacionado = tabla_relacionada.related_model
        nombre_campo_relacionado = tabla_relacionada.field.name
        nombre_tabla_relacionada_plural = modelo_relacionado._meta.verbose_name_plural
        if modelo_relacionado.objects.filter(**{nombre_campo_relacionado: clave_primaria}).exists():
            return False, (
                f'¡No se puede {accion_eliminar} "{info_registro}", '
                f'está presente en {nombre_tabla_relacionada_plural}!'
            )

    # Intentar eliminar
    try:
        if debe_eliminar_registro:
            if es_eliminar_usuario:
                registro_usuario.delete()
                return True, f'¡El Usuario "{registro_usuario.get_full_name()}" fue eliminado correctamente!'
            else:
                instancia.delete()
                return True, f'¡El registro de {modelo._meta.verbose_name} "{info_registro}" fue eliminado correctamente!'
    except Exception as error:
        return False, (
            f'Comuníquese con el administrador. '
            f'No se pudo eliminar {modelo._meta.verbose_name} "{info_registro}": {error}'
        )

def validar_password(password, request=None, add_error_messages=False):
    try:
        validate_password(password)
        return True
    except ValidationError as error:
        if add_error_messages:
            error_messages = '<ul>' + ''.join(f'<li>{e}</li>' for e in error.messages) + '</ul>'
            field_name = User._meta.get_field('password').verbose_name
            messages.error(request, SafeString(f'{field_name}: {error_messages}'))
        return False

def validar_username(username, request=None, add_error_messages=False):
    validator = UnicodeUsernameValidator()
    try:
        validator(username)
        return True
    except ValidationError as e:
        if add_error_messages:
            name = User._meta.get_field('username').verbose_name
            messages.error(request, SafeString(f'{name}: {e.messages[0]}'))
        return False

def validar_username_repetido(username, excluded_username=None, request=None, add_error_messages=False):
    qs = User.objects.exclude(username=excluded_username) if excluded_username else User.objects
    if qs.filter(username=username).exists():
        if add_error_messages:
            messages.error(request, f'Nombre de usuario: El nombre "{username}" ya existe.')
        return False
    return True

def show_form_errors(request, forms):
    request.session['backend_html_form_errors'] = ''
    html = ''
    for form in forms:
        for field in form:
            if field.errors:
                html += f'<strong>{field.label}:</strong><ul>' + ''.join(f'<li>{e}</li>' for e in field.errors) + '</ul>'
    if html:
        request.session['backend_html_form_errors'] = SafeString(f'<div style="text-align:left">{html}</div>')
