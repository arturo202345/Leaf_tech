class ClassifyPlantUseCase:
    """Caso de uso: Clasificar una planta."""

    def __init__(self, classifier_service):
        self.classifier_service = classifier_service

    def execute(self, image):
        label, prob = self.classifier_service.classify(image)
        if prob < 0.7:
            return {"label": "No está en los datos", "prob": prob}
        return {"label": label, "prob": prob}