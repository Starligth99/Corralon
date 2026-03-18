from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Deposito, Vehiculo


ROLE_ADMIN = "administrador"
ROLE_OPERADOR = "operador"
ROLE_CONSULTA = "consulta"

ROLE_LABELS = {
    ROLE_ADMIN: "Administrador",
    ROLE_OPERADOR: "Operador",
    ROLE_CONSULTA: "Consulta",
}

ROLE_PERMISSIONS = {
    ROLE_ADMIN: {"ver_dashboard", "ver_inventario", "registrar", "liberar", "gestionar_depositos"},
    ROLE_OPERADOR: {"ver_dashboard", "ver_inventario", "registrar", "liberar"},
    ROLE_CONSULTA: {"ver_dashboard", "ver_inventario"},
}


def _is_logged_in(request):
    return "usuario" in request.session


def _get_role(request):
    role = request.session.get("rol")
    return role if role in ROLE_LABELS else ROLE_CONSULTA


def _get_role_for_user(user):
    if user.is_superuser:
        return ROLE_ADMIN
    if user.groups.filter(name=ROLE_ADMIN).exists():
        return ROLE_ADMIN
    if user.groups.filter(name=ROLE_OPERADOR).exists():
        return ROLE_OPERADOR
    if user.groups.filter(name=ROLE_CONSULTA).exists():
        return ROLE_CONSULTA
    return ROLE_CONSULTA


def _has_permission(request, permission):
    return permission in ROLE_PERMISSIONS.get(_get_role(request), set())


def _reject_unauthorized(request):
    messages.error(request, "Tu rol no tiene permiso para esta accion.")
    return redirect("dashboard")


def login_view(request):
    error = None

    if request.method == 'POST':
        usuario = (request.POST.get('usuario') or '').strip()
        password = request.POST.get('password') or ''

        if usuario and password:
            user = authenticate(request, username=usuario, password=password)
            if user:
                request.session['usuario'] = user.get_username()
                request.session['rol'] = _get_role_for_user(user)
                return redirect('dashboard')
            error = 'Credenciales invalidas. Verifica tu usuario y contrasena.'
        else:
            error = 'Ingresa usuario y contrasena para continuar.'

    return render(request, 'Vehiculos/login.html', {'error': error})


