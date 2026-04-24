from django.conf import settings
from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    TIPO_DIRECTO = "DIRECTO"
    TIPO_PROSPECTO = "PROSPECTO"
    TIPO_CHOICES = [
        (TIPO_DIRECTO, "Directo"),
        (TIPO_PROSPECTO, "Prospecto"),
    ]

    sap = models.CharField(max_length=30, unique=True, db_index=True)
    nombre = models.CharField(max_length=120)
    tipo_cuenta = models.CharField(max_length=20, choices=TIPO_CHOICES)
    lista_precios = models.CharField(max_length=40, blank=True)

    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    direccion = models.CharField(max_length=180, blank=True)
    zona = models.CharField(max_length=60, blank=True)
    estado = models.CharField(max_length=60, blank=True)
    poblacion = models.CharField(max_length=60, blank=True)

    fecha_registro = models.DateField()
    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clientes_registrados",
        null=True,
        blank=True,
    )

    dias_maximos_entrega = models.PositiveIntegerField(default=0)
    pedido_excede_limite_credito = models.BooleanField(default=False)
    bloquear_cliente_factura_vencida = models.BooleanField(default=False)
    bloqueo_venta_documento_pendiente = models.BooleanField(default=False)
    orden_compra_adquirida = models.BooleanField(default=False)
    permitir_devolucion = models.BooleanField(default=True)
    holgura_dto_pp = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    bloqueo_venta = models.BooleanField(default=False)
    bloqueo_cheques_pendientes = models.BooleanField(default=False)
    tomar_inventario = models.BooleanField(default=False)
    modificar_condicion_pago = models.BooleanField(default=False)
    dias_para_fecha_entrega = models.PositiveIntegerField(default=0)
    orden_compra_automatico = models.BooleanField(default=False)
    edicion_operador_usada = models.BooleanField(default=False)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_registro", "-id"]

    def __str__(self):
        return f"{self.sap} - {self.nombre}"


