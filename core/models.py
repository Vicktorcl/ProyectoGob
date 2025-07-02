from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, Case, When, Value, IntegerField, Max
from core.templatetags.custom_filters import formatear_dinero

# ------------------------------------------------------------------
# Perfil (sin cambios estructurales, pero usando OpcionPregunta)
# ------------------------------------------------------------------
class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=15, verbose_name='Rut de la empresa', blank=True, null=True)
    nombre_empresa = models.CharField(max_length=100, verbose_name='Nombre de la empresa', unique=True)

    class Meta:
        db_table = 'Perfil'
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuarios'
        ordering = ['usuario__username']

    def __str__(self):
        return f'{self.nombre_empresa} - {self.rut}'

    def acciones(self):
        return {
            'accion_eliminar': 'eliminar el Perfil',
            'accion_actualizar': 'actualizar el Perfil'
        }

    def get_dimension_score(self, dimension):
        """
        Calcula el porcentaje de madurez (0–100) para una dimensión,
        tomando la última encuesta del usuario y sumando los puntajes de las opciones.
        """
        from core.models import Encuesta, Respuesta, OpcionPregunta
        ultima = Encuesta.objects.filter(usuario=self.usuario).order_by('-fecha').first()
        if not ultima:
            return 0

        # Sumamos los puntajes elegidos
        qs = Respuesta.objects.filter(
            encuesta=ultima,
            pregunta__dimension=dimension
        ).select_related('opcion')
        total = qs.aggregate(total=Sum('opcion__puntaje'))['total'] or 0

        # Calculamos el máximo posible en esa dimensión
        preguntas_en_dim = ultima.respuestas.filter(pregunta__dimension=dimension).count()
        max_por_pregunta = OpcionPregunta.objects.filter(
            pregunta__dimension=dimension
        ).aggregate(max_puntaje=Max('puntaje'))['max_puntaje'] or 0
        max_score = preguntas_en_dim * max_por_pregunta

        return (total / max_score * 100) if max_score else 0

    def get_all_dimension_scores(self):
        from core.models import Pregunta
        dims = Pregunta.objects.values_list('dimension', flat=True).distinct()
        return {dim: self.get_dimension_score(dim) for dim in dims}

    def get_global_score(self):
        scores = list(self.get_all_dimension_scores().values())
        return sum(scores) / len(scores) if scores else 0


# ------------------------------------------------------------------
# Encuesta Clásica
# ------------------------------------------------------------------
class Encuesta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Encuesta'
        verbose_name_plural = 'Encuestas'
        ordering = ['-fecha']

    def __str__(self):
        return f'Encuesta #{self.id} - {self.usuario.username} ({self.fecha:%Y-%m-%d %H:%M})'


class Pregunta(models.Model):
    codigo = models.AutoField(primary_key=True, verbose_name='id de pregunta')
    dimension = models.CharField(max_length=100)
    criterio = models.CharField(max_length=100)
    texto = models.TextField()

    class Meta:
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'
        ordering = ['dimension', 'codigo']

    def __str__(self):
        return f"{self.codigo} – {self.dimension} – {self.criterio}: {self.texto[:50]}…"


class OpcionPregunta(models.Model):
    """
    Cada pregunta clásica puede tener N opciones con distinto puntaje.
    """
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='opciones')
    texto = models.CharField(max_length=200, verbose_name='Texto de la opción')
    puntaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Puntaje de la opción',
        help_text='Peso/puntaje que aporta esta opción al total.'
    )
    orden = models.PositiveIntegerField(default=0, help_text='Orden en que aparece la opción')

    class Meta:
        verbose_name = 'Opción de Pregunta'
        verbose_name_plural = 'Opciones de Preguntas'
        ordering = ['pregunta__dimension', 'pregunta__codigo', 'orden']

    def __str__(self):
        return f"{self.pregunta.codigo} – {self.texto} ({self.puntaje})"


class Respuesta(models.Model):
    """
    Guarda la respuesta de un usuario a una Pregunta clásica,
    apuntando a la opción elegida.
    """
    encuesta = models.ForeignKey(
        Encuesta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respuestas'
    )
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    opcion = models.ForeignKey(OpcionPregunta, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('encuesta', 'pregunta')
        verbose_name = 'Respuesta'
        verbose_name_plural = 'Respuestas'

    def __str__(self):
        user = self.encuesta.usuario.username if self.encuesta else 'N/A'
        return f"{user} – Pregunta {self.pregunta.codigo}: {self.opcion.texto}"


# ------------------------------------------------------------------
# Encuesta Modelo GD (sin cambios)
# ------------------------------------------------------------------
class PreguntaGD(models.Model):
    NIVEL_CHOICES = [
        (1, 'Inicial'),
        (2, 'Gestionado'),
        (3, 'Definido'),
        (4, 'Medido'),
        (5, 'Optimizado'),
    ]
    codigo = models.CharField(max_length=10)
    grupo = models.CharField(max_length=200)
    categoria = models.CharField(max_length=200)
    area = models.CharField(max_length=200, help_text="Ej. AP2.3.1")
    numero = models.PositiveIntegerField(help_text="Número de afirmación en el área")
    texto = models.TextField()
    peso_area = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Peso del área (suma 100 por categoría)"
    )
    nivel = models.PositiveSmallIntegerField(max_length=20, choices=NIVEL_CHOICES)

    class Meta:
        verbose_name = 'Pregunta GD'
        verbose_name_plural = 'Preguntas GD'
        ordering = ['grupo', 'categoria', 'area', 'numero']

    def __str__(self):
        return f"{self.codigo} – {self.grupo}.{self.categoria}.{self.area} – Nivel {self.get_nivel_display()}"


class EncuestaGD(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Encuesta GD'
        verbose_name_plural = 'Encuestas GD'
        ordering = ['-fecha']

    def __str__(self):
        return f'EncuestaGD #{self.id} – {self.usuario.username} ({self.fecha:%Y-%m-%d})'


class RespuestaGD(models.Model):
    VALORACION = [
        (1, 'No cumple'),
        (2, 'Consciente'),
        (3, 'Implantando'),
        (4, 'Operativo'),
    ]
    encuesta = models.ForeignKey(EncuestaGD, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(PreguntaGD, on_delete=models.CASCADE)
    valoracion = models.PositiveSmallIntegerField(choices=VALORACION)

    class Meta:
        unique_together = ('encuesta', 'pregunta')
        verbose_name = 'Respuesta GD'
        verbose_name_plural = 'Respuestas GD'

    def __str__(self):
        return f"{self.encuesta.usuario.username} – {self.pregunta.codigo}: {self.get_valoracion_display()}"
