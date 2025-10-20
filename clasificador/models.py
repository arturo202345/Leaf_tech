from django.db import models

# Create your models here.
from django.db import models

class Planta(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    Temperatura = models.CharField(max_length=50)
    Humedad = models.CharField(max_length=50)
    PH = models.CharField(max_length=50)
    Estado = models.IntegerField(max_length=1)
    Descripcion = models.TextField(blank=True, null=True)
    ImagenURL = models.URLField(blank=True, null=True)
    Referencia = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.nombre