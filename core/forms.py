from django import forms
from django.forms.models import inlineformset_factory
from django.forms import ModelForm, Form
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Perfil, Pregunta, PreguntaGD, RespuestaGD, OpcionPregunta, Perfil


class IngresarForm(Form):
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu usuario',
            'autofocus': True,
        }),
        error_messages={'required': 'El nombre de usuario es obligatorio.'}
    )
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu contraseña',
        }),
        error_messages={'required': 'La contraseña es obligatoria.'}
    )

    error_messages = {
        'invalid_login': 'Usuario o contraseña incorrectos.',
        'inactive': 'Esta cuenta está desactivada.',
    }

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
    username = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Usuario'}),
        error_messages={'required':'El nombre de usuario es obligatorio.'}
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'tu@ejemplo.com'}),
        error_messages={'required':'El correo es obligatorio.','invalid':'Correo inválido.'}
    )
    password1 = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Contraseña'}),
        help_text='Mínimo 8 caracteres.',
        error_messages={'required':'La contraseña es obligatoria.'}
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Repite la contraseña'}),
        error_messages={'required':'Confirma la contraseña.'}
    )

    class Meta:
        model = User
        fields = ['username','email','password1','password2']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo ya está registrado.')
        return email

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
class RegistroPerfilForm(forms.ModelForm):
    rut = forms.CharField(
        label='RUT',
        max_length=12,
        validators=[
            RegexValidator(
                regex=r'^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$',
                message='Formato inválido. Ej: 12.345.678-5'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12.345.678-5',
            'required': True,
        }),
        error_messages={'required': 'El RUT es obligatorio.'},
    )
    nombre_empresa = forms.CharField(
        label='Nombre de la empresa',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mi Empresa Ltda.',
            'required': True,
        }),
        error_messages={'required': 'El nombre de la empresa es obligatorio.'},
    )

    class Meta:
        model = Perfil
        fields = ['rut', 'nombre_empresa']

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        # (Opcional) validación de dígito verificador:
        num, dv = rut.split('-')
        num = num.replace('.','')
        # aquí podrías implementar el algoritmo del DV
        # si falla, raise ValidationError('DV no corresponde')
        return rut

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