# TODO - Fase 1 (Editar cliente solo 1 vez para operador)

- [x] Agregar campo persistente en `Cliente` para bloquear segunda edición de operador.
- [x] Crear migración para el nuevo campo.
- [x] Ajustar lógica en `views.py` (`editar_cliente`) para:
  - [x] Validar que operador solo edite sus clientes.
  - [x] Permitir únicamente campos autorizados.
  - [x] Bloquear si ya usó su edición única.
  - [x] Marcar edición única como consumida cuando aplique.
- [x] Corregir markup del botón "Editar" en `clientes.html` (sin HTML inválido).
- [x] Corregir `editar_cliente.html` para usar endpoint correcto y UI acorde a edición directa.
- [x] Verificación básica de consistencia (rutas/template/view).
