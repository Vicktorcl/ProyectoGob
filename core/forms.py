from django import forms
from django.forms import ModelForm, Form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil, Pregunta

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
