from django.urls import path
from .views import (
    inicio, registro, nosotros, ingresar, salir, misdatos,
    mipassword, cambiar_password,
    formulario_gobernanza, guardar_gobernanza,
    mantenedor_usuarios, mantenedor_preguntas,
    poblar_bd_view, respuestas_view, mantenedor_respuestas
)

urlpatterns = [
    path('', inicio, name='inicio'),
    path('inicio', inicio, name='inicio'),
    path('registro', registro, name='registro'),
    path('nosotros', nosotros, name='nosotros'),
    
    path('ingresar', ingresar, name='ingresar'),
    path('salir', salir, name='salir'),
    path('misdatos', misdatos, name='misdatos'),
    path('mipassword', mipassword, name='mipassword'),
    path('cambiar_password', cambiar_password, name='cambiar_password'),
    path('mantenedor_respuestas', mantenedor_respuestas, name='mantenedor_respuestas'),
    path('mantenedor_usuarios/<accion>/<id>', mantenedor_usuarios, name='mantenedor_usuarios'),
    path('mantenedor_preguntas/<accion>/<id>', mantenedor_preguntas, name='mantenedor_preguntas'),
    path('mantenedor_respuestas/<accion>/<int:id>', mantenedor_respuestas, name='mantenedor_respuestas'),
    path('respuestas/<int:user_id>/', respuestas_view, name='respuestas_usuario'),
    path('respuestas/<int:user_id>/<slug:fecha>/', respuestas_view, name='respuestas_usuario_fecha'),
    path('gobernanza', formulario_gobernanza, name='formulario_gobernanza'),
    path('gobernanza/guardar', guardar_gobernanza, name='guardar_gobernanza'),
    path('respuestas', respuestas_view, name='respuestas'),
    # Ruta para poblar la base de datos (solo superusuarios activos)
    path('poblar_bd', poblar_bd_view, name='poblar_bd'),
]
