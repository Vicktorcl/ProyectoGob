from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from core.templatetags.custom_filters import formatear_dinero
from django.db import models
from django.db.models import Min
from django.db import connection


class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(
        max_length=15,
        verbose_name='RUT'
    )

    class Meta:
        db_table = 'Perfil'
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuarios'
        ordering = ['usuario__username']

    def __str__(self):
        return f'{self.usuario.first_name} {self.usuario.last_name} (ID {self.id})'

    def acciones(self):
        return {
            'accion_eliminar': 'eliminar el Perfil',
            'accion_actualizar': 'actualizar el Perfil'
        }