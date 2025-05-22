from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from core.templatetags.custom_filters import formatear_dinero
from django.db import models
from django.db.models import Sum, Case, When, Value, IntegerField

class Perfil(models.Model):
    # Relación uno a uno con el modelo User
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Datos de la empresa
    rut = models.CharField(max_length=15, verbose_name='Rut de la empresa', unique=True)
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
        Calcula el porcentaje de madurez (0–100) para una dimensión dada,
        tomando la última encuesta del usuario.
        """
        from core.models import Respuesta, Pregunta, Encuesta
        ultima = Encuesta.objects.filter(usuario=self.usuario).order_by('-fecha').first()
        if not ultima:
            return 0
        qs = Respuesta.objects.filter(
            encuesta=ultima,
            pregunta__dimension=dimension
        )
        total = qs.aggregate(
            total=Sum(
                Case(
                    When(valor='si', then=Value(6)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        )['total'] or 0
        max_score = qs.count() * 6
        return (total / max_score * 100) if max_score else 0

    def get_all_dimension_scores(self):
        """
        Retorna un dict {dimension: porcentaje} para la última encuesta.
        """
        from core.models import Pregunta
        dims = Pregunta.objects.values_list('dimension', flat=True).distinct()
        return {dim: self.get_dimension_score(dim) for dim in dims}

    def get_global_score(self):
        """
        Calcula el puntaje global (0–100) promediando todas las dimensiones
        de la última encuesta.
        """
        scores = list(self.get_all_dimension_scores().values())
        return sum(scores) / len(scores) if scores else 0


class Encuesta(models.Model):
    """
    Representa una ejecución de la encuesta por parte de un usuario.
    Se genera una nueva instancia por cada envío del formulario.
    """
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL,
        null=True,
        blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Encuesta'
        verbose_name_plural = 'Encuestas'
        ordering = ['-fecha']

    def __str__(self):
        return f'Encuesta #{self.id} - {self.usuario.username} ({self.fecha:%Y-%m-%d %H:%M})'


class Pregunta(models.Model):
    # ID de negocio (no confundir con el pk de Django)
    codigo = models.IntegerField(unique=True, verbose_name='id de pregunta')
    dimension = models.CharField(max_length=100)
    criterio  = models.CharField(max_length=100)
    texto     = models.TextField()

    def __str__(self):
        return f"{self.codigo} – {self.dimension} – {self.criterio}: {self.texto[:50]}…"

    @staticmethod
    def acciones():
        return {
            'accion_eliminar': 'eliminar la pregunta',
            'accion_crear': 'crear una nueva pregunta',
            'accion_editar': 'editar la pregunta'
        }


class Respuesta(models.Model):
    VALORES = [
        ('si', 'Sí'),
        ('no', 'No'),
    ]
    encuesta = models.ForeignKey(
        Encuesta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respuestas'
    )
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    valor = models.CharField(max_length=2, choices=VALORES)

    class Meta:
        unique_together = ('encuesta', 'pregunta')
        verbose_name = 'Respuesta'
        verbose_name_plural = 'Respuestas'

    def __str__(self):
        user = self.encuesta.usuario.username if self.encuesta else 'N/A'
        enc = f'Encuesta {self.encuesta.id}' if self.encuesta else ''
        return f"{user} - {enc} - Pregunta {self.pregunta.codigo}: {self.valor}"
