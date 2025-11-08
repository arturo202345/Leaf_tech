import base64
import cv2
import numpy as np
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from clasificador.application.classify_plant_usecase import ClassifyPlantUseCase
from clasificador.infraestructure.tf_classifier import TensorflowPlantClassifier
from clasificador.infraestructure.color_analyzer import analizar_colores

classifier = TensorflowPlantClassifier()
usecase = ClassifyPlantUseCase(classifier)

class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if "frame" not in data:
            return

        frame_data = data["frame"].split(",")[1]
        img_bytes = base64.b64decode(frame_data)

        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        result = usecase.execute(frame)
        colores = analizar_colores(frame)

        final = {
            **result,
            **colores
        }

        await self.send(json.dumps(final))

    async def disconnect(self, code):
        pass
