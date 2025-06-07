#!/usr/bin/env python
"""
core/zpoblar.py

Script para poblar las tablas Pregunta y OpcionPregunta
a partir de un CSV de “Preguntas-Respuestas-Posibilidades”.

Este CSV tiene las columnas:
    'texto_concatenado', 'dimensión', 'criterio',
    'n_pregunta', 'pregunta', 'respuesta',
    'nivel de madurez_concepto', 'nivel de madurez_valor'

Para ejecutarlo:
    python core/zpoblar.py
"""

import os
import django
import pandas as pd
import traceback
from django.contrib.auth.models import User
from django.db import transaction
from core.models import Pregunta, OpcionPregunta, Encuesta, Respuesta

# -------------------------------------------------------------------
# 1) CONFIGURACIÓN DE DJANGO
# -------------------------------------------------------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyectoGob.settings')
django.setup()

# -------------------------------------------------------------------
# 2) RUTAS Y CONSTANTES
# -------------------------------------------------------------------

# Ajusta esta ruta si el CSV está en otra carpeta o con otro nombre
CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    'Preguntas-respuestas-posibilidades(Hoja2).csv'
)

# Usuario al que asignar respuestas por defecto (si lo deseas)
DEFAULT_USERNAME = 'super123'

# Límite de transacciones “en batch” para no saturar la BD (opcional)
BATCH_SIZE = 50  # como cada fila crea OpcionPregunta, aumentamos el batch


# -------------------------------------------------------------------
# 3) FUNCIONES AUXILIARES PARA “LIMPIAR” TABLAS
# -------------------------------------------------------------------

def eliminar_tablas():
    """
    Elimina todos los registros de Respuesta, Encuesta, OpcionPregunta y Pregunta.
    Úsalo con cuidado (solo en desarrollo si quieres reiniciar todo).
    """
    print('> Eliminando respuestas existentes...')
    Respuesta.objects.all().delete()

    print('> Eliminando encuestas existentes...')
    Encuesta.objects.all().delete()

    print('> Eliminando opciones de pregunta existentes...')
    OpcionPregunta.objects.all().delete()

    print('> Eliminando preguntas existentes...')
    Pregunta.objects.all().delete()


# -------------------------------------------------------------------
# 4) LECTURA DEL CSV Y CREACIÓN DE Pregunta + OpcionPregunta
# -------------------------------------------------------------------

