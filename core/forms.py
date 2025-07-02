from django import forms
from django.forms.models import inlineformset_factory
from django.forms import ModelForm, Form
from django.core.validators import RegexValidator, MinValueValidator
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
    codigo = forms.CharField(
        label='Código',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1.1.1',
        }),
        error_messages={'required': 'El código es obligatorio.'},
    )
    grupo = forms.CharField(
        label='Grupo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: G1 Principios',
        }),
        error_messages={'required': 'El grupo es obligatorio.'},
    )
    categoria = forms.CharField(
        label='Categoría',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: C1.1 Principios',
        }),
        error_messages={'required': 'La categoría es obligatoria.'},
    )
    area = forms.CharField(
        label='Área',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Principios relacionados con los datos',
        }),
        error_messages={'required': 'El área es obligatoria.'},
    )
    texto = forms.CharField(
        label='Texto de la pregunta',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Escribe el enunciado aquí',
        }),
        error_messages={'required': 'El texto es obligatorio.'},
    )
    peso_area = forms.DecimalField(
        label='Peso del área',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Ej: 2,00',
        }),
        error_messages={'required': 'El peso del área es obligatorio.'},
        min_value=0,
        max_digits=5,
        decimal_places=2,
    )
    nivel = forms.ChoiceField(
        label='Nivel de madurez',
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        choices=PreguntaGD.NIVEL_CHOICES,
        error_messages={'required': 'Selecciona un nivel.'},
    )

    class Meta:
        model = PreguntaGD
        fields = ['codigo', 'grupo', 'categoria', 'area', 'texto', 'peso_area', 'nivel']

    def clean(self):
        """
        Validación cruzada: podrías, por ejemplo, asegurar que peso_area
        sea coherente con otras áreas de la misma categoría.
        """
        cleaned = super().clean()
        # ejemplo hipotético:
        # if cleaned.get('peso_area') > 100:
        #     self.add_error('peso_area', 'El peso no puede superar 100.')
        return cleaned

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
    dimension = forms.CharField(
        label='Dimensión',
        required=True,
        error_messages={'required': 'La dimensión es obligatoria.'},
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Procesos',
            'required': True,
        })
    )
    criterio = forms.CharField(
        label='Criterio',
        required=True,
        error_messages={'required': 'El criterio es obligatorio.'},
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Nivel de control',
            'required': True,
        })
    )
    texto = forms.CharField(
        label='Texto de la pregunta',
        required=True,
        error_messages={'required': 'El texto de la pregunta es obligatorio.'},
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Escribe el enunciado de la pregunta',
            'required': True,
        })
    )

    class Meta:
        model = Pregunta
        fields = ['dimension', 'criterio', 'texto']


class OpcionPreguntaForm(ModelForm):
    texto = forms.CharField(
        label='Texto de la opción',
        required=True,
        error_messages={'required': 'El texto de la opción es obligatorio.'},
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Sí, No, Parcial',
            'required': True,
        })
    )
    puntaje = forms.DecimalField(
        label='Puntaje',
        required=True,
        min_value=0,
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        error_messages={
            'required':   'El puntaje es obligatorio.',
            'invalid':    'Ingrese un puntaje válido.',
            'min_value':  'El puntaje no puede ser negativo.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'required': True,
        })
    )
    orden = forms.IntegerField(
        label='Orden',
        required=True,
        min_value=1,
        error_messages={
            'required':   'El orden es obligatorio.',
            'invalid':    'Ingrese un número entero válido.',
            'min_value':  'El orden debe ser al menos 1.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'required': True,
        })
    )

    class Meta:
        model = OpcionPregunta
        fields = ['texto', 'puntaje', 'orden']


# Inline formset sin cambios estructurales
OpcionFormSet = inlineformset_factory(
    Pregunta, OpcionPregunta,
    fields=('texto', 'puntaje'),  # <- elimina 'orden' de aquí
    extra=1, can_delete=True
)

# ————————————————
# Form para Opciones de Pregunta
# ————————————————


# Inline formset para ligar Opciones a la Pregunta


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
            'placeholder': '12.345.678-6',
        })
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
        # opcional: comprueba dígito verificador
        num, dv = rut.split('-')
        num = num.replace('.', '')
        # aquí podrías llamar a tu función de validación de DV
        # if not valida_dv(num, dv): raise ValidationError('DV no corresponde')
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
class PerfilForm(forms.ModelForm):
    rut = forms.CharField(
        label='RUT',
        max_length=12,
        validators=[RegexValidator(
            regex=r'^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$',
            message='Formato inválido. Ej: 12.345.678-6'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12.345.678-6',
        })
    )
    nombre_empresa = forms.CharField(
        label='Nombre de la empresa',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mi Empresa Ltda.',
        }),
        error_messages={'required': 'El nombre de la empresa es obligatorio.'},
    )

    class Meta:
        model = Perfil
        fields = ['rut', 'nombre_empresa']

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        # opcional: comprueba dígito verificador
        num, dv = rut.split('-')
        num = num.replace('.', '')
        # aquí podrías llamar a tu función de validación de DV
        # if not valida_dv(num, dv): raise ValidationError('DV no corresponde')
        return rut


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