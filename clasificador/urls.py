from django.urls import path, include
from clasificador.infraestructure import django_views as plant_views
from clasificador.login import loginViews as auth_views
from clasificador.plantas import plantasViews as plantas_views

urlpatterns = [
    # Rutas de plantas (infraestructura)
    path('', plant_views.index, name='index'),
    path('video_feed/', plant_views.video_feed, name='video_feed'),
    path('page1/', plant_views.page_1, name='page1'),
    path('get_last_result/', plant_views.get_last_result, name='get_last_result'),
    path('get_plant_data/', plant_views.get_plant_data, name='get_plant_data'),
    path('manual_usuario/', plantas_views.manual_usuario, name='manual_usuario'),

    # ✅ RUTA CORREGIDA - Faltaba 'name'
    path('get-consejos-cuidado/', plantas_views.get_consejos_cuidado, name='get_consejos_cuidado'),

    # Rutas de gestión de plantas del usuario
    path('mis-plantas/', plantas_views.mis_plantas, name='mis_plantas'),
    path('editar-planta/<int:planta_id>/', plantas_views.editar_planta, name='editar_planta'),
    path('planta/<int:planta_id>/', plantas_views.detalle_planta, name='detalle_planta'),
    path('planta/<int:planta_id>/eliminar/', plantas_views.eliminar_planta, name='eliminar_planta'),

    path('planta/monitoreo/<int:monitoreo_id>/nota/', plantas_views.guardar_nota_monitoreo,
         name='guardar_nota_monitoreo'),

    # Guardar desde monitoreo en tiempo real
    path('guardar-monitoreo/', plantas_views.guardar_planta_monitoreo, name='guardar_planta_monitoreo'),

    # Rutas de autenticación
    path('signup/', auth_views.signup, name='signup'),
    path('signin/', auth_views.signin, name='signin'),
    path('logout/', auth_views.signout, name='logout'),

    path('monitoreo/<int:monitoreo_id>/transcribir_audio/', plantas_views.transcribir_audio_nota, name='transcribir_audio_nota')
]