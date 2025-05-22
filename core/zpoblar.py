# core/zpoblar.py
#!/usr/bin/env python
"""
Script para poblar las tablas Pregunta, Encuesta y Respuesta usando el campo 'codigo'.
Ejecuta desde la raíz del proyecto:
    python core/zpoblar.py
"""
import os
import re
import django
from django.contrib.auth.models import User
from core.models import Pregunta, Encuesta, Respuesta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyectoGob.settings')
django.setup()

# Datos embebidos de preguntas (codigo, dimension, criterio, texto completo)
PREGUNTAS_DATA = [
    { 'codigo': 1,  'dimension': 'Visión estratégica',                   'criterio': 'Visión',                             'texto': '01.- ¿Existe un compromiso directivo formal y efectivo con la gestión y gobernanza de datos como elementos que aportan valor público?' },
    { 'codigo': 2,  'dimension': 'Visión estratégica',                   'criterio': 'Estrategia',                         'texto': '02.- ¿Están incluidos los temas de datos en los objetivos e iniciativas estratégicas de la organización?' },
    { 'codigo': 3,  'dimension': 'Visión estratégica',                   'criterio': 'Presupuesto y Recursos',              'texto': '03.- ¿Existe una asignación de presupuestos y recursos para cumplimiento de hoja de ruta o plan de gobernanza? (cuando existe)' },
    { 'codigo': 4,  'dimension': 'Visión estratégica',                   'criterio': 'Capacidades',                        'texto': '04.- ¿Existen actualmente en la institución capacidades para la gestión de datos?' },
    { 'codigo': 5,  'dimension': 'Visión estratégica',                   'criterio': 'Gestión del Cambio',                 'texto': '05.- ¿Existe un plan de gestión del cambio, ya sea específico en torno a la Ley de Transformación Digital o Institucional que aborde los temas de datos?' },
    { 'codigo': 6,  'dimension': 'Visión estratégica',                   'criterio': 'Alianzas y Colaboraciones',          'texto': '06.- ¿Se cuenta con múltiples alianzas o colaboraciones con otros OAE y/o privados en torno a los datos (intercambio de información, análisis de datos, etc.) y se busca activamente ampliarlas?' },
    { 'codigo': 7,  'dimension': 'Visión estratégica',                   'criterio': 'Medición y Seguimiento',              'texto': '07.- ¿Existen métricas claras para evaluar el éxito de la estrategia e implantación del MGDE? ¿Se realizan revisiones periódicas para evaluar el progreso y realizar ajustes si es necesario?' },

    { 'codigo': 8,  'dimension': 'Gobernanza de datos',                  'criterio': 'Política de gobernanza de datos',     'texto': '08.- ¿Existe una política/estrategia de gobernanza de datos que cubra la gestión de los datos a lo largo de su ciclo de vida, desde su creación hasta su eliminación o archivo?' },
    { 'codigo': 9,  'dimension': 'Gobernanza de datos',                  'criterio': 'Organización',                       'texto': '09.- ¿Existen roles o funciones institucionales responsables del liderazgo de datos?' },
    { 'codigo': 10, 'dimension': 'Gobernanza de datos',                  'criterio': 'Implementación',                     'texto': '10.- ¿Existe un plan de implementación de la gobernanza de datos?' },
    { 'codigo': 11, 'dimension': 'Gobernanza de datos',                  'criterio': 'Herramientas',                       'texto': '11.- ¿Se han incorporado herramientas para apoyo a la gobernanza?' },
    { 'codigo': 12, 'dimension': 'Gobernanza de datos',                  'criterio': 'Capacitación',                       'texto': '12.- ¿Se han realizado capacitaciones de gobernanza y gestión de datos en base al MGDE (o DAMA) en la institución?' },
    { 'codigo': 13, 'dimension': 'Gobernanza de datos',                  'criterio': 'Gestión de Riesgos',                 'texto': '13.- ¿Se han identificado y evaluado los riesgos asociados con la gestión de datos y existen procesos para mitigar y gestionar estos riesgos de manera efectiva?' },
    { 'codigo': 14, 'dimension': 'Gobernanza de datos',                  'criterio': 'Gestión ética de datos',             'texto': '14.- ¿Existen políticas, directivas o estándares para promover el uso ético de datos?' },

    { 'codigo': 15, 'dimension': 'Arquitectura, diseño y documentación', 'criterio': 'Arquitectura Institucional de datos','texto': '15.- ¿Existe una conceptualización formalizada de la información relevante para el quehacer institucional?' },
    { 'codigo': 16, 'dimension': 'Arquitectura, diseño y documentación', 'criterio': 'Catálogo',                           'texto': '16.- ¿Existe un levantamiento, catálogo o inventario de los datos que maneja la institución?' },
    { 'codigo': 17, 'dimension': 'Arquitectura, diseño y documentación', 'criterio': 'Catálogo',                           'texto': '17.- ¿Existe evaluación de la calidad de los catálogos o inventarios de datos?' },
    { 'codigo': 18, 'dimension': 'Arquitectura, diseño y documentación', 'criterio': 'Modelos y Documentación',             'texto': '18.- ¿Existen modelos o documentación (diseño, diccionario de datos) de las bases de datos?' },
    { 'codigo': 19, 'dimension': 'Arquitectura, diseño y documentación', 'criterio': 'Metadatos',                          'texto': '19.- ¿Existen directrices y estándares para la definición y gestión de metadatos asociados a datos y documentos?' },
    { 'codigo': 20, 'dimension': 'Arquitectura, diseño y documentación', 'criterio': 'Metadatos',                          'texto': '20.- ¿Existen metadatos asociados a las bases de datos?' },

    { 'codigo': 21, 'dimension': 'Almacenamiento y operación',           'criterio': 'Gestión de la operación y almacenamiento', 'texto': '21.- ¿Se gestiona la operación y el almacenamiento de los datos mediante la administración de las bases, internamente o con apoyo externo?' },

    { 'codigo': 22, 'dimension': 'Seguridad y ciberseguridad de datos',  'criterio': 'Seguridad',                         'texto': '22.- ¿Existen políticas y procedimientos para el cumplimiento de la normativa de seguridad de la información?' },
    { 'codigo': 23, 'dimension': 'Seguridad y ciberseguridad de datos',  'criterio': 'Ciberseguridad',                   'texto': '23.- ¿Existen políticas y procedimientos de ciberseguridad de la información?' },
    { 'codigo': 24, 'dimension': 'Seguridad y ciberseguridad de datos',  'criterio': 'Protección de Datos Personales',    'texto': '24.- ¿Existe un responsable de la protección de datos?' },
    { 'codigo': 25, 'dimension': 'Seguridad y ciberseguridad de datos',  'criterio': 'Protección de Datos Personales',    'texto': '25.- ¿Existen políticas y procedimientos asociados al cumplimiento de la privacidad y protección de datos personales?' },
    { 'codigo': 26, 'dimension': 'Seguridad y ciberseguridad de datos',  'criterio': 'Protección de Datos Personales',    'texto': '26.- ¿Existen directrices para la anonimización de datos cuando es requerido?' },
    { 'codigo': 27, 'dimension': 'Seguridad y ciberseguridad de datos',  'criterio': 'Recuperación ante desastres',       'texto': '27.- ¿Existen mecanismos de respaldo y recuperación, planes de recuperación ante desastres (DRP) o planes de continuidad de negocio (BCP) probados y operativos?' },

    { 'codigo': 28, 'dimension': 'Integración e interoperabilidad',      'criterio': 'Integración',                       'texto': '28.- ¿Existen mecanismos de integración y consolidación de datos mediante herramientas tipo ETL o Ingesta para las bases de datos y/o bases de gestión (Datamart, Datawarehouse, Datalake)?' },
    { 'codigo': 29, 'dimension': 'Integración e interoperabilidad',      'criterio': 'Interoperabilidad',                'texto': '29.- ¿Existen acuerdos de acceso y/o intercambio de datos con terceros, sean estas instituciones del sector público, privado o internacional?' },
    { 'codigo': 30, 'dimension': 'Integración e interoperabilidad',      'criterio': 'Interoperabilidad',                'texto': '30.- ¿Se han identificado los requerimientos de interoperabilidad (tanto de entrada como de salida) y existen mecanismos de interoperabilidad?' },
    { 'codigo': 31, 'dimension': 'Integración e interoperabilidad',      'criterio': 'Interoperabilidad',                'texto': '31.- ¿Se utiliza la Plataforma de Interoperabilidad del Estado para la interoperabilidad con otras instituciones?' },

    { 'codigo': 32, 'dimension': 'Documentos y contenidos',              'criterio': 'Definiciones',                      'texto': '32.- ¿Existe un diagnóstico del estado de la gestión documental y una política de gestión documental?' },
    { 'codigo': 33, 'dimension': 'Documentos y contenidos',              'criterio': 'Metadatos',                         'texto': '33.- ¿Se ha revisado la definición del documento "Metadatos para la Gestión Documental de las Instituciones Públicas" identificando las brechas y generando un plan de cumplimiento?' },
    { 'codigo': 34, 'dimension': 'Documentos y contenidos',              'criterio': 'Expediente Electrónico',            'texto': '34.- ¿Se cuenta con una definición y plan de implementación del expediente electrónico de acuerdo a lo requerido en la Ley 21.180 (Ley de TD)?' },
    { 'codigo': 35, 'dimension': 'Documentos y contenidos',              'criterio': 'Repositorio Documental',            'texto': '35.- ¿Se ha incorporado una herramienta de repositorio documental?' },

    { 'codigo': 36, 'dimension': 'Datos maestros y de referencia',       'criterio': 'Datos referenciales',               'texto': '36.- ¿Existen estandarización de códigos de la información que se comparte entre áreas y/o con externos?' },
    { 'codigo': 37, 'dimension': 'Datos maestros y de referencia',       'criterio': 'Datos maestros',                    'texto': '37.- ¿Existe una identificación de los datos maestros y estos se consolidan y gestionan centralmente?' },
    { 'codigo': 38, 'dimension': 'Datos maestros y de referencia',       'criterio': 'Herramientas',                      'texto': '38.- ¿Se cuenta con desarrollos ad-hoc o herramientas de Master Data Management (MDM) que apoyan la gestión de los datos maestros y referenciales?' },

    { 'codigo': 39, 'dimension': 'Analítica e inteligencia de negocios', 'criterio': 'Toma de decisiones basada en información','texto': '39.- ¿Existe la definición institucional y la práctica de hacer análisis de datos para la gestión y toma de decisiones?' },
    { 'codigo': 40, 'dimension': 'Analítica e inteligencia de negocios', 'criterio': 'Información de gestión',             'texto': '40.- ¿Existen repositorios de gestión de tipo data mart / data warehouse o data lake para la gestión institucional?' },
    { 'codigo': 41, 'dimension': 'Analítica e inteligencia de negocios', 'criterio': 'Herramientas',                      'texto': '41.- ¿Existen herramientas de tipo inteligencia de negocios y otras para hacer analítica o ciencia de datos, incluyendo IA?' },

    { 'codigo': 42, 'dimension': 'Calidad de datos',                     'criterio': 'Definición',                        'texto': '42.- ¿Existe una definición de calidad de datos que permita evaluar y auditar la calidad de datos a nivel institucional?' },
    { 'codigo': 43, 'dimension': 'Calidad de datos',                     'criterio': 'Metodología y Herramientas',        'texto': '43.- ¿Se utilizan metodologías (o estándares) y herramientas para la gestión de calidad?' },

    { 'codigo': 44, 'dimension': 'Datos abiertos',                       'criterio': 'Definiciones',                      'texto': '44.- ¿Existe una estrategia de datos abiertos?' },
    { 'codigo': 45, 'dimension': 'Datos abiertos',                       'criterio': 'Definiciones',                      'texto': '45.- ¿Se ha incorporado institucionalmente la definición de datos abiertos por defecto y los principios de datos abiertos (Open Data Charter)?' },
    { 'codigo': 46, 'dimension': 'Datos abiertos',                       'criterio': 'Publicación',                        'texto': '46.- ¿Se publican datos abiertos de manera regular?' },
    { 'codigo': 47, 'dimension': 'Datos abiertos',                       'criterio': 'Publicación',                        'texto': '47.- ¿Si se publican datos abiertos en qué lugar se publican?' },
    { 'codigo': 48, 'dimension': 'Datos abiertos',                       'criterio': 'Publicación',                        'texto': '48.- ¿Existen las condiciones (recursos) e incentivos para la publicación de datos abiertos?' },
    { 'codigo': 49, 'dimension': 'Datos abiertos',                       'criterio': 'Publicación',                        'texto': '49.- ¿Se incentiva la publicación de datasets de alta contribución según lo estipula la normativa de datos abiertos y estrategia nacional de datos abiertos?' },
    { 'codigo': 50, 'dimension': 'Datos abiertos',                       'criterio': 'Mecanismos de acceso, formato, documentación y condiciones de uso', 'texto': '50.- ¿Con qué mecanismos de acceso, formato, documentación y condiciones de uso se publican los datos abiertos?' },

    { 'codigo': 51, 'dimension': 'Aspectos legales y normativos',        'criterio': 'Participación del área jurídica',   'texto': '51.- ¿Existe participación del área jurídica en la definición y validación de políticas y procedimientos de gobierno de datos para asegurar cumplimiento de las leyes y normativas?' },
    { 'codigo': 52, 'dimension': 'Aspectos legales y normativos',        'criterio': 'Cumplimiento aspectos legales y normativos', 'texto': '52.- ¿Se cumple con las regulaciones y estándares relevantes en cuanto a la gestión y protección de datos personales (PDP) y existen procedimientos para garantizar el cumplimiento frente a cambios legislativos o normativos?' },
]


