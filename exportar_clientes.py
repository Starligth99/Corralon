import os
import django
import csv

# 1. Configuración del entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Corralon.settings')
django.setup()

from vehiculos.models import Cliente

nombre_csv = 'reporte_detallado_clientes.csv'

try:
    with open(nombre_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # CABECERAS DESGLOSADAS
        writer.writerow([
            'CODIGO SAP', 'NOMBRE', 'TIPO DE CUENTA', 
            'LATITUD', 'LONGITUD', 'LISTA DE PRECIOS',
            'CALLE / REFERENCIA', 'POBLACION / MUNICIPIO', 'ESTADO', 
            'CODIGO POSTAL', 'PAIS', 'ZONA', 
            'FECHA REGISTRO', 'REGISTRADO POR (NOMBRE)', 'REGISTRADO POR (EMAIL)'
        ])
        
        clientes = Cliente.objects.all()
        
        for c in clientes:
            # --- LÓGICA DEL REGISTRADOR ---
            # Intentamos obtener los datos del usuario que registró
            nombre_usuario = "Sistema"
            email_usuario = "No asignado"
            
            # Ajustamos al nombre de tu campo (registrado_por)
            usuario = getattr(c, 'registrado_por', None)
            if usuario:
                nombre_usuario = f"{usuario.first_name} {usuario.last_name}".strip() or usuario.username
                email_usuario = usuario.email

            # --- LÓGICA DE DIRECCIÓN DESGLOSADA ---
            # Si tu modelo ya tiene campos separados, los usamos. 
            # Si no, el script los dejará en blanco para que tú los completes o los mapees.
            calle = getattr(c, 'calle', getattr(c, 'direccion', '-'))
            poblacion = getattr(c, 'poblacion', getattr(c, 'municipio', '-'))
            estado = getattr(c, 'estado', 'Tlaxcala') # Default basado en tu zona
            cp = getattr(c, 'codigo_postal', '-')
            pais = getattr(c, 'pais', 'México')

            writer.writerow([
                getattr(c, 'sap', '-'),
                getattr(c, 'nombre', '-'),
                getattr(c, 'tipo_filtro', '-'),
                getattr(c, 'latitud', '-'),
                getattr(c, 'longitud', '-'),
                getattr(c, 'lista_precios', 'DEFAULT'),
                calle,
                poblacion,
                estado,
                cp,
                pais,
                getattr(c, 'zona', '-'),
                c.fecha_registro.strftime('%d-%b-%Y') if hasattr(c, 'fecha_registro') and c.fecha_registro else '-',
                nombre_usuario,
                email_usuario
            ])
            
    print(f"✅ Reporte generado: {clientes.count()} clientes exportados.")
    print(f"📂 Archivo: C:\\Corralon\\{nombre_csv}")

except Exception as e:
    print(f"❌ Error: {e}")