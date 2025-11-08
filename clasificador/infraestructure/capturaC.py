# captura_en_vivo.py
import cv2
import sys
import os
import django
from clasificador.domain.color_analizer import ColorAnalyzer
from clasificador.models import Planta
from datetime import datetime



def capturar_y_analizar():
    # Inicializar cámara
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: No se pudo acceder a la cámara")
        return

    analyzer = ColorAnalyzer()
    print("Presiona 'c' para capturar y analizar")
    print("Presiona 's' para guardar datos en la base de datos")
    print("Presiona 'q' para salir")

    ultimo_analisis = None

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error al leer el frame")
            break

        # Analizar el frame actual
        porcentajes = analyzer.detectar_colores_frame(frame)

        if porcentajes:
            # Evaluar estado
            estado, descripcion = analyzer.evaluar_estado_salud(porcentajes)

            # Dibujar información en el frame
            frame_con_info = analyzer.dibujar_info_frame(
                frame.copy(),
                porcentajes,
                estado,
                descripcion
            )

            # Guardar el último análisis
            ultimo_analisis = {
                'porcentajes': porcentajes,
                'estado': estado,
                'descripcion': descripcion,
                'frame': frame.copy()
            }

            # Mostrar el frame
            cv2.imshow('Analisis de Planta en Vivo', frame_con_info)

        # Capturar teclas
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('c') and ultimo_analisis:
            # Mostrar análisis detallado
            print("\n=== ANALISIS CAPTURADO ===")
            print(f"Verde: {ultimo_analisis['porcentajes']['verde']}%")
            print(f"Amarillo: {ultimo_analisis['porcentajes']['amarillo']}%")
            print(f"Marrón: {ultimo_analisis['porcentajes']['marron']}%")
            print(f"Rojo: {ultimo_analisis['porcentajes']['rojo']}%")
            print(f"Estado: {ultimo_analisis['descripcion']}")
            print("========================\n")
        elif key == ord('s') and ultimo_analisis:
            # Guardar en base de datos
            guardar_analisis(ultimo_analisis)

    cap.release()
    cv2.destroyAllWindows()


def guardar_analisis(analisis):
    """
    Guarda el análisis en la base de datos
    """
    try:
        # Puedes modificar esto para seleccionar una planta específica
        planta_id = input("Ingresa el ID de la planta a actualizar: ")
        planta = Planta.objects.get(id=planta_id)

        # Guardar imagen capturada (opcional)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        imagen_path = f"media/plantas/captura_{timestamp}.jpg"
        cv2.imwrite(imagen_path, analisis['frame'])

        # Actualizar planta
        planta.porcentaje_verde = analisis['porcentajes']['verde']
        planta.porcentaje_amarillo = analisis['porcentajes']['amarillo']
        planta.porcentaje_marron = analisis['porcentajes']['marron']
        planta.porcentaje_rojo = analisis['porcentajes']['rojo']
        planta.Estado = analisis['estado']
        planta.Descripcion = analisis['descripcion']
        planta.ImagenURL = imagen_path
        planta.save()

        print(f"✓ Datos guardados para la planta: {planta.nombre}")
    except Planta.DoesNotExist:
        print("✗ Planta no encontrada")
    except Exception as e:
        print(f"✗ Error al guardar: {e}")


if __name__ == "__main__":
    capturar_y_analizar()