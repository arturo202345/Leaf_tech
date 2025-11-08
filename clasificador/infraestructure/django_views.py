from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
import cv2
import numpy as np
from clasificador.application.classify_plant_usecase import ClassifyPlantUseCase
from clasificador.infraestructure.tf_classifier import TensorflowPlantClassifier
from clasificador.domain.color_analizer import ColorAnalyzer
from clasificador.models import EspeciePlanta
from django.core.exceptions import ObjectDoesNotExist

classifier_service = TensorflowPlantClassifier("modelo_plantas_cnn_v4.h5", "labels_v4.pkl")
usecase = ClassifyPlantUseCase(classifier_service)
color_analyzer = ColorAnalyzer()

# Variables globales para el estado actual
last_result = {"label": "Detectando...", "prob": 0.0}
last_color_analysis = {
    'verde': 0,
    'amarillo': 0,
    'marron': 0,
    'rojo': 0,
    'estado': 0,
    'descripcion': 'Analizando...'
}

def generate_video():
    """Genera el stream de video con detección y análisis en tiempo real"""
    global last_result, last_color_analysis
    cap = cv2.VideoCapture(0)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Redimensionar frame para mejor rendimiento
        frame = cv2.resize(frame, (640, 480))

        # Detección de objetos verdes (plantas)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Rango de verde más natural
        lower_green = (40, 40, 40)
        upper_green = (80, 255, 255)
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # Limpieza de ruido
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        # Buscar contornos (posibles hojas)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            area = cv2.contourArea(c)

            # Filtro por área
            if not (8000 < area < 150000):
                continue

            # Filtro por circularidad
            perimeter = cv2.arcLength(c, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            if circularity < 0.2 or circularity > 0.9:
                continue

            # Filtro por aspect ratio
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = w / float(h)
            if not (0.5 < aspect_ratio < 2.0):
                continue

            # Validación de color verde
            mean_hsv = cv2.mean(hsv[y:y + h, x:x + w])
            if not (35 <= mean_hsv[0] <= 85 and mean_hsv[1] > 40 and mean_hsv[2] > 50):
                continue

            # Recortar región de interés
            crop = frame[y:y + h, x:x + w]

            # Clasificación de planta
            result = usecase.execute(crop)
            last_result = result

            # Si no es una planta, ignorar y no dibujar nada
            if result["label"] == "No está en los datos":
                continue

            # Análisis de color cada 10 frames
            if frame_count % 10 == 0:
                porcentajes = color_analyzer.detectar_colores_frame(crop)
                if porcentajes:
                    estado, descripcion = color_analyzer.evaluar_estado_salud(porcentajes)
                    last_color_analysis = {
                        'verde': porcentajes['verde'],
                        'amarillo': porcentajes['amarillo'],
                        'marron': porcentajes['marron'],
                        'rojo': porcentajes['rojo'],
                        'estado': estado,
                        'descripcion': descripcion
                    }

            # Color del contorno según la confianza
            if result["prob"] < 0.85:
                color = (0, 255, 255)  # amarillo = baja confianza
            else:
                color = (0, 255, 0)  # verde = alta confianza

            # Dibujar solo el contorno con grosor aumentado
            cv2.drawContours(frame, [c], -1, color, 4)

        frame_count += 1

        # Codificar y enviar frame
        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
def video_feed(request):
    """Vista para el streaming de video"""
    return StreamingHttpResponse(
        generate_video(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


def get_last_result(request):
    """Retorna el último resultado de clasificación"""
    global last_result
    safe_result = {
        "label": str(last_result.get("label", "Detectando...")),
        "prob": float(last_result.get("prob", 0.0))
    }
    return JsonResponse(safe_result)


def index(request):
    """Página principal"""
    return render(request, 'clasificador/index.html')


def page_1(request):
    """Página de monitoreo"""
    return render(request, 'clasificador/page1.html')

def get_plant_data(request):
    """
    Retorna información completa de la especie detectada
    Incluye datos del catálogo y análisis de color en tiempo real

    IMPORTANTE: Solo retorna info de la ESPECIE, no de ejemplares específicos
    Los ejemplares específicos se manejan en las vistas de usuario
    """
    global last_result, last_color_analysis

    label = str(last_result.get("label", "Desconocido"))
    prob = float(last_result.get("prob", 0.0))

    # Estructura base con análisis de color (siempre disponible)
    base_data = {
        "label": label,
        "prob": prob,
        "porcentaje_verde": last_color_analysis['verde'],
        "porcentaje_amarillo": last_color_analysis['amarillo'],
        "porcentaje_marron": last_color_analysis['marron'],
        "porcentaje_rojo": last_color_analysis['rojo'],
        "estado": last_color_analysis['estado'],
        "descripcion_estado": last_color_analysis['descripcion'],
    }

    # CASO 1: Estado de detección inicial
    if label in ["Detectando...", "Desconocido", ""]:
        data = {
            **base_data,
            "nombre_cientifico": "-",
            "familia": "-",
            "descripcion": "La información aparecerá cuando se detecte una planta.",
            "imagen": "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=280&h=320&fit=crop",
            "referencia": "https://es.wikipedia.org/wiki/Planta",
            "mis_ejemplares": [],
            "tiene_ejemplares": False
        }
        return JsonResponse(data)

    # CASO 2: no_planta detectado (especie no catalogada)
    if label.lower() == "no_planta":
        data = {
            **base_data,
            "label": "no_planta",
            "nombre_cientifico": "-",
            "familia": "-",
            "descripcion": "Especie detectada pero no está en el catálogo.",
            "imagen": "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=280&h=320&fit=crop",
            "referencia": "https://es.wikipedia.org/wiki/Planta",
            "mis_ejemplares": [],
            "tiene_ejemplares": False
        }
        return JsonResponse(data)

    # CASO 3: Buscar especie en el catálogo
    try:
        especie = EspeciePlanta.objects.filter(nombre__iexact=label).first()

        if especie is None:
            # Especie detectada pero no está en la BD
            data = {
                **base_data,
                "nombre_cientifico": "-",
                "familia": "-",
                "descripcion": f'La especie "{label}" fue detectada pero no está en el catálogo.',
                "imagen": "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=280&h=320&fit=crop",
                "referencia": "https://es.wikipedia.org/wiki/Planta",
                "mis_ejemplares": [],
                "tiene_ejemplares": False
            }
            return JsonResponse(data)

        # ESPECIE ENCONTRADA EN EL CATÁLOGO
        data = {
            **base_data,
            "label": especie.nombre,
            "nombre_cientifico": especie.nombre_cientifico or "-",
            "familia": especie.familia or "-",
            "descripcion": especie.descripcion or "No hay descripción disponible para esta especie.",
            "imagen": especie.imagen_url or "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=280&h=320&fit=crop",
            "referencia": especie.referencia_url or "https://es.wikipedia.org/wiki/Planta",
        }

        # Si el usuario está autenticado, incluir sus ejemplares de esta especie
        if request.user.is_authenticated:
            from clasificador.models import MiPlanta
            mis_ejemplares = MiPlanta.objects.filter(
                usuario=request.user,
                especie=especie
            ).values('id', 'estado', 'especie__nombre')

            data['mis_ejemplares'] = list(mis_ejemplares)
            data['tiene_ejemplares'] = len(mis_ejemplares) > 0
        else:
            data['mis_ejemplares'] = []
            data['tiene_ejemplares'] = False

        return JsonResponse(data)

    except Exception as e:
        # Error inesperado
        print(f"❌ Error en get_plant_data: {str(e)}")
        data = {
            **base_data,
            "nombre_cientifico": "-",
            "familia": "-",
            "descripcion": "Error al obtener información de la planta.",
            "imagen": "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=280&h=320&fit=crop",
            "referencia": "https://es.wikipedia.org/wiki/Planta",
            "mis_ejemplares": [],
            "tiene_ejemplares": False
        }
        return JsonResponse(data)

def get_user_plants_of_species(request):
    """
    Retorna los ejemplares del usuario de una especie específica
    Útil para cuando el usuario quiere guardar/actualizar un ejemplar
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Usuario no autenticado'}, status=401)

    especie_nombre = request.GET.get('especie', '')

    try:
        from clasificador.models import MiPlanta

        ejemplares = MiPlanta.objects.filter(
            usuario=request.user,
            especie__nombre__iexact=especie_nombre
        ).select_related('especie').values(
            'id',
            'estado',
            'especie__nombre',
            'ultima_actualizacion',
            'descripcion_estado'
        )

        return JsonResponse({
            'success': True,
            'ejemplares': list(ejemplares),
            'count': len(ejemplares)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

