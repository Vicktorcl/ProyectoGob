from django.urls import path
from .views import (
    inicio, registro, nosotros, ingresar, salir, misdatos,
    mipassword, cambiar_password,
    formulario_gobernanza, guardar_gobernanza,
    mantenedor_usuarios, mantenedor_preguntas
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
    
    path('mantenedor_usuarios/<accion>/<id>', mantenedor_usuarios, name='mantenedor_usuarios'),
    path('mantenedor_preguntas/<accion>/<id>', mantenedor_preguntas, name='mantenedor_preguntas'),
    
    path('gobernanza/', formulario_gobernanza, name='formulario_gobernanza'),
    path('gobernanza/guardar/', guardar_gobernanza, name='guardar_gobernanza')
]