def crear_preguntas_y_opciones():
    """
    Lee el CSV con Preguntas y sus posibles respuestas, y llena
    las tablas Pregunta y OpcionPregunta. Este CSV tiene columnas:

        'n_pregunta'                → código de la pregunta (entero)
        'dimensión'                 → dimensión (texto)
        'criterio'                  → criterio (texto)
        'pregunta'                  → texto completo de la pregunta
        'respuesta'                 → texto de cada opción
        'nivel de madurez_valor'    → puntaje asociado a la opción

    El script agrupa las filas por 'n_pregunta' para crear una sola
    entrada en Pregunta, y luego para cada fila crea una OpcionPregunta.
    """

    print(f"> Leyendo CSV desde: {CSV_PATH} ...")
    try:
        # Intentamos leer con encoding latin-1 y separador ';'
        df = pd.read_csv(CSV_PATH, sep=';', encoding='latin-1')
    except Exception as e_latin:
        print("ERROR al intentar leer el CSV con encoding='latin-1':")
        traceback.print_exc()
        print("\nSe intenta de nuevo con UTF-8 + engine='python' ...")
        try:
            df = pd.read_csv(CSV_PATH, sep=';', encoding='utf-8', engine='python')
        except Exception as e_utf8:
            print("ERROR al intentar leer el CSV con encoding='utf-8' + engine='python':")
            traceback.print_exc()
            print("=== No se pudo leer el CSV. Abortando creación de preguntas. ===")
            return

    # Columnas que realmente trae tu CSV
    columnas = list(df.columns)
    columnas_requeridas = ['n_pregunta', 'dimensión', 'criterio', 'pregunta', 'respuesta', 'nivel de madurez_valor']
    faltantes = [col for col in columnas_requeridas if col not in columnas]
    if faltantes:
        print("ERROR: El CSV no contiene las columnas obligatorias:")
        print(f"       {faltantes}")
        print(f" Columnas encontradas: {columnas}")
        return

    # Renombramos columnas para trabajar con nombres “sin tilde” ni espacios
    df = df.rename(columns={
        'n_pregunta': 'codigo',
        'dimensión': 'dimension',
        'pregunta': 'texto',
        'respuesta': 'opcion_texto',
        'nivel de madurez_valor': 'puntaje'
    })

    total_filas = len(df)
    print(f"> Filas en el CSV: {total_filas}")

    creadas_preguntas = 0
    creadas_opciones = 0

    # Vamos a llevar un contador de “orden de opción” por cada pregunta
    # { codigo_pregunta: siguiente_orden_disponible }
    orden_por_pregunta = {}

    # Iniciamos una transacción general para mejorar performance
    with transaction.atomic():
        for idx, row in df.iterrows():
            fila_num = idx + 1
            try:
                # 1) Obtenemos el código de pregunta y otros campos básicos
                codigo_raw = row['codigo']
                try:
                    codigo = int(codigo_raw)
                except:
                    raise ValueError(
                        f"Columna 'codigo' en fila {fila_num} no es numérico: '{codigo_raw}'"
                    )

                dimension = str(row['dimension']).strip()
                criterio  = str(row['criterio']).strip()
                texto     = str(row['texto']).strip()

                # 2) Creamos o actualizamos la Pregunta (una sola vez por código)
                pregunta_obj, created_preg = Pregunta.objects.update_or_create(
                    codigo=codigo,
                    defaults={
                        'dimension': dimension,
                        'criterio':  criterio,
                        'texto':     texto
                    }
                )
                if created_preg:
                    creadas_preguntas += 1
                    print(f"  [PREGUNTA CREADA] fila {fila_num} → código={pregunta_obj.codigo}")
                    # Inicializamos contador de orden para esta pregunta
                    orden_por_pregunta[codigo] = 1
                else:
                    # Si no se creó, nos aseguramos de tener inicializado su orden
                    if codigo not in orden_por_pregunta:
                        # Por defecto, empezamos en 1
                        orden_por_pregunta[codigo] = 1

                # 3) Procesamos la opción: cada fila del CSV es una opción distinta
                opcion_texto = str(row['opcion_texto']).strip()
                puntaje_raw  = row['puntaje']

                if opcion_texto and pd.notna(puntaje_raw):
                    try:
                        puntaje = float(puntaje_raw)
                    except:
                        raise ValueError(
                            f"Fila {fila_num}, columna 'puntaje' no es numérico: '{puntaje_raw}'"
                        )

                    # Tomamos el orden asignado (incremental)
                    orden_actual = orden_por_pregunta[codigo]

                    # Creamos o actualizamos la OpcionPregunta asociada a esta Pregunta
                    opc_obj, created_opc = OpcionPregunta.objects.update_or_create(
                        pregunta=pregunta_obj,
                        texto=opcion_texto,
                        defaults={
                            'puntaje': puntaje,
                            'orden':   orden_actual
                        }
                    )
                    if created_opc:
                        creadas_opciones += 1
                        print(f"    [OPCIÓN CREADA] fila {fila_num} → '{opcion_texto}' (puntaje={puntaje})")
                    else:
                        # Si existe una opción con mismo texto para esa pregunta, lo sobreescribimos puntaje y orden
                        opc_obj.puntaje = puntaje
                        opc_obj.orden = orden_actual
                        opc_obj.save()

                    # Incrementamos el contador de orden para la próxima opción de esta misma pregunta
                    orden_por_pregunta[codigo] += 1
                else:
                    # Si la columna "respuesta" viene vacía o el puntaje es NaN, ignoramos esa fila
                    print(f"    [OMITIDA] fila {fila_num}: opción vacía o puntaje inválido.")
                    continue

                # 4) Guardado parcial cada BATCH_SIZE filas, para no saturar la BD
                if (fila_num % BATCH_SIZE) == 0:
                    print(f">>> Guardado parcial: fila {fila_num} de {total_filas} completada.")

            except Exception as e_fila:
                print(f"\nERROR procesando fila {fila_num}: {e_fila}")
                traceback.print_exc()
                print(f"→ Se omite la fila {fila_num} y se continúa con la siguiente.\n")
                continue  # seguimos con la siguiente fila

    print(f"\n> Total de preguntas creadas: {creadas_preguntas}")
    print(f"> Total de opciones creadas:   {creadas_opciones}")


# -------------------------------------------------------------------
# 5) ASIGNAR RESPUESTAS “POR DEFECTO” A UN USUARIO
# -------------------------------------------------------------------

def asignar_respuestas_por_defecto(username=DEFAULT_USERNAME, valor_por_defecto='si'):
    """
    Si necesitas que, tras poblar las preguntas y opciones, exista
    una Encuesta “vacía” con respuestas por defecto (p.ej. todas 'si'),
    úsalo. Crea una nueva Encuesta para el usuario dado y asigna
    a cada Pregunta su Respuesta con “valor_por_defecto”.
    """
    try:
        usuario = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"ERROR: Usuario '{username}' no existe. No se asignarán respuestas por defecto.")
        return

    encuesta = Encuesta.objects.create(usuario=usuario)
    asignadas = 0

    for pregunta in Pregunta.objects.all():
        # Para preguntas “clásicas” sin opciones, asumimos el campo 'valor' en Respuesta
        # Si tu modelo cambió y ya no usas campo 'valor', adapta esto:
        Respuesta.objects.create(
            encuesta=encuesta,
            pregunta=pregunta,
            valor=valor_por_defecto
        )
        asignadas += 1

    print(f"> Respuestas '{valor_por_defecto}' asignadas a '{username}' en encuesta {encuesta.id}: {asignadas}")


# -------------------------------------------------------------------
# 6) FLUJO PRINCIPAL DE POBLADO
# -------------------------------------------------------------------

def poblar_bd():
    print("=== Iniciando poblamiento de Pregunta y OpcionPregunta desde CSV ===")
    eliminar_tablas()
    crear_preguntas_y_opciones()

    # Si deseas asignar respuestas por defecto, descomenta la línea siguiente:
    # asignar_respuestas_por_defecto()

    print(">>> Proceso de poblamiento completado.")


# -------------------------------------------------------------------
# 7) CUERPO PRINCIPAL
# ----------------------------------------------
