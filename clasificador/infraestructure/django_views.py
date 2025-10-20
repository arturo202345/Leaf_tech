from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
import cv2
from clasificador.application.classify_plant_usecase import ClassifyPlantUseCase
from clasificador.infraestructure.tf_classifier import TensorflowPlantClassifier
from clasificador.models import Planta
from django.core.exceptions import ObjectDoesNotExist

classifier_service = TensorflowPlantClassifier("modelo_plantas_cnn.h5", "labels.pkl")
usecase = ClassifyPlantUseCase(classifier_service)

# Variable global para guardar el último resultado detectado
last_result = {"label": "Detectando...", "prob": 0.0}

def generate_video():
    global last_result
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (25, 40, 40), (95, 255, 255))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            if w * h > 5000:
                crop = frame[y:y+h, x:x+w]
                result = usecase.execute(crop)
                last_result = result  # guardamos el último resultado

                # solo marcamos el recuadro (sin texto)
                color = (0, 255, 0) if result["label"] != "No está en los datos" else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

def video_feed(request):
    return StreamingHttpResponse(generate_video(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

# Nueva vista para devolver el resultado actual
def get_last_result(request):
    global last_result
    # Convertimos todos los valores a tipos nativos de Python (para evitar float32, etc.)
    safe_result = {
        "label": str(last_result.get("label", "Detectando...")),
        "prob": float(last_result.get("prob", 0.0))
    }
    return JsonResponse(safe_result)

def index(request):
    return render(request, 'clasificador/index.html')

def page_1(request):
    return render(request, 'clasificador/page1.html')

def get_plant_data(request):
    global last_result
    label = str(last_result.get("label", "Desconocido"))
    prob = float(last_result.get("prob", 0.0))

    try:
        planta = Planta.objects.get(nombre__iexact=label)
        data = {
            "label": planta.nombre,
            "temperatura": planta.Temperatura,
            "humedad": planta.Humedad,
            "estado": planta.Estado,
            "descripcion": planta.Descripcion or "No hay descripción disponible.",
            "imagen": planta.ImagenURL or "https://via.placeholder.com/280x320?text=Sin+imagen",
            "referencia": planta.Referencia or "https://es.wikipedia.org/wiki/Planta",
            "prob": prob,
        }
    except ObjectDoesNotExist:
        data = {
            "label": label,
            "temperatura": "N/A",
            "humedad": "N/A",
            "estado": "N/A",
            "descripcion": "No hay información sobre esta planta.",
            "imagen": "https://via.placeholder.com/280x320?text=Desconocido",
            "referencia": "https://es.wikipedia.org/wiki/Planta",
            "prob": prob,
        }

    return JsonResponse(data)
