from datetime import date
import random

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.models import Group
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import Deposito, SolicitudCorreccion, Vehiculo


ROLE_ADMIN = "administrador"
ROLE_OPERADOR = "operador"
ROLE_CONSULTA = "consulta"
ALLOWED_EMAIL_DOMAIN = "@smyt.gob.mx"

ROLE_LABELS = {
    ROLE_ADMIN: "Administrador",
    ROLE_OPERADOR: "Operador",
    ROLE_CONSULTA: "Consulta",
}

ROLE_PERMISSIONS = {
    ROLE_ADMIN: {
        "ver_dashboard",
        "ver_inventario",
        "registrar",
        "operadorregistrador",
        "liberar",
        "gestionar_depositos",
        "gestionar_correcciones",
        "gestionar_usuarios",
        "solicitar_correccion",
    },
    ROLE_OPERADOR: {
        "ver_dashboard",
        "operadorregistrador",
        "ver_inventario",
        "registrar",
        "liberar",
        "solicitar_correccion",
    },
    ROLE_CONSULTA: {"ver_dashboard", "ver_inventario"},
}

CORRECCION_FIELDS = {
    "folio": "Folio",
    "fecha_ingreso": "Fecha de ingreso",
    "turno": "Turno",
    "autoridad": "Autoridad que remite",
    "deposito": "Deposito",
    "motivo": "Motivo de ingreso",
    "grua_motivo": "Motivo de grua",
    "grua_direccion": "Direccion de grua",
    "marca": "Marca",
    "modelo": "Modelo",
    "anio": "Año",
    "color": "Color",
    "placas": "Placas",
    "vin": "VIN",
    "numero_motor": "Numero de motor",
    "tipo_servicio": "Tipo de servicio",
    "combustible": "Combustible",
    "kilometraje": "Kilometraje",
    "estatus_legal": "Estatus legal",
    "oficio": "Numero de oficio",
    "fecha_oficio": "Fecha de oficio",
    "titular": "Titular",
    "observaciones": "Observaciones",
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


def _get_current_user(request):
    username = request.session.get("usuario")
    if not username:
        return None
    User = get_user_model()
    return User.objects.filter(username=username).first()


def _normalize_email(value):
    return (value or "").strip().lower()


def _email_allowed(email):
    normalized = _normalize_email(email)
    if not normalized.endswith(ALLOWED_EMAIL_DOMAIN):
        return False
    if normalized.count("@") != 1:
        return False
    local_part = normalized.split("@", 1)[0]
    return bool(local_part)


def _get_role_groups():
    groups = {}
    for role in ROLE_LABELS:
        group, _ = Group.objects.get_or_create(name=role)
        groups[role] = group
    return groups


def _coerce_field_value(field_name, raw_value):
    field = Vehiculo._meta.get_field(field_name)
    if raw_value is None:
        return None
    value = raw_value.strip()

    if field.get_internal_type() in ("IntegerField", "PositiveIntegerField", "BigIntegerField", "SmallIntegerField"):
        return int(value)
    if field.get_internal_type() == "DateField":
        parsed = parse_date(value)
        if not parsed:
            raise ValueError("Fecha invalida. Usa formato YYYY-MM-DD.")
        return parsed
    return value


def _generate_folio():
    today = timezone.localdate()
    prefix = today.strftime("FOL-%y%m%d-")
    for _ in range(25):
        serial = random.randint(100, 999)
        folio = f"{prefix}{serial}"
        if not Vehiculo.objects.filter(folio=folio).exists():
            return folio
    return f"{prefix}{random.randint(1000, 9999)}"


def _get_folio_sugerido(request):
    folio = request.session.get("folio_sugerido")
    if folio and not Vehiculo.objects.filter(folio=folio).exists():
        return folio
    folio = _generate_folio()
    request.session["folio_sugerido"] = folio
    return folio


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
                auth_login(request, user)
                request.session['usuario'] = user.get_username()
                request.session['rol'] = _get_role_for_user(user)
                return redirect('dashboard')
            error = 'Credenciales invalidas. Verifica tu usuario y contraseña.'
        else:
            error = 'Ingresa usuario y contraseña para continuar.'

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
        'can_correcciones': _has_permission(request, "gestionar_correcciones"),
        'can_usuarios': _has_permission(request, "gestionar_usuarios"),
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

    depositos = list(Deposito.objects.order_by('nombre'))
    conteos = {
        item['deposito']: item['total']
        for item in Vehiculo.objects.values('deposito').annotate(total=Count('id'))
    }
    depositos_data = [
        {
            'nombre': deposito.nombre,
            'creado_en': deposito.creado_en,
            'total': conteos.get(deposito.nombre, 0),
        }
        for deposito in depositos
    ]
    return render(
        request,
        'Vehiculos/depositos.html',
        {
            'depositos': depositos_data,
            'can_depositos': True,
        },
    )


def usuarios_view(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "gestionar_usuarios"):
        return _reject_unauthorized(request)

    User = get_user_model()
    role_groups = _get_role_groups()
    role_names = list(ROLE_LABELS.keys())
    current_user = _get_current_user(request)

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()

        if action == 'create':
            email = _normalize_email(request.POST.get('email'))
            password = request.POST.get('password') or ''
            role = (request.POST.get('role') or '').strip()

            if not email or not password or role not in ROLE_LABELS:
                messages.error(request, 'Completa correo, contraseña y rol para crear la cuenta.')
                return redirect('usuarios')

            if not _email_allowed(email):
                messages.error(request, 'Solo se permiten correos con dominio @smyt.gob.mx.')
                return redirect('usuarios')

            if User.objects.filter(username=email).exists():
                messages.error(request, 'Ya existe una cuenta registrada con ese correo.')
                return redirect('usuarios')

            user = User.objects.create_user(username=email, email=email, password=password)
            role_group = role_groups[role]
            user.groups.remove(*Group.objects.filter(name__in=role_names))
            user.groups.add(role_group)
            if role == ROLE_ADMIN:
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False
            user.save()
            messages.success(request, f'Cuenta {email} creada correctamente.')
            return redirect('usuarios')

        if action == 'delete':
            user_id = request.POST.get('user_id')
            target = User.objects.filter(id=user_id).first()
            if not target:
                messages.error(request, 'No se encontro la cuenta solicitada.')
                return redirect('usuarios')

            if current_user and target.id == current_user.id:
                messages.error(request, 'No puedes eliminar tu propia cuenta.')
                return redirect('usuarios')

            target_email = _normalize_email(target.email or target.username)
            if not _email_allowed(target_email):
                messages.error(request, 'Solo puedes eliminar cuentas con dominio @smyt.gob.mx.')
                return redirect('usuarios')

            target.delete()
            messages.success(request, f'Cuenta {target_email} eliminada correctamente.')
            return redirect('usuarios')

        messages.error(request, 'Accion invalida.')
        return redirect('usuarios')

    usuarios = []
    for user in User.objects.order_by('username'):
        display_email = (user.email or user.username or '').strip()
        if not _email_allowed(display_email):
            continue
        role = _get_role_for_user(user)
        usuarios.append(
            {
                'id': user.id,
                'email': display_email,
                'role': role,
                'role_label': ROLE_LABELS.get(role, role),
                'is_self': current_user and user.id == current_user.id,
            }
        )

    return render(
        request,
        'Vehiculos/usuarios.html',
        {
            'usuarios': usuarios,
            'role_options': [(key, ROLE_LABELS[key]) for key in ROLE_LABELS],
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
            'folio_sugerido': _get_folio_sugerido(request),
        }

    if request.method == 'POST':
        post = request.POST
        archivo = request.FILES.get('documento_pdf')

        required = [
            'fecha_ingreso',
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
            missing_labels = [CORRECCION_FIELDS.get(field, field) for field in missing]
            messages.error(
                request,
                f'Completa los campos obligatorios: {", ".join(missing_labels)}.',
            )
            return render(request, 'Vehiculos/registrar-vehiculo.html', build_context())

        field_limits = {
            'turno': 20,
            'autoridad': 120,
            'deposito': 120,
            'motivo': 280,
            'grua_motivo': 240,
            'grua_direccion': 180,
            'marca': 60,
            'modelo': 60,
            'color': 40,
            'placas': 15,
            'vin': 17,
            'numero_motor': 40,
            'tipo_servicio': 30,
            'combustible': 20,
            'oficio': 80,
            'titular': 120,
            'observaciones': 280,
        }
        for field, max_len in field_limits.items():
            value = (post.get(field) or '').strip()
            if value and len(value) > max_len:
                label = CORRECCION_FIELDS.get(field, field)
                messages.error(request, f'El campo {label} excede {max_len} caracteres.')
                return render(request, 'Vehiculos/registrar-vehiculo.html', build_context())

        vin_value = (post.get('vin') or '').strip()
        if vin_value and len(vin_value) != 17:
            messages.error(request, 'El VIN debe tener exactamente 17 caracteres.')
            return render(request, 'Vehiculos/registrar-vehiculo.html', build_context())

        folio = request.session.get("folio_sugerido") or _generate_folio()
        folio = folio.strip().upper()
        if Vehiculo.objects.filter(folio=folio).exists():
            folio = _generate_folio().strip().upper()

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

        request.session.pop("folio_sugerido", None)
        messages.success(request, f'Vehiculo {vehiculo.folio} registrado correctamente.')
        return redirect('vehiculos')

    return render(request, 'Vehiculos/registrar-vehiculo.html', build_context())


def vehiculos_list(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "ver_inventario"):
        return redirect('login')

    depositos = list(Deposito.objects.order_by('nombre').values_list('nombre', flat=True))
    deposito_query = (request.GET.get('deposito') or '').strip()

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
            'can_solicitar_correccion': _has_permission(request, "solicitar_correccion"),
            'depositos': depositos,
            'deposito_actual': deposito_query,
        },
    )


def operadorregistrador_view(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "operadorregistrador"):
        return _reject_unauthorized(request)

    def build_context():
        return {
            'depositos': list(Deposito.objects.order_by('nombre').values_list('nombre', flat=True)),
            'can_depositos': _has_permission(request, "gestionar_depositos"),
            'folio_sugerido': _get_folio_sugerido(request),
        }

    if request.method == 'POST':
        post = request.POST

        required = [
            'fecha_ingreso',
            'nombre',
            'apellidos',
            'sap',
            'direccion',
            'zona',
            'estado',
            'poblacion',
            'tipo_cuenta',
            'marca',
            'modelo',
        ]
        missing = [field for field in required if not (post.get(field) or '').strip()]
        if missing:
            missing_labels = [CORRECCION_FIELDS.get(field, field) for field in missing]
            messages.error(
                request,
                f'Completa los campos obligatorios: {", ".join(missing_labels)}.',
            )
            return render(request, 'Vehiculos/operador.html', build_context())

        field_limits = {
            'turno': 20,
            'autoridad': 120,
            'deposito': 120,
            'motivo': 280,
            'grua_motivo': 240,
            'grua_direccion': 180,
            'marca': 60,
            'modelo': 60,
            'color': 40,
            'placas': 15,
            'vin': 17,
            'numero_motor': 40,
            'tipo_servicio': 30,
            'combustible': 20,
            'oficio': 80,
            'titular': 120,
            'observaciones': 280,
        }
        for field, max_len in field_limits.items():
            value = (post.get(field) or '').strip()
            if value and len(value) > max_len:
                label = CORRECCION_FIELDS.get(field, field)
                messages.error(request, f'El campo {label} excede {max_len} caracteres.')
                return render(request, 'Vehiculos/operador.html', build_context())

        vin_value = (post.get('vin') or '').strip()
        if vin_value and len(vin_value) != 17:
            messages.error(request, 'El VIN debe tener exactamente 17 caracteres.')
            return render(request, 'Vehiculos/operador.html', build_context())

        messages.success(request, 'Registro de cliente recibido correctamente.')
        return redirect('operador')

    return render(request, 'Vehiculos/operador.html', build_context())


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
    auth_logout(request)
    request.session.flush()
    return redirect('login')


def solicitar_correccion(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "solicitar_correccion"):
        return _reject_unauthorized(request)

    folio_query = (request.GET.get('folio') or '').strip().upper()
    vehiculo = Vehiculo.objects.filter(folio=folio_query).first() if folio_query else None

    if request.method == 'POST':
        folio = (request.POST.get('folio') or '').strip().upper()
        campo = (request.POST.get('campo') or '').strip()
        valor_nuevo = (request.POST.get('valor_nuevo') or '').strip()
        motivo = (request.POST.get('motivo') or '').strip()

        vehiculo = Vehiculo.objects.filter(folio=folio).first()
        if not vehiculo:
            messages.error(request, 'No se encontro el vehiculo solicitado.')
            return redirect('solicitar_correccion')

        if campo not in CORRECCION_FIELDS:
            messages.error(request, 'Selecciona un campo valido para corregir.')
            return redirect('solicitar_correccion')

        if not valor_nuevo:
            messages.error(request, 'Ingresa el valor correcto.')
            return redirect('solicitar_correccion')

        field = Vehiculo._meta.get_field(campo)
        if field.choices:
            valid_choices = [choice[0] for choice in field.choices]
            if valor_nuevo not in valid_choices:
                messages.error(request, 'El valor no es valido para el campo seleccionado.')
                return redirect('solicitar_correccion')

        try:
            _coerce_field_value(campo, valor_nuevo)
        except Exception:
            messages.error(request, 'El valor no tiene el formato correcto para ese campo.')
            return redirect('solicitar_correccion')

        SolicitudCorreccion.objects.create(
            vehiculo=vehiculo,
            solicitante=_get_current_user(request),
            campo=campo,
            valor_nuevo=valor_nuevo,
            motivo=motivo,
        )

        messages.success(request, 'Solicitud enviada al administrador.')
        return redirect('vehiculos')

    return render(
        request,
        'Vehiculos/solicitar-correccion.html',
        {
            'vehiculo': vehiculo,
            'campos': CORRECCION_FIELDS,
        },
    )


def solicitudes_correccion(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not _has_permission(request, "gestionar_correcciones"):
        return _reject_unauthorized(request)

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        solicitud_id = request.POST.get('solicitud_id')
        solicitud = SolicitudCorreccion.objects.select_related('vehiculo').filter(id=solicitud_id).first()

        if not solicitud:
            messages.error(request, 'No se encontro la solicitud.')
            return redirect('solicitudes_correccion')

        if solicitud.estatus != SolicitudCorreccion.ESTATUS_PENDIENTE:
            messages.error(request, 'La solicitud ya fue atendida.')
            return redirect('solicitudes_correccion')

        if action == 'rechazar':
            solicitud.estatus = SolicitudCorreccion.ESTATUS_RECHAZADA
            solicitud.resuelto_en = timezone.now()
            solicitud.resuelto_por = _get_current_user(request)
            solicitud.save(update_fields=['estatus', 'resuelto_en', 'resuelto_por'])
            messages.info(request, 'Solicitud rechazada.')
            return redirect('solicitudes_correccion')

        if action == 'aprobar':
            try:
                nuevo_valor = _coerce_field_value(solicitud.campo, solicitud.valor_nuevo)
            except Exception:
                messages.error(request, 'No se pudo aplicar el cambio por formato invalido.')
                return redirect('solicitudes_correccion')

            vehiculo = solicitud.vehiculo
            if solicitud.campo == 'estatus_legal':
                if nuevo_valor == Vehiculo.ESTATUS_LIBERADO:
                    vehiculo.marcar_liberado()
                else:
                    vehiculo.estatus_legal = nuevo_valor
                    vehiculo.liberado = False
                    vehiculo.fecha_liberacion = None
            else:
                setattr(vehiculo, solicitud.campo, nuevo_valor)
            vehiculo.save()

            solicitud.estatus = SolicitudCorreccion.ESTATUS_APROBADA
            solicitud.resuelto_en = timezone.now()
            solicitud.resuelto_por = _get_current_user(request)
            solicitud.save(update_fields=['estatus', 'resuelto_en', 'resuelto_por'])

            messages.success(request, 'Solicitud aplicada correctamente.')
            return redirect('solicitudes_correccion')

        messages.error(request, 'Accion invalida.')
        return redirect('solicitudes_correccion')

    solicitudes = list(
        SolicitudCorreccion.objects.select_related('vehiculo', 'solicitante').order_by('-creado_en')
    )
    for solicitud in solicitudes:
        solicitud.campo_label = CORRECCION_FIELDS.get(solicitud.campo, solicitud.campo)
    return render(
        request,
        'Vehiculos/solicitudes-correccion.html',
        {
            'solicitudes': solicitudes,
        },
    )