def eliminar_tablas():
    print('> Eliminando respuestas existentes...')
    Respuesta.objects.all().delete()
    print('> Eliminando preguntas existentes...')
    Pregunta.objects.all().delete()

def crear_preguntas():
    creadas = 0
    for entry in PREGUNTAS_DATA:
        # Limpiar prefijo numérico
        texto = re.sub(r'^\d+\.-\s*', '', entry['texto'])
        pregunta, created = Pregunta.objects.update_or_create(
            codigo=entry['codigo'],
            defaults={
                'dimension': entry['dimension'],
                'criterio': entry['criterio'],
                'texto': texto
            }
        )
        if created:
            creadas += 1
            print(f"  [CREADA] código={pregunta.codigo} | {pregunta.dimension} | {pregunta.criterio}")
    print(f"> Total de preguntas creadas: {creadas}")

def asignar_respuestas(username='super123', valor='si'):
    try:
        usuario = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"ERROR: Usuario '{username}' no existe.")
        return
    # Crear nueva encuesta para este usuario
    encuesta = Encuesta.objects.create(usuario=usuario)
    asignadas = 0
    for pregunta in Pregunta.objects.all():
        _, created = Respuesta.objects.get_or_create(
            encuesta=encuesta,
            pregunta=pregunta,
            defaults={'valor': valor}
        )
        if created:
            asignadas += 1
    print(f"> Respuestas '{valor}' asignadas a '{username}' en encuesta {encuesta.id}: {asignadas}")

def poblar_bd():
    print('Iniciando poblamiento de Pregunta y Respuesta...')
    eliminar_tablas()
    crear_preguntas()
    asignar_respuestas()
    print('Proceso de poblamiento completado.')

if __name__ == '__main__':
    poblar_bd()
