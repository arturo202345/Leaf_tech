import cv2
import numpy as np
import tensorflow as tf
import pickle
from clasificador.domain.plant_classifier import PlantClassifierPort

class TensorflowPlantClassifier(PlantClassifierPort):
    """Adaptador que conecta el dominio con TensorFlow."""

    def __init__(self, model_path, labels_path):
        self.model = tf.keras.models.load_model(model_path)
        with open(labels_path, "rb") as f:
            labels_dict = pickle.load(f)
        self.labels = {v: k for k, v in labels_dict.items()}

    def classify(self, image):
        img = cv2.resize(image, (128, 128))
        img = img.astype("float32") / 255.0
        img = np.expand_dims(img, axis=0)
        pred = self.model.predict(img, verbose=0)
        idx = np.argmax(pred)
        prob = np.max(pred)
        return self.labels.get(idx, "Desconocido"), prob