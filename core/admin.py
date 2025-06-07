from django.contrib import admin
from .models import Perfil, Pregunta, Respuesta, EncuestaGD, PreguntaGD, RespuestaGD, OpcionPregunta

admin.site.register(Perfil)
admin.site.register(Pregunta)
admin.site.register(Respuesta)
admin.site.register(OpcionPregunta)
admin.site.register(PreguntaGD)
admin.site.register(RespuestaGD)
admin.site.register(EncuestaGD)