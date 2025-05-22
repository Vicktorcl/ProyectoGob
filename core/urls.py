from django.urls import path
from .views import (
    inicio, registro, nosotros, ingresar, salir, misdatos,
    mipassword, cambiar_password,
    formulario_gobernanza, guardar_gobernanza,
    mantenedor_usuarios, mantenedor_preguntas,
    poblar_bd_view,
    seleccionar_encuesta, respuestas_view, mantenedor_respuestas,
)

urlpatterns = [
    # Públicas
    path('', inicio, name='inicio'),
    path('inicio/', inicio, name='inicio'),
    path('registro/', registro, name='registro'),
    path('nosotros/', nosotros, name='nosotros'),
    path('ingresar/', ingresar, name='ingresar'),

    # Autenticadas
    path('salir/', salir, name='salir'),
    path('misdatos/', misdatos, name='misdatos'),
    path('mipassword/', mipassword, name='mipassword'),
    path('cambiar_password/', cambiar_password, name='cambiar_password'),

    # Mantenedores
    path('mantenedor_usuarios/<str:accion>/<int:id>/', mantenedor_usuarios, name='mantenedor_usuarios'),
    path('mantenedor_preguntas/<str:accion>/<int:id>/', mantenedor_preguntas, name='mantenedor_preguntas'),
    # Mantenedor de respuestas: listar sin params, o con accion e id
    path('mantenedor_respuestas/', mantenedor_respuestas, name='mantenedor_respuestas'),
    path('mantenedor_respuestas/<str:accion>/<int:id>/', mantenedor_respuestas, name='mantenedor_respuestas'),

    # Formulario de gobernanza
    path('gobernanza/', formulario_gobernanza, name='formulario_gobernanza'),
    path('gobernanza/guardar/', guardar_gobernanza, name='guardar_gobernanza'),

    # Selección y vista de respuestas
    path('respuestas/seleccionar/', seleccionar_encuesta, name='seleccionar_encuesta'),
    path('respuestas/seleccionar/<int:user_id>/', seleccionar_encuesta, name='seleccionar_encuesta'),
    path('respuestas/', respuestas_view, name='respuestas'),

    # Poblado de BD (superuser)
    path('poblar_bd/', poblar_bd_view, name='poblar_bd'),
]