def dashboard(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "ver_dashboard"):
        return redirect('login')

    total = Vehiculo.objects.count()
    liberados = Vehiculo.objects.filter(estatus_legal=Vehiculo.ESTATUS_LIBERADO).count()
    pendientes = Vehiculo.objects.exclude(estatus_legal=Vehiculo.ESTATUS_LIBERADO).count()
    en_proceso = max(total - pendientes - liberados, 0)

    monthly_data = (
        Vehiculo.objects.filter(fecha_ingreso__isnull=False)
        .annotate(month=TruncMonth('fecha_ingreso'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('-month')[:6]
    )
    monthly_data = list(reversed(monthly_data))
    monthly_labels = [item['month'].strftime('%b') for item in monthly_data]
    monthly_ingress = [item['total'] for item in monthly_data]

    tipo_data = (
        Vehiculo.objects.values('tipo_servicio')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    type_labels = [item['tipo_servicio'] for item in tipo_data]
    type_values = [item['total'] for item in tipo_data]

    actividad = Vehiculo.objects.order_by('-creado_en')[:5]

    context = {
        'resumen_data': {
            'total': total,
            'pendientes': pendientes,
            'liberados': liberados,
            'enProceso': en_proceso,
        },
        'detalle_data': {
            'monthlyLabels': monthly_labels,
            'monthlyIngress': monthly_ingress,
            'typeLabels': type_labels,
            'typeValues': type_values,
        },
        'actividad': actividad,
        'hoy': date.today(),
        'rol': _get_role(request),
        'rol_label': ROLE_LABELS[_get_role(request)],
        'can_registrar': _has_permission(request, "registrar"),
        'can_inventario': _has_permission(request, "ver_inventario"),
        'can_liberar': _has_permission(request, "liberar"),
        'can_depositos': _has_permission(request, "gestionar_depositos"),
    }
    return render(request, 'Vehiculos/dashboard.html', context)


def depositos_view(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "gestionar_depositos"):
        return _reject_unauthorized(request)

    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        if not nombre:
            messages.error(request, 'Ingresa un nombre de deposito valido.')
            return redirect('depositos')
        if Deposito.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'El deposito "{nombre}" ya existe.')
            return redirect('depositos')

        Deposito.objects.create(nombre=nombre)
        messages.success(request, f'Deposito "{nombre}" agregado correctamente.')
        return redirect('depositos')

    depositos = Deposito.objects.order_by('nombre')
    return render(
        request,
        'Vehiculos/depositos.html',
        {
            'depositos': depositos,
            'can_depositos': True,
        },
    )


def registrar_vehiculo(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "registrar"):
        return _reject_unauthorized(request)

    def build_context():
        return {
            'depositos': list(Deposito.objects.order_by('nombre').values_list('nombre', flat=True)),
            'can_depositos': _has_permission(request, "gestionar_depositos"),
        }

    if request.method == 'POST':
        post = request.POST
        archivo = request.FILES.get('documento_pdf')

        required = [
            'fecha_ingreso',
            'folio',
            'autoridad',
            'deposito',
            'marca',
            'modelo',
            'anio',
            'placas',
            'vin',
            'numero_motor',
            'tipo_servicio',
            'estatus_legal',
            'grua_motivo',
            'grua_direccion',
        ]
        missing = [field for field in required if not (post.get(field) or '').strip()]
        if missing:
            messages.error(request, 'Completa todos los campos obligatorios.')
            return render(request, 'Vehiculos/registrar-vehiculo.html', build_context())

        folio = post.get('folio', '').strip().upper()
        if Vehiculo.objects.filter(folio=folio).exists():
            messages.error(request, f'El folio {folio} ya existe.')
            return render(request, 'Vehiculos/registrar-vehiculo.html', build_context())

        try:
            anio = int(post.get('anio', '0'))
            kilometraje = int(post.get('kilometraje', '0') or 0)
        except ValueError:
            messages.error(request, 'Revisa los campos numericos.')
            return render(request, 'Vehiculos/registrar-vehiculo.html', build_context())

        vehiculo = Vehiculo.objects.create(
            folio=folio,
            fecha_ingreso=post.get('fecha_ingreso'),
            turno=(post.get('turno') or '').strip(),
            autoridad=(post.get('autoridad') or '').strip(),
            deposito=(post.get('deposito') or '').strip(),
            motivo=(post.get('motivo') or '').strip(),
            grua_motivo=(post.get('grua_motivo') or '').strip(),
            grua_direccion=(post.get('grua_direccion') or '').strip(),
            marca=(post.get('marca') or '').strip(),
            modelo=(post.get('modelo') or '').strip(),
            anio=anio,
            color=(post.get('color') or '').strip(),
            placas=(post.get('placas') or '').strip().upper(),
            vin=(post.get('vin') or '').strip().upper(),
            numero_motor=(post.get('numero_motor') or '').strip().upper(),
            tipo_servicio=(post.get('tipo_servicio') or '').strip(),
            combustible=(post.get('combustible') or '').strip(),
            kilometraje=kilometraje,
            estatus_legal=(post.get('estatus_legal') or Vehiculo.ESTATUS_EN_CUSTODIA).strip(),
            oficio=(post.get('oficio') or '').strip(),
            fecha_oficio=post.get('fecha_oficio') or None,
            titular=(post.get('titular') or '').strip(),
            observaciones=(post.get('observaciones') or '').strip(),
            documento_nombre=archivo.name if archivo else '',
            liberado=(post.get('estatus_legal') or '').strip() == Vehiculo.ESTATUS_LIBERADO,
        )

        if vehiculo.liberado:
            vehiculo.fecha_liberacion = timezone.now()
            vehiculo.save(update_fields=['fecha_liberacion'])

        messages.success(request, f'Vehiculo {vehiculo.folio} registrado correctamente.')
        return redirect('vehiculos')

    return render(request, 'Vehiculos/registrar-vehiculo.html', build_context())


def vehiculos_list(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "ver_inventario"):
        return redirect('login')

    data = [
        {
            'folio': v.folio,
            'marca': v.marca,
            'modelo': v.modelo,
            'anio': v.anio,
            'placas': v.placas,
            'vin': v.vin,
            'deposito': v.deposito,
            'motivo': v.motivo,
            'grua_motivo': v.grua_motivo,
            'grua_direccion': v.grua_direccion,
            'tipo': v.tipo_servicio,
            'estatus': v.estatus_legal,
            'fecha': v.fecha_ingreso.isoformat() if v.fecha_ingreso else '',
        }
        for v in Vehiculo.objects.all()
    ]
    return render(
        request,
        'Vehiculos/vehiculos.html',
        {
            'vehiculos_data': data,
            'can_registrar': _has_permission(request, "registrar"),
            'can_liberar': _has_permission(request, "liberar"),
        },
    )


def liberar_vehiculo(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "liberar"):
        return _reject_unauthorized(request)

    def build_context(prefill=None):
        lookup_data = [
            {
                'folio': v.folio,
                'placas': v.placas,
                'vin': v.vin,
                'vehiculo': f'{v.marca} {v.modelo} {v.anio}',
            }
            for v in Vehiculo.objects.exclude(estatus_legal=Vehiculo.ESTATUS_LIBERADO)[:200]
        ]
        return {
            'vehiculos_lookup_data': lookup_data,
            'vehiculo_prefill': prefill,
            'can_liberar': _has_permission(request, "liberar"),
        }

    folio_query = (request.GET.get('folio') or '').strip().upper()
    vehiculo_prefill = None
    if folio_query:
        vehiculo_prefill = Vehiculo.objects.filter(folio=folio_query).first()

    if request.method == 'POST':
        post = request.POST
        folio = (post.get('folio') or '').strip().upper()
        placas = (post.get('placas') or '').strip().upper()
        vin = (post.get('vin') or '').strip().upper()
        oficio = (post.get('oficio') or '').strip()
        fecha_oficio = post.get('fecha_oficio')
        autoriza = (post.get('autoriza') or '').strip()
        observaciones = (post.get('observaciones') or '').strip()

        if not all([folio, placas, vin, oficio, fecha_oficio, autoriza]):
            messages.error(request, 'Completa todos los datos obligatorios de liberacion.')
            return render(request, 'Vehiculos/liberar-vehiculo.html', build_context(vehiculo_prefill))

        vehiculo = Vehiculo.objects.filter(folio=folio).first()
        if not vehiculo:
            messages.error(request, f'No existe un vehiculo con folio {folio}.')
            return render(request, 'Vehiculos/liberar-vehiculo.html', build_context(vehiculo_prefill))

        if vehiculo.placas != placas or vehiculo.vin != vin:
            messages.error(request, 'Placas o VIN no coinciden con el folio capturado.')
            return render(request, 'Vehiculos/liberar-vehiculo.html', build_context(vehiculo))

        vehiculo.oficio = oficio
        vehiculo.fecha_oficio = fecha_oficio
        vehiculo.autoriza_liberacion = autoriza
        vehiculo.liberacion_observaciones = observaciones
        vehiculo.documento_nombre = (
            request.FILES['documento_pdf'].name if request.FILES.get('documento_pdf') else vehiculo.documento_nombre
        )
        vehiculo.aceite_drenado = post.get('aceite_drenado') == 'on'
        vehiculo.combustible_drenado = post.get('combustible_drenado') == 'on'
        vehiculo.anticongelante_drenado = post.get('anticongelante_drenado') == 'on'
        vehiculo.sin_objetos_pendientes = post.get('sin_objetos_pendientes') == 'on'
        vehiculo.marcar_liberado()
        vehiculo.save()

        messages.success(request, f'Vehiculo {vehiculo.folio} liberado correctamente.')
        return redirect('vehiculos')

    return render(request, 'Vehiculos/liberar-vehiculo.html', build_context(vehiculo_prefill))


def logout_view(request):
    request.session.flush()
    return redirect('login')
