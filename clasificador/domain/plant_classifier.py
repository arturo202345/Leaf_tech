from abc import ABC, abstractmethod

class PlantClassifierPort(ABC):
    """Puerto (interfaz) que define cómo clasificar una planta."""

    @abstractmethod
    def classify(self, image):
        """Recibe una imagen y devuelve (nombre, probabilidad)."""
        pass