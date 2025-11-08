from django.db import models
from django.contrib.auth.models import User


class EspeciePlanta(models.Model):
    """
    Catálogo GLOBAL de especies (biblioteca de referencia)
    NO se edita por usuarios, solo admin o sistema de entrenamiento
    """
    nombre = models.CharField(max_length=100, unique=True)
    nombre_cientifico = models.CharField(max_length=150, blank=True, null=True)
    familia = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen_url = models.URLField(blank=True, null=True)
    referencia_url = models.URLField(blank=True, null=True)

    # Control de modelo
    en_modelo_entrenado = models.BooleanField(
        default=False,
        help_text="True si está en el modelo CNN actual"
    )
    pendiente_entrenamiento = models.BooleanField(
        default=False,
        help_text="True si fue detectada pero no está en el modelo"
    )

    # Contador de ejemplares para priorizar reentrenamiento
    total_ejemplares = models.IntegerField(default=0)

    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    agregada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que sugirió esta especie"
    )

    class Meta:
        verbose_name = "Especie de Planta"
        verbose_name_plural = "Especies de Plantas"
        ordering = ['nombre']

    def __str__(self):
        status = "✓" if self.en_modelo_entrenado else "⏳"
        return f"{status} {self.nombre}"


class MiPlanta(models.Model):
    """
    Ejemplares individuales de cada usuario
    Aquí cada usuario personaliza SUS plantas
    """
    ESTADO_CHOICES = [
        (0, 'Enferma'),
        (1, 'Saludable'),
        (2, 'Crítica'),
    ]

    # Relaciones
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mis_plantas')
    especie = models.ForeignKey(EspeciePlanta, on_delete=models.CASCADE, related_name='ejemplares')

    # Sin personalización por ahora - cada usuario solo guarda ejemplares

    # Estado actual (última medición)
    estado = models.IntegerField(choices=ESTADO_CHOICES, default=1)
    porcentaje_verde = models.FloatField(default=0.0)
    porcentaje_amarillo = models.FloatField(default=0.0)
    porcentaje_marron = models.FloatField(default=0.0)
    porcentaje_rojo = models.FloatField(default=0.0)
    descripcion_estado = models.TextField(blank=True, null=True)

    # Metadata
    fecha_agregada = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mi Planta"
        verbose_name_plural = "Mis Plantas"
        ordering = ['-ultima_actualizacion']
        # Un usuario solo puede tener UN ejemplar de cada especie
        unique_together = [['usuario', 'especie']]

    def save(self, *args, **kwargs):
        # Actualizar contador en la especie
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.especie.total_ejemplares = self.especie.ejemplares.count()
            self.especie.save()

    def delete(self, *args, **kwargs):
        especie = self.especie
        super().delete(*args, **kwargs)
        especie.total_ejemplares = especie.ejemplares.count()
        especie.save()

    def __str__(self):
        return f"{self.especie.nombre} #{self.id} - {self.usuario.username}"

    @property
    def nombre_completo(self):
        """Retorna nombre para mostrar"""
        return f"{self.especie.nombre} #{self.id}"


class MonitoreoPlanta(models.Model):
    """
    Historial de monitoreos de cada ejemplar del usuario
    """
    ESTADO_CHOICES = [
        (0, 'Enferma'),
        (1, 'Saludable'),
        (2, 'Crítica'),
    ]

    planta = models.ForeignKey(MiPlanta, on_delete=models.CASCADE, related_name='monitoreos')

    # Datos del monitoreo
    estado = models.IntegerField(choices=ESTADO_CHOICES)
    porcentaje_verde = models.FloatField()
    porcentaje_amarillo = models.FloatField()
    porcentaje_marron = models.FloatField()
    porcentaje_rojo = models.FloatField()
    descripcion_estado = models.TextField(blank=True, null=True)

    # Observaciones del usuario
    notas = models.TextField(
        blank=True,
        null=True,
        help_text="Tus observaciones en este monitoreo"
    )
    foto_url = models.URLField(blank=True, null=True)

    # Metadata
    fecha_monitoreo = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Monitoreo"
        verbose_name_plural = "Monitoreos"
        ordering = ['-fecha_monitoreo']

    def __str__(self):
        return f"Monitoreo de {self.planta} - {self.fecha_monitoreo.strftime('%d/%m/%Y %H:%M')}"