from django.contrib import admin

from .models import Deposito, Vehiculo


@admin.register(Deposito)
class DepositoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'creado_en')
    search_fields = ('nombre',)


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'folio',
        'marca',
        'modelo',
        'placas',
        'estatus_legal',
        'fecha_ingreso',
        'liberado',
    )
    list_filter = ('estatus_legal', 'tipo_servicio', 'fecha_ingreso')
    search_fields = ('folio', 'placas', 'vin', 'marca', 'modelo')

# Register your models here.
