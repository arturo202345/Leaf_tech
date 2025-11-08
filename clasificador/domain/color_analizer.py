# clasificador/domain/color_analyzer.py
import cv2
import numpy as np


class ColorAnalyzer:

    @staticmethod
    def detectar_colores_frame(frame):
        """
        Detecta los colores en un frame de video en tiempo real
        """
        if frame is None:
            return None

        # Convertir a HSV
        imageHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Definir rangos de colores para plantas
        verdeBajo = np.array([36, 25, 25], np.uint8)
        verdeAlto = np.array([86, 255, 255], np.uint8)

        amarilloBajo = np.array([20, 100, 20], np.uint8)
        amarilloAlto = np.array([35, 255, 255], np.uint8)

        marronBajo = np.array([8, 40, 40], np.uint8)
        marronAlto = np.array([20, 255, 200], np.uint8)

        rojoBajo1 = np.array([0, 100, 20], np.uint8)
        rojoAlto1 = np.array([10, 255, 255], np.uint8)
        rojoBajo2 = np.array([175, 100, 20], np.uint8)
        rojoAlto2 = np.array([180, 255, 255], np.uint8)

        # Crear máscaras
        maskVerde = cv2.inRange(imageHSV, verdeBajo, verdeAlto)
        maskAmarillo = cv2.inRange(imageHSV, amarilloBajo, amarilloAlto)
        maskMarron = cv2.inRange(imageHSV, marronBajo, marronAlto)
        maskRojo1 = cv2.inRange(imageHSV, rojoBajo1, rojoAlto1)
        maskRojo2 = cv2.inRange(imageHSV, rojoBajo2, rojoAlto2)
        maskRojo = cv2.add(maskRojo1, maskRojo2)

        # Calcular total de píxeles
        total_pixels = frame.shape[0] * frame.shape[1]

        # Calcular porcentajes
        porcentaje_verde = (cv2.countNonZero(maskVerde) / total_pixels) * 100
        porcentaje_amarillo = (cv2.countNonZero(maskAmarillo) / total_pixels) * 100
        porcentaje_marron = (cv2.countNonZero(maskMarron) / total_pixels) * 100
        porcentaje_rojo = (cv2.countNonZero(maskRojo) / total_pixels) * 100

        return {
            'verde': round(porcentaje_verde, 2),
            'amarillo': round(porcentaje_amarillo, 2),
            'marron': round(porcentaje_marron, 2),
            'rojo': round(porcentaje_rojo, 2),
            'masks': {
                'verde': maskVerde,
                'amarillo': maskAmarillo,
                'marron': maskMarron,
                'rojo': maskRojo
            }
        }

    @staticmethod
    def dibujar_info_frame(frame, porcentajes, estado, descripcion):
        """
        Dibuja la información de análisis en el frame
        """
        height, width = frame.shape[:2]

        # Fondo semi-transparente para el texto
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 200), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

        # Título
        cv2.putText(frame, "Analisis de Color", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Porcentajes con colores
        y_offset = 65
        colores_texto = [
            (f"Verde: {porcentajes['verde']}%", (0, 255, 0)),
            (f"Amarillo: {porcentajes['amarillo']}%", (0, 255, 255)),
            (f"Marron: {porcentajes['marron']}%", (0, 100, 139)),
            (f"Rojo: {porcentajes['rojo']}%", (0, 0, 255))
        ]

        for texto, color in colores_texto:
            cv2.putText(frame, texto, (20, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_offset += 30

        # Estado de salud
        color_estado = (0, 255, 0) if estado == 1 else (0, 0, 255)
        cv2.putText(frame, descripcion[:35], (20, y_offset + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_estado, 2)

        return frame

    @staticmethod
    def obtener_color_dominante(porcentajes):
        """
        Retorna el color dominante de la planta
        """
        if not porcentajes:
            return "Desconocido"

        colores_solo = {k: v for k, v in porcentajes.items() if k != 'masks'}
        max_color = max(colores_solo, key=colores_solo.get)
        valor = colores_solo[max_color]

        if valor > 15:
            return max_color.capitalize()
        return "Mixto"

    @staticmethod
    def evaluar_estado_salud(porcentajes):
        """
        Evalúa el estado de salud basándose en los porcentajes de color
        """
        if not porcentajes:
            return 0, "No se pudo analizar"

        verde = porcentajes.get('verde', 0)
        amarillo = porcentajes.get('amarillo', 0)
        marron = porcentajes.get('marron', 0)
        rojo = porcentajes.get('rojo', 0)

        if verde > 50 and amarillo < 20 and marron < 10:
            return 1, "Saludable"
        elif amarillo > 25:
            return 0, "Deficiencia nutrientes"
        elif marron > 20:
            return 0, "Falta de agua"
        elif rojo > 15 and verde < 40:
            return 0, "Posible enfermedad"
        elif verde > 30:
            return 1, "Estado moderado"
        else:
            return 0, "Color atipico"