class PerfilUsuario(models.Model):
    PREFIJO_ADMIN_MASTER = "AMS"
    PREFIJO_ADMINISTRADOR = "ADM"
    PREFIJO_OPERADOR = "OPE"
    PREFIJO_PROMOTOR = "PRO"
    PREFIJO_CONSULTA = "CON"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    numero_interno = models.CharField(max_length=20, unique=True, editable=False)
    nombre_completo = models.CharField(max_length=120, blank=True)
    rfc = models.CharField(max_length=13, blank=True)
    rfc_pdf = models.FileField(upload_to="usuarios/rfc/", null=True, blank=True)
    ine_pdf = models.FileField(upload_to="usuarios/ine/", null=True, blank=True)
    comprobante_domicilio_pdf = models.FileField(
        upload_to="usuarios/comprobante_domicilio/",
        null=True,
        blank=True,
    )
    direccion = models.CharField(max_length=180, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    operador_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotores_asignados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["numero_interno"]

    def __str__(self):
        return f"{self.numero_interno} - {self.user.get_username()}"


class Deposito(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Vehiculo(models.Model):
    ESTATUS_EN_CUSTODIA = "En custodia"
    ESTATUS_DECOMISADO = "Decomisado"
    ESTATUS_SINIESTRADO = "Siniestrado"
    ESTATUS_ABANDONADO = "Abandonado"
    ESTATUS_LIBERADO = "Liberado"

    ESTATUS_CHOICES = [
        (ESTATUS_EN_CUSTODIA, "En custodia"),
        (ESTATUS_DECOMISADO, "Decomisado"),
        (ESTATUS_SINIESTRADO, "Siniestrado"),
        (ESTATUS_ABANDONADO, "Abandonado"),
        (ESTATUS_LIBERADO, "Liberado"),
    ]

    folio = models.CharField(max_length=30, unique=True)
    fecha_ingreso = models.DateField()
    turno = models.CharField(max_length=20, blank=True)
    autoridad = models.CharField(max_length=120)
    deposito = models.CharField(max_length=120)
    motivo = models.TextField(blank=True)
    grua_motivo = models.TextField(blank=True)
    grua_direccion = models.CharField(max_length=180, blank=True)

    marca = models.CharField(max_length=60)
    modelo = models.CharField(max_length=60)
    anio = models.PositiveIntegerField()
    color = models.CharField(max_length=40, blank=True)
    placas = models.CharField(max_length=15, db_index=True)
    vin = models.CharField(max_length=17, db_index=True)
    numero_motor = models.CharField(max_length=40)
    tipo_servicio = models.CharField(max_length=30)
    combustible = models.CharField(max_length=20, blank=True)
    kilometraje = models.PositiveIntegerField(default=0)

    estatus_legal = models.CharField(
        max_length=30, choices=ESTATUS_CHOICES, default=ESTATUS_EN_CUSTODIA
    )
    oficio = models.CharField(max_length=80, blank=True)
    fecha_oficio = models.DateField(null=True, blank=True)
    titular = models.CharField(max_length=120, blank=True)
    observaciones = models.TextField(blank=True)
    documento_nombre = models.CharField(max_length=180, blank=True)

    liberado = models.BooleanField(default=False)
    fecha_liberacion = models.DateTimeField(null=True, blank=True)
    autoriza_liberacion = models.CharField(max_length=120, blank=True)
    liberacion_observaciones = models.TextField(blank=True)
    aceite_drenado = models.BooleanField(default=False)
    combustible_drenado = models.BooleanField(default=False)
    anticongelante_drenado = models.BooleanField(default=False)
    sin_objetos_pendientes = models.BooleanField(default=False)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_ingreso", "-id"]

    def __str__(self):
        return f"{self.folio} - {self.marca} {self.modelo}"

    def marcar_liberado(self):
        self.estatus_legal = self.ESTATUS_LIBERADO
        self.liberado = True
        self.fecha_liberacion = timezone.now()


class SolicitudCorreccion(models.Model):
    ESTATUS_PENDIENTE = "Pendiente"
    ESTATUS_APROBADA = "Aprobada"
    ESTATUS_RECHAZADA = "Rechazada"

    ESTATUS_CHOICES = [
        (ESTATUS_PENDIENTE, "Pendiente"),
        (ESTATUS_APROBADA, "Aprobada"),
        (ESTATUS_RECHAZADA, "Rechazada"),
    ]

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="correcciones")
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correcciones_solicitadas",
    )
    campo = models.CharField(max_length=60)
    valor_nuevo = models.TextField()
    motivo = models.TextField()
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default=ESTATUS_PENDIENTE)
    creado_en = models.DateTimeField(auto_now_add=True)
    resuelto_en = models.DateTimeField(null=True, blank=True)
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correcciones_resueltas",
    )

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.vehiculo.folio} - {self.campo} ({self.estatus})"


class SolicitudCorreccionCliente(models.Model):
    ESTATUS_PENDIENTE = "Pendiente"
    ESTATUS_APROBADA = "Aprobada"
    ESTATUS_RECHAZADA = "Rechazada"

    ESTATUS_CHOICES = [
        (ESTATUS_PENDIENTE, "Pendiente"),
        (ESTATUS_APROBADA, "Aprobada"),
        (ESTATUS_RECHAZADA, "Rechazada"),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="correcciones",
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correcciones_clientes_solicitadas",
    )
    campo = models.CharField(max_length=60)
    valor_nuevo = models.TextField()
    motivo = models.TextField()
    estatus = models.CharField(
        max_length=20,
        choices=ESTATUS_CHOICES,
        default=ESTATUS_PENDIENTE,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    resuelto_en = models.DateTimeField(null=True, blank=True)
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correcciones_clientes_resueltas",
    )

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.cliente.sap} - {self.campo} ({self.estatus})"
