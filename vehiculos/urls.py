from django.urls import path

from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vehiculos/registrar/', views.registrar_vehiculo, name='registrar_vehiculo'),
    path('vehiculos/inventario/', views.vehiculos_list, name='vehiculos'),
    path('vehiculos/liberar/', views.liberar_vehiculo, name='liberar_vehiculo'),
    path('vehiculos/depositos/', views.depositos_view, name='depositos'),
    path('vehiculos/correcciones/solicitar/', views.solicitar_correccion, name='solicitar_correccion'),
    path('vehiculos/correcciones/', views.solicitudes_correccion, name='solicitudes_correccion'),
    path('logout/', views.logout_view, name='logout'),
]
