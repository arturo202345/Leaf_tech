from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
import cv2
from clasificador.application.classify_plant_usecase import ClassifyPlantUseCase
from clasificador.infraestructure.tf_classifier import TensorflowPlantClassifier

classifier_service = TensorflowPlantClassifier("modelo_plantas_cnn.h5", "labels.pkl")
usecase = ClassifyPlantUseCase(classifier_service)

def generate_video():
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
                color = (0, 255, 0) if result["label"] != "No está en los datos" else (0, 0, 255)
                texto = f"{result['label']} ({result['prob']*100:.1f}%)"
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, texto, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

def video_feed(request):
    return StreamingHttpResponse(generate_video(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

def index(request):
    return render(request, 'clasificador/index.html')
