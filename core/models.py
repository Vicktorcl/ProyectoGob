from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from core.templatetags.custom_filters import formatear_dinero
from django.db import models
from django.db.models import Min
from django.db import connection


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
        
class Pregunta(models.Model):
    dimension = models.CharField(max_length=100)
    criterio = models.CharField(max_length=100)
    texto = models.TextField()

    def __str__(self):
        return f"{self.dimension} - {self.criterio}: {self.texto[:50]}..."

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
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    valor = models.CharField(max_length=2, choices=VALORES)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'pregunta')
        verbose_name = 'Respuesta'
        verbose_name_plural = 'Respuestas'

    def __str__(self):
        return f"{self.usuario.username} - {self.pregunta.id}: {self.valor}"
