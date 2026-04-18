from django.urls import path

from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vehiculos/registrar/', views.registrar_vehiculo, name='registrar_vehiculo'),
    path('vehiculos/operador_registrador', views.operadorregistrador_view, name='operador'),
    path('clientes/', views.clientes_list_view, name='clientes_list'),
    path('clientes/<int:cliente_id>/credito/', views.editar_credito_view, name='editar_credito'),
    path('historial/', views.historial_view, name='historial'),
    path('vehiculos/inventario/', views.vehiculos_list, name='vehiculos'),
    path('inventario/', views.vehiculos_list, name='inventario'),
    path('vehiculos/', views.vehiculos_list),
    path('vehiculos/liberar/', views.liberar_vehiculo, name='liberar_vehiculo'),
    path('vehiculos/depositos/', views.depositos_view, name='depositos'),
    path('usuarios/', views.usuarios_view, name='usuarios'),
    path('vehiculos/correcciones/solicitar/', views.solicitar_correccion, name='solicitar_correccion'),
    path('vehiculos/correcciones/', views.solicitudes_correccion, name='solicitudes_correccion'),
    path('logout/', views.logout_view, name='logout'),
]
