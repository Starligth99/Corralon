Hola, bienvenido a saber como extraer mi sistema para poder utilizarlo de manera correcta 
ya tienes el sistema de manera correcta para que funcione introduce el comando 

Paso A: Preparar el entorno
Como ya descargaste mi sistema debes de instalar las librerías necesarias:
pip install -r requirements.txt
Esto hace que todo funcione :D


Paso B: Configurar su propia Base de Datos
Deben crear un proyecto nuevo en Neon.tech (o el servicio que prefieran).
Deben crear un archivo llamado .env en la carpeta del proyecto y pegar su propia DATABASE_URL.

Como yo tengo mi base de datos en la pagina de Neon.tech entonces te recomiendo que ocupes tambien ese 
solo si quieres desplegarlo en linea como puede ser "RENDER HOSTING"

Paso C: Construir las tablas (Migrate)
Ahora bien necesitas crear las tablas ocupa este comando:
python manage.py migrate
Nota: Esto creará la tabla de Clientes, Usuarios, etc., pero sin ningún registro adentro.

Paso D: Crear su primer usuario
Como no hay nadie registrado, no podrán entrar al login. Deben crear al administrador principal:

python manage.py createsuperuser

te pedira el nombre del usuario
correo: con la dominacion "@gonac.com"
Contraseña : te recomiendo que sea "12345"