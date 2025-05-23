#!/usr/bin/env python
# core/zpoblar_gd.py

import os
import django
from core.models import PreguntaGD, RespuestaGD, EncuestaGD
from django.contrib.auth.models import User

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyectoGob.settings')
django.setup()

# ------------------------------------------------------------
# Grupo G1 – C1.1 – AP1.1.1 Principios relacionados con los datos
# ------------------------------------------------------------
PREGUNTAS_G1 = [
    # nivel 'inicial'
    {'codigo': 'G1-1', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 1,
     'texto': 'En algunos proyectos se establecen unas directrices o guías sobre las actividades relacionadas con los datos.',
     'nivel': 'inicial'},
    # nivel 'basico'
    {'codigo': 'G1-2', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 2,
     'texto': 'Existe un proceso para la definición de principios, pero no está integrado en la organización y se circunscribe sólo a departamentos aislados.',
     'nivel': 'basico'},
    # nivel 'basico'
    {'codigo': 'G1-3', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 3,
     'texto': 'Este proceso se planifica y ejecuta.',
     'nivel': 'basico'},
    # nivel 'basico'
    {'codigo': 'G1-4', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 4,
     'texto': 'Este proceso emplea personal con los perfiles adecuados.',
     'nivel': 'basico'},
    # nivel 'basico'
    {'codigo': 'G1-5', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 5,
     'texto': 'El proceso tiene asignados los recursos necesarios.',
     'nivel': 'basico'},
    # nivel 'basico'
    {'codigo': 'G1-6', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 6,
     'texto': 'El proceso involucra a las partes interesadas relevantes.',
     'nivel': 'basico'},
    # nivel 'basico'
    {'codigo': 'G1-7', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 7,
     'texto': 'El proceso se monitoriza, se controla y se evalúa para verificar su cumplimiento.',
     'nivel': 'basico'},
    # nivel 'intermedio'
    {'codigo': 'G1-8', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 8,
     'texto': 'El proceso de definición de los Principios pertenece al conjunto de procesos estándar de la empresa.',
     'nivel': 'intermedio'},
    # nivel 'intermedio'
    {'codigo': 'G1-9', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 9,
     'texto': 'Los principios se enfocan hacia una arquitectura centrada en el dato.',
     'nivel': 'intermedio'},
    # nivel 'intermedio'
    {'codigo': 'G1-10', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 10,
     'texto': 'Cada principio está alineado con, y contribuye a soportar, las metas y objetivos de la GD y la gestión de datos.',
     'nivel': 'intermedio'},
    # nivel 'medido'
    {'codigo': 'G1-11', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 11,
     'texto': 'Se han establecido métricas para la monitorización de este proceso.',
     'nivel': 'medido'},
    # nivel 'optimo'
    {'codigo': 'G1-12', 'grupo': 'G1', 'categoria': 'C1.1', 'area': 'AP1.1.1', 'numero': 12,
     'texto': 'Se comprueba que se aplican los principios y su eficacia, se analizan las métricas y se establecen pautas de mejora de los principios y el proceso en sí mismo.',
     'nivel': 'optimo'},
    {'codigo': 'G2-1',  'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 1,
     'texto': 'Se definen órganos de gobierno y actores en proyectos aislados.',
     'nivel': 'inicial'},
    {'codigo': 'G2-2',  'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 2,
     'texto': 'Se establecen órganos de gobierno y actores de la GD mediante un proceso que se circunscribe sólo a áreas específicas de la empresa o unidades de negocio, o proyectos transversales.',
     'nivel': 'basico'},
    {'codigo': 'G2-3',  'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 3,
     'texto': 'Existe un proceso para definir los órganos de gobierno y actores de la GD, integrado en el conjunto de procesos estándar de la empresa.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-4',  'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 4,
     'texto': 'El proceso implica a toda la organización.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-5',  'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 5,
     'texto': 'Se establece una estructura de gobierno de datos en toda la organización y un plan de implementación con respaldo ejecutivo.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-6',  'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 6,
     'texto': 'Los órganos de gobierno y actores se han incluido y documentado en el plan de GD.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-7',  'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 7,
     'texto': 'En la definición de los órganos de gobierno y actores de la GD se ha implicado tanto a la parte de negocio como a la de tecnología.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-8',  'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 8,
     'texto': 'En la definición de los órganos de gobierno y actores de la GD se han tenido en cuenta los distintos niveles de Integración Vertical y Horizontal de la I4.0.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-9',  'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 9,
     'texto': 'Se supervisa y controla la actividad de los órganos de gobierno y actores.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-10', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 10,
     'texto': 'Se utilizan técnicas estadísticas y otras técnicas cuantitativas para evaluar la eficacia de los órganos de gobierno y actores de la GD.',
     'nivel': 'medido'},
    {'codigo': 'G2-11', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 11,
     'texto': 'Se actúa sobre el proceso en consecuencia.',
     'nivel': 'medido'},
    {'codigo': 'G2-12', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 12,
     'texto': 'La organización explora nuevas formas de gobierno y definición de actores de la GD.',
     'nivel': 'medido'},
    {'codigo': 'G2-13', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 13,
     'texto': 'La organización analiza y adopta las mejores prácticas del sector para la definición de la estructura de GD.',
     'nivel': 'optimo'},
    {'codigo': 'G2-14', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.1', 'numero': 14,
     'texto': 'Los procesos relacionados con esta área se analizan, refinan y mejoran constantemente.',
     'nivel': 'optimo'},

    # AP2.2.2 – Modelo organizativo de la GD (nivel 1–10) :contentReference[oaicite:1]{index=1}
    {'codigo': 'G2-15', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 1,
     'texto': 'Se define un modelo organizativo sólo en proyectos aislados.',
     'nivel': 'inicial'},
    {'codigo': 'G2-16', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 2,
     'texto': 'Se establece el modelo de organización con que va a operar la GD mediante un proceso que se circunscribe sólo a áreas específicas de la empresa o unidades de negocio, o proyectos transversales.',
     'nivel': 'basico'},
    {'codigo': 'G2-17', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 3,
     'texto': 'Existe un proceso para definir la estructura organizativa de la GD, integrado en el conjunto de procesos estándar de la empresa.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-18', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 4,
     'texto': 'El proceso implica a toda la organización.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-19', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 5,
     'texto': 'El modelo organizativo se ha documentado y ha sido aprobado por el órgano competente.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-20', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 6,
     'texto': 'Los órganos de gobierno y actores se han incluido y documentado en el plan de GD.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-21', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 7,
     'texto': 'En la definición del modelo organizativo de la GD se ha implicado tanto a la parte de negocio como a la de tecnología.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-22', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 8,
     'texto': 'En la definición del modelo organizativo de la GD se han tenido en cuenta los distintos niveles de Integración Vertical y Horizontal de la I4.0.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-23', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 9,
     'texto': 'Se han firmado contratos con las partes implicadas fuera de la organización para la aplicación del programa de GD.',
     'nivel': 'intermedio'},
    {'codigo': 'G2-24', 'grupo': 'G2', 'categoria': 'C2.2', 'area': 'AP2.2.2', 'numero': 10,
     'texto': 'Se supervisa y controla la implantación del modelo.',
     'nivel': 'medido'},
]



def poblar_gd():
    # Eliminar datos previos
    print("-> Limpiando RespuestasGD y PreguntasGD existentes...")
    RespuestaGD.objects.all().delete()
    PreguntaGD.objects.all().delete()

    # Crear preguntas G1
    for data in PREGUNTAS_G1:
        PreguntaGD.objects.create(
            codigo      = data['codigo'],
            grupo       = data['grupo'],
            categoria   = data['categoria'],
            area        = data['area'],
            numero      = data['numero'],
            texto       = data['texto'],
            peso_area   = 1.0,       # Ajusta si tienes pesos específicos
            nivel       = data['nivel']
        )
    print(f">> {len(PREGUNTAS_G1)} preguntas de G1 creadas.")

if __name__ == '__main__':
    poblar_gd()
