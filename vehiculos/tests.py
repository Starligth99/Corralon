from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

User = get_user_model()

ROLE_ADMIN = "administrador"


class CreateUserAndLoginTest(TestCase):
    """Create a new user via the /usuarios/ page, then verify they can log in."""

    def setUp(self):
        # Create the admin group and an admin user who can manage usuarios.
        admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        self.admin_email = "admin@smyt.gob.mx"
        self.admin_password = "Adm1n_s3cure!"
        self.admin = User.objects.create_user(
            username=self.admin_email,
            email=self.admin_email,
            password=self.admin_password,
            is_staff=True,
            is_superuser=True,
        )
        self.admin.groups.add(admin_group)

        # Log in as admin and store the session role so _is_logged_in passes.
        self.client.post(
            "/",
            {"usuario": self.admin_email, "password": self.admin_password},
        )

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def _create_user_via_page(self, email, password, role):
        """POST to /usuarios/ with action=create and return the response."""
        return self.client.post(
            "/usuarios/",
            {
                "action": "create",
                "email": email,
                "password": password,
                "role": role,
            },
        )

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------
    def test_create_user_and_login(self):
        """Full flow: admin creates a user, then that user logs in successfully."""

        new_email = "nuevousuario@smyt.gob.mx"
        new_password = "Nu3v0_Pass!"
        new_role = "operador"

        # 1. Admin creates the new user via the usuarios page.
        response = self._create_user_via_page(new_email, new_password, new_role)
        self.assertIn(response.status_code, (200, 302))

        # Verify the user record exists in the database.
        self.assertTrue(
            User.objects.filter(username=new_email).exists(),
            "The new user should exist in the database after creation.",
        )

        # Verify the user was assigned the correct role group.
        new_user = User.objects.get(username=new_email)
        self.assertTrue(
            new_user.groups.filter(name=new_role).exists(),
            "The new user should belong to the 'operador' group.",
        )

        # 2. Log out the admin.
        self.client.get("/logout/")

        # 3. Log in as the newly created user.
        login_response = self.client.post(
            "/",
            {"usuario": new_email, "password": new_password},
        )

        # A successful login redirects (302) to the dashboard.
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.url, "/dashboard/")

        # 4. Verify the session contains the correct user and role.
        self.assertEqual(self.client.session["usuario"], new_email)
        self.assertEqual(self.client.session["rol"], new_role)

        # 5. The dashboard should be accessible (200) for the new user.
        dashboard_response = self.client.get("/dashboard/")
        self.assertEqual(dashboard_response.status_code, 200)

    def test_created_user_cannot_login_with_wrong_password(self):
        """A user created via /usuarios/ cannot log in with an incorrect password."""

        email = "wrongpass@smyt.gob.mx"
        password = "C0rr3ct_Pass!"

        self._create_user_via_page(email, password, "consulta")
        self.client.get("/logout/")

        login_response = self.client.post(
            "/",
            {"usuario": email, "password": "WRONG_password"},
        )

        # Should NOT redirect — stays on the login page with an error.
        self.assertEqual(login_response.status_code, 200)
        self.assertNotIn("usuario", self.client.session)

    def test_duplicate_email_is_rejected(self):
        """Creating a user with an email that already exists is rejected."""

        email = "duplicado@smyt.gob.mx"
        password = "Dup1_Pass!"

        self._create_user_via_page(email, password, "operador")

        # Attempt to create the same user again.
        response = self._create_user_via_page(email, password, "operador")
        self.assertIn(response.status_code, (200, 302))

        # Only one record should exist.
        self.assertEqual(User.objects.filter(username=email).count(), 1)

    def test_non_allowed_domain_is_rejected(self):
        """An email with a domain other than @smyt.gob.mx is rejected."""

        response = self._create_user_via_page(
            "user@gmail.com", "Some_Pass1!", "operador"
        )
        self.assertIn(response.status_code, (200, 302))
        self.assertFalse(User.objects.filter(username="user@gmail.com").exists())
