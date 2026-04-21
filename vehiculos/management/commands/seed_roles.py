import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from vehiculos.models import PerfilUsuario


class Command(BaseCommand):
    help = "Crea los grupos y usuarios base (admin_master, administrador, operador, consulta)."

    def handle(self, *args, **options):
        roles = [
            "admin_master",
            "administrador",
            "operador",
            "consulta",
        ]

        groups = {}
        for role in roles:
            group, _ = Group.objects.get_or_create(name=role)
            groups[role] = group

        defaults = {
            "ADMIN_MASTER_EMAIL": "adminmaster@gonac.com",
            "ADMIN_MASTER_PASSWORD": "12345",
            "ADMIN_EMAIL": "miguelromeroalcantara@gonac.com",
            "ADMIN_PASSWORD": "12345",
            "OPERADOR_EMAIL": "gamalielalexis@gonac.com",
            "OPERADOR_PASSWORD": "12345",
            "CONSULTA_EMAIL": "camilalunatepox@gonac.com",
            "CONSULTA_PASSWORD": "12345",
        }

        def get_env(key):
            return os.getenv(key, defaults[key])

        User = get_user_model()

        role_prefixes = {
            "admin_master": PerfilUsuario.PREFIJO_ADMIN_MASTER,
            "administrador": PerfilUsuario.PREFIJO_ADMINISTRADOR,
            "operador": PerfilUsuario.PREFIJO_OPERADOR,
            "consulta": PerfilUsuario.PREFIJO_CONSULTA,
        }

        def next_numero_interno(prefix: str) -> str:
            existing = (
                PerfilUsuario.objects.filter(numero_interno__startswith=f"{prefix}-")
                .order_by("-numero_interno")
                .values_list("numero_interno", flat=True)
                .first()
            )
            if existing:
                try:
                    last = int(existing.split("-")[-1])
                except ValueError:
                    last = 0
            else:
                last = 0
            return f"{prefix}-{last + 1:05d}"

        @transaction.atomic
        def ensure_user(email, password, role, is_admin=False):
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email},
            )
            password_set = False
            if created or not user.has_usable_password():
                user.set_password(password)
                password_set = True
            user.is_staff = bool(is_admin)
            user.is_superuser = bool(is_admin)
            user.email = email
            user.save()
            if role in groups:
                user.groups.add(groups[role])
            perfil, perfil_created = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={"numero_interno": next_numero_interno(role_prefixes[role])},
            )
            return created, password_set, perfil.numero_interno

        admin_master_email = get_env("ADMIN_MASTER_EMAIL")
        admin_master_password = get_env("ADMIN_MASTER_PASSWORD")
        admin_email = get_env("ADMIN_EMAIL")
        admin_password = get_env("ADMIN_PASSWORD")
        oper_email = get_env("OPERADOR_EMAIL")
        oper_password = get_env("OPERADOR_PASSWORD")
        cons_email = get_env("CONSULTA_EMAIL")
        cons_password = get_env("CONSULTA_PASSWORD")

        created_ams, pw_ams, id_ams = ensure_user(admin_master_email, admin_master_password, "admin_master", is_admin=True)
        created_admin, pw_admin, id_admin = ensure_user(admin_email, admin_password, "administrador", is_admin=True)
        created_oper, pw_oper, id_oper = ensure_user(oper_email, oper_password, "operador", is_admin=False)
        created_cons, pw_cons, id_cons = ensure_user(cons_email, cons_password, "consulta", is_admin=False)

        self.stdout.write(self.style.SUCCESS("Usuarios base listos:"))
        self.stdout.write(f"Admin Master: {admin_master_email} [{id_ams}] (password {'creada' if pw_ams else 'existente'})")
        self.stdout.write(f"Administrador: {admin_email} [{id_admin}] (password {'creada' if pw_admin else 'existente'})")
        self.stdout.write(f"Operador: {oper_email} [{id_oper}] (password {'creada' if pw_oper else 'existente'})")
        self.stdout.write(f"Consulta: {cons_email} [{id_cons}] (password {'creada' if pw_cons else 'existente'})")

        if created_ams or created_admin or created_oper or created_cons:
            self.stdout.write(self.style.SUCCESS("Usuarios creados o actualizados correctamente."))
