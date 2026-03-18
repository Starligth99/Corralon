import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea los grupos y usuarios base (administrador, operador, consulta)."

    def handle(self, *args, **options):
        roles = [
            "administrador",
            "operador",
            "consulta",
        ]

        groups = {}
        for role in roles:
            group, _ = Group.objects.get_or_create(name=role)
            groups[role] = group

        defaults = {
            "ADMIN_EMAIL": "miguelromeroalcantara@smyt.gob.mx",
            "ADMIN_PASSWORD": "12345",
            "OPERADOR_EMAIL": "gamalielalexis@smyt.gob.mx",
            "OPERADOR_PASSWORD": "12345",
            "CONSULTA_EMAIL": "camilalunatepox@symt.gob.mx",
            "CONSULTA_PASSWORD": "12345",
        }

        def get_env(key):
            return os.getenv(key, defaults[key])

        User = get_user_model()

        def ensure_user(email, password, role, is_admin=False):
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email},
            )
            password_set = False
            if created or not user.has_usable_password():
                user.set_password(password)
                password_set = True
            if is_admin:
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False
            user.email = email
            user.save()
            if role in groups:
                user.groups.add(groups[role])
            return created, password_set

        admin_email = get_env("ADMIN_EMAIL")
        admin_password = get_env("ADMIN_PASSWORD")
        oper_email = get_env("OPERADOR_EMAIL")
        oper_password = get_env("OPERADOR_PASSWORD")
        cons_email = get_env("CONSULTA_EMAIL")
        cons_password = get_env("CONSULTA_PASSWORD")

        created_admin, pw_admin = ensure_user(admin_email, admin_password, "administrador", is_admin=True)
        created_oper, pw_oper = ensure_user(oper_email, oper_password, "operador", is_admin=False)
        created_cons, pw_cons = ensure_user(cons_email, cons_password, "consulta", is_admin=False)

        self.stdout.write(self.style.SUCCESS("Usuarios base listos:"))
        self.stdout.write(f"Administrador: {admin_email} (password {'creada' if pw_admin else 'existente'})")
        self.stdout.write(f"Operador: {oper_email} (password {'creada' if pw_oper else 'existente'})")
        self.stdout.write(f"Consulta: {cons_email} (password {'creada' if pw_cons else 'existente'})")

        if created_admin or created_oper or created_cons:
            self.stdout.write(self.style.SUCCESS("Usuarios creados o actualizados correctamente."))
