from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import requests
from django.views.decorators.csrf import csrf_exempt


from clasificador.models import EspeciePlanta, MiPlanta, MonitoreoPlanta, ConsejoCuidado


@login_required
def mis_plantas(request):
    """Lista todos los ejemplares del usuario actual"""
    plantas = MiPlanta.objects.filter(usuario=request.user).select_related('especie')

    context = {
        'plantas': plantas,
        'total_plantas': plantas.count(),
        'plantas_saludables': plantas.filter(estado=1).count(),
        'plantas_atencion': plantas.filter(estado__in=[0, 2]).count(),
    }
    return render(request, 'planta/mis_plantas.html', context)


@login_required
def editar_planta(request, planta_id):
    """
    Por ahora solo permite ver el ejemplar
    En versiones futuras se puede agregar personalización
    """
    planta = get_object_or_404(MiPlanta, id=planta_id, usuario=request.user)
    return redirect('detalle_planta', planta_id=planta.id)


@login_required
def detalle_planta(request, planta_id):
    """Ver detalle de un ejemplar específico con su historial"""
    planta = get_object_or_404(
        MiPlanta.objects.select_related('especie'),
        id=planta_id,
        usuario=request.user
    )

    # Obtener historial de monitoreos (últimos 20)
    monitoreos = planta.monitoreos.all().order_by('-fecha_monitoreo')[:20]

    context = {
        'planta': planta,
        'monitoreos': monitoreos,
        'total_monitoreos': planta.monitoreos.count(),
    }
    return render(request, 'planta/detalle_planta.html', context)


@login_required
def eliminar_planta(request, planta_id):
    """Eliminar un ejemplar específico del usuario"""
    planta = get_object_or_404(MiPlanta, id=planta_id, usuario=request.user)

    if request.method == 'POST':
        planta.delete()
        return redirect('mis_plantas')

    return render(request, 'planta/eliminacion.html', {'planta': planta})


