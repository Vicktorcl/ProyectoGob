from django import forms
from django.forms import ModelForm, Form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil, Pregunta, PreguntaGD, RespuestaGD

# Formulario para ingresar un nuevo usuario
class IngresarForm(Form):
    username = forms.CharField(widget=forms.TextInput(), label="Nombre de usuario")
    password = forms.CharField(widget=forms.PasswordInput(), label="Contraseña")
    class Meta:
        fields = ['username', 'password']
        

# Formulario dinámico para las preguntas de gobernanza de datos
class GobernanzaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        preguntas = kwargs.pop('preguntas', None)
        super().__init__(*args, **kwargs)
        if preguntas is None:
            preguntas = Pregunta.objects.all()
        for pregunta in preguntas:
            field_name = f'respuesta_{pregunta.id}'
            self.fields[field_name] = forms.ChoiceField(
                label=f"{pregunta.dimension} – {pregunta.criterio}: {pregunta.texto}",
                choices=[('si', 'Sí'), ('no', 'No')],
                widget=forms.RadioSelect(attrs={'class': 'respuesta-btn'}),
                required=True,
            )


# Formulario para registro de nuevo usuario
class RegistroUsuarioForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1' , 'password2']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo de contacto',
            'password2': 'Confirme su contraseña'
        }

# Formulario para crear preguntas
class PreguntaForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ['dimension', 'criterio', 'texto']
        widgets = {
            'dimension': forms.TextInput(attrs={'class': 'form-control'}),
            'criterio': forms.TextInput(attrs={'class': 'form-control'}),
            'texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# Formulario para registro de nuevo perfil (empresa)
class RegistroPerfilForm(ModelForm):
    class Meta:
        model = Perfil
        fields = ['rut', 'nombre_empresa']

# Formulario para editar datos de usuario
class UsuarioForm(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'email': 'Correo'
        }

# Formulario para modificar perfil (empresa)
class PerfilForm(ModelForm):
    class Meta:
        model = Perfil
        fields = ['rut', 'nombre_empresa']


class EncuestaGDForm(forms.Form):
    """
    Un form dinámico que crea un campo por cada PreguntaGD para
    que el usuario seleccione un nivel.
    """
    def __init__(self, *args, preguntas=None, **kwargs):
        super().__init__(*args, **kwargs)
        if preguntas is None:
            preguntas = PreguntaGD.objects.all().order_by('dimension','nivel','codigo')
        for pregunta in preguntas:
            field_name = f'preg_{pregunta.id}'
            self.fields[field_name] = forms.ChoiceField(
                label=pregunta.texto,
                choices=PreguntaGD.NIVEL_CHOICES,
                widget=forms.Select(attrs={'class': 'form-select'}),
                help_text=pregunta.get_nivel_display(),
                required=True,
            )
            # Guarda la instancia para accederla en la vista
            self.fields[field_name].pregunta = pregunta

class RespuestaGDForm(forms.ModelForm):
    class Meta:
        model = RespuestaGD
        # usa 'valoracion' en lugar de 'valor':
        fields = ['pregunta', 'valoracion']
        widgets = {
            'pregunta': forms.HiddenInput(),  # si así lo necesitas
        }
        labels = {
            'valoracion': 'Nivel seleccionado',
        }