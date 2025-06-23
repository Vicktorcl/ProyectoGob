# core/urls.py
from django.urls import path

from . import views  # Importamos todo el módulo de vistas
from .views import (
    inicio, registro, nosotros, ingresar, salir, misdatos,
    mipassword, cambiar_password,
    formulario_gobernanza, guardar_gobernanza,
    mantenedor_usuarios, mantenedor_preguntas,
    poblar_bd_view,
    seleccionar_encuesta, respuestas_view, mantenedor_respuestas,
    seleccionar_encuesta_gd, nueva_encuesta_gd, reporte_gd, zpoblar2_view,
    mantenedor_preguntas_gd_gd, mantenedor_respuestas_gd,
)

urlpatterns = [
    # Públicas
    path('', nosotros, name='nosotros'),
    path('inicio/', inicio, name='inicio'),
    path('registro/', registro, name='registro'),
    path('nosotros/', nosotros, name='nosotros'),
    path('ingresar/', ingresar, name='ingresar'),

    # Recuperar contraseña (usando nuestros wrappers en views.py)
    path(
        'password-reset/',
        views.password_reset_request,
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        views.password_reset_done_view,
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        views.password_reset_confirm_view,
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        views.password_reset_complete_view,
        name='password_reset_complete'
    ),

    # Autenticadas
    path('salir/', salir, name='salir'),
    path('misdatos/', misdatos, name='misdatos'),
    path('mipassword/', mipassword, name='mipassword'),
    path('cambiar_password/', cambiar_password, name='cambiar_password'),

    # Mantenedores
    path('mantenedor_usuarios/<str:accion>/<int:id>/', mantenedor_usuarios, name='mantenedor_usuarios'),
    path('mantenedor_preguntas/<str:accion>/<int:id>/', mantenedor_preguntas, name='mantenedor_preguntas'),
    path('mantenedor_respuestas/', mantenedor_respuestas, name='mantenedor_respuestas'),
    path('mantenedor_respuestas/<str:accion>/<int:id>/', mantenedor_respuestas, name='mantenedor_respuestas'),

    # Encuesta Modelo MGDE
    path('gobernanza/', formulario_gobernanza, name='formulario_gobernanza'),
    path('gobernanza/guardar/', guardar_gobernanza, name='guardar_gobernanza'),
    path('respuestas/seleccionar/', seleccionar_encuesta, name='seleccionar_encuesta'),
    path('respuestas/seleccionar/<int:user_id>/', seleccionar_encuesta, name='seleccionar_encuesta'),
    path('respuestas/', respuestas_view, name='respuestas'),

    # Encuesta Modelo 4.0 de Madurez de Datos
    path('gd/seleccionar/', seleccionar_encuesta_gd, name='seleccionar_encuesta_gd'),
    path('gd/nueva/', nueva_encuesta_gd, name='nueva_encuesta_gd'),
    path('gd/reporte/<int:encuesta_id>/', reporte_gd, name='reporte_gd'),
    path('mantenedor_preguntas_gd/', mantenedor_preguntas_gd_gd, name='mantenedor_preguntas_gd'),
    path('mantenedor_preguntas_gd/<str:accion>/<int:id>/', mantenedor_preguntas_gd_gd, name='mantenedor_preguntas_gd'),
    path('mantenedor_respuestas_gd/', mantenedor_respuestas_gd, name='mantenedor_respuestas_gd'),
    path('mantenedor_respuestas_gd/<str:accion>/<int:id>/', mantenedor_respuestas_gd, name='mantenedor_respuestas_gd'),

    # Poblado de BD (superuser)
    path('poblar_bd/', poblar_bd_view, name='poblar_bd'),
    path('zpoblar2/', zpoblar2_view, name='zpoblar2'),
]