@login_required
def guardar_planta_monitoreo(request):
    """
    Guarda un nuevo ejemplar desde el monitoreo en tiempo real
    o actualiza uno existente
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

    try:
        # Datos de la especie detectada
        nombre_especie = request.POST.get('nombre', '').strip()

        # VALIDACIONES CRÍTICAS
        invalid_names = ['Detectando...', 'Desconocido', 'no_planta', '']
        if not nombre_especie or nombre_especie in invalid_names:
            return JsonResponse({
                'success': False,
                'message': 'No se ha detectado una especie válida. Espera a que se complete la detección.'
            }, status=400)

        # Datos del análisis de color actual
        try:
            porcentaje_verde = float(request.POST.get('porcentaje_verde', 0))
            porcentaje_amarillo = float(request.POST.get('porcentaje_amarillo', 0))
            porcentaje_marron = float(request.POST.get('porcentaje_marron', 0))
            porcentaje_rojo = float(request.POST.get('porcentaje_rojo', 0))
            estado = int(request.POST.get('estado', 1))
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'message': f'Error en los datos numéricos: {str(e)}'
            }, status=400)

        descripcion_estado = request.POST.get('descripcion_estado', '')

        # ID del ejemplar (para actualizar existente)
        planta_id = request.POST.get('planta_id', '').strip()

        # 1. BUSCAR O CREAR la especie en el catálogo
        especie, especie_creada = EspeciePlanta.objects.get_or_create(
            nombre__iexact=nombre_especie,
            defaults={
                'nombre': nombre_especie,
                'nombre_cientifico': request.POST.get('nombre_cientifico', ''),
                'familia': request.POST.get('familia', ''),
                'descripcion': request.POST.get('descripcion', ''),
                'imagen_url': request.POST.get('imagen_url', ''),
                'en_modelo_entrenado': True,  # Fue detectada por el modelo
                'pendiente_entrenamiento': False,
                'agregada_por': request.user
            }
        )

        if especie_creada:
            print(f"✅ Nueva especie creada en el catálogo: {nombre_especie}")

        # 2. Crear o actualizar el ejemplar
        if planta_id:
            # ACTUALIZAR ejemplar existente
            try:
                mi_planta = MiPlanta.objects.get(id=planta_id, usuario=request.user)
                mi_planta.estado = estado
                mi_planta.porcentaje_verde = porcentaje_verde
                mi_planta.porcentaje_amarillo = porcentaje_amarillo
                mi_planta.porcentaje_marron = porcentaje_marron
                mi_planta.porcentaje_rojo = porcentaje_rojo
                mi_planta.descripcion_estado = descripcion_estado
                mi_planta.save()

                created = False
                mensaje = f'✅ Monitoreo de {especie.nombre} actualizado exitosamente'

            except MiPlanta.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'El ejemplar que intentas actualizar no existe o no te pertenece.'
                }, status=404)
        else:
            # CREAR nuevo ejemplar
            mi_planta = MiPlanta.objects.create(
                usuario=request.user,
                especie=especie,
                estado=estado,
                porcentaje_verde=porcentaje_verde,
                porcentaje_amarillo=porcentaje_amarillo,
                porcentaje_marron=porcentaje_marron,
                porcentaje_rojo=porcentaje_rojo,
                descripcion_estado=descripcion_estado,
            )

            created = True
            mensaje = f'🌱 {especie.nombre} guardada exitosamente en tu colección'

        # 3. Crear registro de monitoreo
        MonitoreoPlanta.objects.create(
            planta=mi_planta,
            estado=estado,
            porcentaje_verde=porcentaje_verde,
            porcentaje_amarillo=porcentaje_amarillo,
            porcentaje_marron=porcentaje_marron,
            porcentaje_rojo=porcentaje_rojo,
            descripcion_estado=descripcion_estado,
        )

        return JsonResponse({
            'success': True,
            'message': mensaje,
            'planta_id': mi_planta.id,
            'created': created,
            'especie_nueva': especie_creada
        })

    except Exception as e:
        # Log del error para debugging
        print(f"❌ Error al guardar planta: {str(e)}")
        print(f"❌ Tipo de error: {type(e).__name__}")
        import traceback
        traceback.print_exc()

        return JsonResponse({
            'success': False,
            'message': f'Error inesperado al guardar: {str(e)}'
        }, status=500)


@login_required
def guardar_nota_monitoreo(request, monitoreo_id):
    """
    Vista para guardar o actualizar notas de un monitoreo ESPECÍFICO
    Cada monitoreo tiene su propia nota independiente
    """
    # Obtener el monitoreo y verificar permisos en una sola consulta
    monitoreo = get_object_or_404(
        MonitoreoPlanta.objects.select_related('planta__usuario'),
        id=monitoreo_id,
        planta__usuario=request.user  # Verificación directa en la query
    )

    if request.method == 'POST':
        notas = request.POST.get('notas', '').strip()

        # Validar longitud máxima
        if len(notas) > 500:
            messages.error(request, '❌ La nota no puede exceder 500 caracteres.')
            return redirect('detalle_planta', planta_id=monitoreo.planta.id)

        # Guardar o eliminar la nota
        monitoreo.notas = notas if notas else None
        monitoreo.save(update_fields=['notas'])  # Solo actualizar el campo notas

        if notas:
            messages.success(request, f'✅ Nota guardada para el monitoreo del {monitoreo.fecha_monitoreo.strftime("%d/%m/%Y")}')
        else:
            messages.success(request, '✅ Nota eliminada exitosamente.')

        return redirect('detalle_planta', planta_id=monitoreo.planta.id)

    # Si no es POST, redirigir al detalle
    return redirect('detalle_planta', planta_id=monitoreo.planta.id)


@login_required
def editar_nota_monitoreo(request, monitoreo_id):
    """
    Vista para mostrar el formulario de edición de nota
    """
    monitoreo = get_object_or_404(
        MonitoreoPlanta.objects.select_related('planta__usuario', 'planta__especie'),
        id=monitoreo_id,
        planta__usuario=request.user
    )

    if request.method == 'POST':
        # Redirigir al guardado
        return guardar_nota_monitoreo(request, monitoreo_id)

    context = {
        'monitoreo': monitoreo,
        'planta': monitoreo.planta,
    }
    return render(request, 'planta/editar_nota_monitoreo.html', context)


@login_required
def manual_usuario(request):
    """Vista del manual de usuario"""
    return render(request, 'clasificador/ManualU.html')


@require_http_methods(["GET"])
def get_consejos_cuidado(request):
    """
    Obtiene los consejos de cuidado para una planta específica
    SOLO LECTURA - Los usuarios no pueden modificar
    """
    nombre_planta = request.GET.get('nombre_planta', '')

    # Validar que hay una planta válida
    if not nombre_planta or nombre_planta == "Detectando..." or nombre_planta == "no_planta":
        return JsonResponse({
            'success': False,
            'message': 'No hay planta detectada'
        })

    try:
        # Buscar la especie en el catálogo
        especie = EspeciePlanta.objects.filter(
            Q(nombre__iexact=nombre_planta) |
            Q(nombre_cientifico__iexact=nombre_planta)
        ).first()

        if not especie:
            return JsonResponse({
                'success': False,
                'message': f'La especie "{nombre_planta}" no está en el catálogo.'
            })

        # Intentar obtener los consejos
        try:
            consejo = especie.consejo

            # Verificar que los consejos estén activos
            if not consejo.activo:
                return JsonResponse({
                    'success': False,
                    'message': f'Los consejos para {especie.nombre} están temporalmente desactivados.'
                })

            # Retornar consejos completos
            return JsonResponse({
                'success': True,
                'consejos': {
                    'nombre_planta': especie.nombre,
                    'nombre_cientifico': especie.nombre_cientifico or '',
                    'luz': consejo.luz,
                    'riego': consejo.riego,
                    'temperatura': consejo.temperatura,
                    'humedad': consejo.humedad,
                    'suelo': consejo.suelo,
                    'fertilizacion': consejo.fertilizacion,
                    'poda': consejo.poda or '',
                    'plagas_comunes': consejo.plagas_comunes or '',
                    'toxicidad': consejo.get_toxicidad_display(),
                    'toxicidad_svg': consejo.get_nivel_toxicidad_display_svg(),
                    'dificultad': consejo.get_dificultad_display(),
                    'dificultad_svg': consejo.get_dificultad_svg(),
                    'notas_adicionales': consejo.notas_adicionales or ''
                }
            })

        except ConsejoCuidado.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Aún no hay consejos de cuidado disponibles para {especie.nombre}. '
                           f'Nuestro equipo está trabajando en agregarlos pronto.'
            })

    except Exception as e:
        # Log del error (opcional)
        print(f"Error al obtener consejos: {str(e)}")

        return JsonResponse({
            'success': False,
            'message': 'Ocurrió un error al cargar los consejos. Por favor, intenta de nuevo.'
        }, status=500)
    

ASSEMBLYAI_API_KEY = "90064a041b134dd7ba5f7c704d4080bf"

@csrf_exempt
@login_required
def transcribir_audio_nota(request, monitoreo_id):
    """
    Recibe un archivo de audio grabado desde el navegador,
    lo envía a AssemblyAI y guarda la transcripción como nota del monitoreo.
    """
    if request.method != 'POST' or 'audio' not in request.FILES:
        return JsonResponse({'error': 'No se envió archivo de audio'}, status=400)

    # Verificar monitoreo del usuario
    monitoreo = get_object_or_404(
        MonitoreoPlanta.objects.select_related('planta__usuario'),
        id=monitoreo_id,
        planta__usuario=request.user
    )

    audio_file = request.FILES['audio']

    # Subir a AssemblyAI
    headers = {'authorization': ASSEMBLYAI_API_KEY}

    upload_response = requests.post(
        'https://api.assemblyai.com/v2/upload',
        headers=headers,
        data=audio_file.read()
    )

    if upload_response.status_code != 200:
        return JsonResponse({'error': 'Error al subir audio'}, status=upload_response.status_code)

    audio_url = upload_response.json().get('upload_url')

    # Crear la transcripción
    json_data = {"audio_url": audio_url, "language_code": "es"}
    transcript_response = requests.post(
        'https://api.assemblyai.com/v2/transcript',
        headers=headers,
        json=json_data
    )

    if transcript_response.status_code != 200:
        return JsonResponse({'error': 'Error al crear transcripción'}, status=transcript_response.status_code)

    transcript_id = transcript_response.json()['id']

    # Esperar a que termine la transcripción (consulta polling)
    status = "processing"
    while status not in ["completed", "error"]:
        poll = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        status = poll.json()['status']
        if status == "completed":
            text = poll.json()['text']
            monitoreo.notas = text
            monitoreo.save(update_fields=['notas'])
            return JsonResponse({'success': True, 'texto': text})
        elif status == "error":
            return JsonResponse({'error': 'Error en transcripción'}, status=500)

    return JsonResponse({'error': 'Transcripción no completada'}, status=500)