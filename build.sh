#/usr/bin/env bash
# Salir en caso de error
set -o errexit

#Modifique esta linea segun sea necesario para su gestor de paquetes (pip, pip3, pip3.8, etc)
pip install -r requirements.txt

#convetir el script a ejecutable
python manage.py collectstatic --no-input

#Aplicar las migraciones de base de datos pendientes
python manage.py migrate