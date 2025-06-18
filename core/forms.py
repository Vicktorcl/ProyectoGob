from django import forms
from django.forms.models import inlineformset_factory
from django.forms import ModelForm, Form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil, Pregunta, PreguntaGD, RespuestaGD, OpcionPregunta


class PreguntaGDForm(forms.ModelForm):
    class Meta:
        model = PreguntaGD
        fields = [
            'codigo',
            'grupo',
            'categoria',
            'area',
            'texto',
            'peso_area',
            'nivel',
        ]  # <---- Quitamos 'numero' de aquí
        widgets = {
            'codigo':     forms.TextInput(attrs={'class': 'form-control'}),
            'grupo':      forms.TextInput(attrs={'class': 'form-control'}),
            'categoria':  forms.TextInput(attrs={'class': 'form-control'}),
            'area':       forms.TextInput(attrs={'class': 'form-control'}),
            'texto':      forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'peso_area':  forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nivel':      forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'codigo':    'Código',
            'grupo':     'Grupo',
            'categoria': 'Categoría',
            'area':      'Área',
            'texto':     'Texto de la pregunta',
            'peso_area': 'Peso del área',
            'nivel':     'Nivel de madurez',
        }
        
# Formulario para ingresar un nuevo usuario
class IngresarForm(Form):
    username = forms.CharField(widget=forms.TextInput(), label="Nombre de usuario")
    password = forms.CharField(widget=forms.PasswordInput(), label="Contraseña")
    class Meta:
        fields = ['username', 'password']
        

class GobernanzaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        preguntas = kwargs.pop('preguntas', None)
        super().__init__(*args, **kwargs)
        if preguntas is None:
            preguntas = Pregunta.objects.all()
        for pregunta in preguntas:
            field_name = f'respuesta_{pregunta.pk}'
            # Obtenemos todas las opciones para esta pregunta:
            opts = pregunta.opciones.all()
            # Si no tiene opciones, dejamos el si/no por defecto:
            if not opts:
                choices = [('si', 'Sí'), ('no', 'No')]
            else:
                # Sino, construimos choices dinámicamente:
                # usamos el PK de la opcion como valor, y su texto como label
                choices = [(opt.pk, opt.texto) for opt in opts]
            self.fields[field_name] = forms.ChoiceField(
                label=f"{pregunta.dimension} – {pregunta.criterio}: {pregunta.texto}",
                choices=choices,
                widget=forms.RadioSelect(attrs={'class': 'respuesta-btn'}),
                required=True,
            )
            # Guardamos la pregunta en el campo para la vista:
            self.fields[field_name].pregunta = pregunta


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

# Formulario para crear pregunta
class PreguntaForm(ModelForm):
    class Meta:
        model = Pregunta
        fields = ['codigo', 'dimension', 'criterio', 'texto']
        widgets = {
            'codigo':    forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'dimension': forms.TextInput(attrs={'class': 'form-control'}),
            'criterio':  forms.TextInput(attrs={'class': 'form-control'}),
            'texto':     forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'codigo': 'Código de la pregunta',
        }

# ————————————————
# Form para Opciones de Pregunta
# ————————————————
class OpcionPreguntaForm(ModelForm):
    class Meta:
        model = OpcionPregunta
        fields = ['texto', 'puntaje', 'orden']
        widgets = {
            'texto':   forms.TextInput(attrs={'class': 'form-control'}),
            'puntaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'orden':   forms.NumberInput(attrs={'class': 'form-control'}),
        }

# Inline formset para ligar Opciones a la Pregunta
OpcionFormSet = inlineformset_factory(
    Pregunta,
    OpcionPregunta,
    form=OpcionPreguntaForm,
    extra=1,
    can_delete=True
)



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