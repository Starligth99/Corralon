import os
import secrets
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


def _random_password(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


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

        email_defaults = {
            "ADMIN_EMAIL": "miguelromeroalcantara@smyt.gob.mx",
            "OPERADOR_EMAIL": "gamalielalexis@smyt.gob.mx",
            "CONSULTA_EMAIL": "camilalunatepox@symt.gob.mx",
        }

        def get_email(key):
            return os.getenv(key, email_defaults[key])

        def get_password(key):
            value = os.getenv(key)
            if value:
                return value, False
            generated = _random_password()
            return generated, True

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

        admin_email = get_email("ADMIN_EMAIL")
        admin_password, admin_generated = get_password("ADMIN_PASSWORD")
        oper_email = get_email("OPERADOR_EMAIL")
        oper_password, oper_generated = get_password("OPERADOR_PASSWORD")
        cons_email = get_email("CONSULTA_EMAIL")
        cons_password, cons_generated = get_password("CONSULTA_PASSWORD")

        created_admin, pw_admin = ensure_user(admin_email, admin_password, "administrador", is_admin=True)
        created_oper, pw_oper = ensure_user(oper_email, oper_password, "operador", is_admin=False)
        created_cons, pw_cons = ensure_user(cons_email, cons_password, "consulta", is_admin=False)

        self.stdout.write(self.style.SUCCESS("Usuarios base listos:"))
        self.stdout.write(f"Administrador: {admin_email} (password {'creada' if pw_admin else 'existente'})")
        self.stdout.write(f"Operador: {oper_email} (password {'creada' if pw_oper else 'existente'})")
        self.stdout.write(f"Consulta: {cons_email} (password {'creada' if pw_cons else 'existente'})")

        # Warn if passwords were auto-generated (env vars not set)
        for label, generated, pw in [
            ("ADMIN_PASSWORD", admin_generated, admin_password),
            ("OPERADOR_PASSWORD", oper_generated, oper_password),
            ("CONSULTA_PASSWORD", cons_generated, cons_password),
        ]:
            if generated:
                self.stdout.write(
                    self.style.WARNING(
                        f"WARNING: {label} env var not set. "
                        f"Generated random password: {pw}  -- save it now!"
                    )
                )

        if created_admin or created_oper or created_cons:
            self.stdout.write(self.style.SUCCESS("Usuarios creados o actualizados correctamente."))
