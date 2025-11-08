from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q
from django.contrib import messages
from clasificador.models import EspeciePlanta, MiPlanta, MonitoreoPlanta


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