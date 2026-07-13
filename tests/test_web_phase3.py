"""Phase-3 web tests: settings CRUD (clinic/doctors/services/users), backup UI,
role guard, password hashing, and admin bootstrap."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from clinic.domain import (
    clinic_info_service,
    doctor_service,
    service_service,
    user_service,
)
from clinic.web.app import create_app
from clinic.web.security import hash_password, verify_password

ADMIN_USER = "admin"
ADMIN_PASSWORD = "clinic"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def admin_client() -> TestClient:
    with TestClient(create_app()) as c:
        resp = c.post(
            "/login",
            data={"username": ADMIN_USER, "password": ADMIN_PASSWORD},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        yield c


@pytest.fixture()
def staff_client() -> TestClient:
    """Log in as a freshly-created ``staff`` user (no admin rights)."""
    with TestClient(create_app()) as c:
        # Provision the staff user via the admin session first, then re-login.
        admin_resp = c.post(
            "/login",
            data={"username": ADMIN_USER, "password": ADMIN_PASSWORD},
            follow_redirects=False,
        )
        assert admin_resp.status_code == 303
        c.post(
            "/settings/users/new",
            data={
                "username": "nurse",
                "password": "secret4",
                "role": "staff",
                "full_name": "Ismoilova Feruza",
            },
            follow_redirects=False,
        )
        c.get("/logout", follow_redirects=False)
        # Now log in as nurse
        resp = c.post(
            "/login",
            data={"username": "nurse", "password": "secret4"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        yield c


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_password_hash_verifies_correctly() -> None:
    h = hash_password("secret")
    assert h.startswith("pbkdf2_sha256$")
    assert verify_password("secret", h)
    assert not verify_password("wrong", h)


def test_password_hash_is_salted_random() -> None:
    a = hash_password("same")
    b = hash_password("same")
    assert a != b  # different salts
    assert verify_password("same", a)
    assert verify_password("same", b)


# ---------------------------------------------------------------------------
# Bootstrap admin
# ---------------------------------------------------------------------------


def test_bootstrap_admin_created_on_first_boot(admin_client: TestClient) -> None:
    users = user_service.list_all()
    admins = [u for u in users if u.role == "admin"]
    assert any(u.username == ADMIN_USER for u in admins)


def test_login_wrong_password_after_bootstrap(admin_client: TestClient) -> None:
    admin_client.get("/logout", follow_redirects=False)
    resp = admin_client.post(
        "/login",
        data={"username": ADMIN_USER, "password": "nope"},
        follow_redirects=False,
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Role guard
# ---------------------------------------------------------------------------


def test_staff_cannot_access_settings(staff_client: TestClient) -> None:
    resp = staff_client.get("/settings/users", follow_redirects=False)
    assert resp.status_code == 403


def test_staff_can_access_home_and_reception(staff_client: TestClient) -> None:
    assert staff_client.get("/").status_code == 200
    assert staff_client.get("/reception/new").status_code == 200
    assert staff_client.get("/patients").status_code == 200


def test_admin_can_access_settings(admin_client: TestClient) -> None:
    for path in ("/settings/clinic", "/settings/doctors", "/settings/services",
                 "/settings/users", "/settings/backup"):
        resp = admin_client.get(path)
        assert resp.status_code == 200, f"{path} → {resp.status_code}"


# ---------------------------------------------------------------------------
# Clinic profile
# ---------------------------------------------------------------------------


def test_clinic_profile_saves(admin_client: TestClient) -> None:
    resp = admin_client.post(
        "/settings/clinic",
        data={
            "name_uz": "LOR klinikasi",
            "name_ru": "ЛОР клиника",
            "address_uz": "Sergeli",
            "address_ru": "Сергели",
            "phone": "+998 93 391 91 64",
            "logo_path": "",
            "language": "uz",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    info = clinic_info_service.load()
    assert info.name_uz == "LOR klinikasi"
    assert info.name_ru == "ЛОР клиника"
    assert info.phone == "+998 93 391 91 64"


# ---------------------------------------------------------------------------
# Doctors CRUD
# ---------------------------------------------------------------------------


def test_doctor_lifecycle(admin_client: TestClient) -> None:
    # Create
    resp = admin_client.post(
        "/settings/doctors/new",
        data={"full_name": "Karimov Ali", "phone": "+998901234567"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    doctors = doctor_service.list_all()
    assert any(d.full_name == "Karimov Ali" for d in doctors)
    d = next(x for x in doctors if x.full_name == "Karimov Ali")
    assert d.is_active

    # Edit
    resp = admin_client.post(
        f"/settings/doctors/{d.id}/edit",
        data={"full_name": "Karimov Ali Valiyevich", "phone": "+998901234567"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert doctor_service.get(d.id).full_name == "Karimov Ali Valiyevich"

    # Toggle archive
    resp = admin_client.post(f"/settings/doctors/{d.id}/toggle", follow_redirects=False)
    assert resp.status_code == 303
    assert doctor_service.get(d.id).is_active is False

    # Toggle back
    admin_client.post(f"/settings/doctors/{d.id}/toggle", follow_redirects=False)
    assert doctor_service.get(d.id).is_active is True


# ---------------------------------------------------------------------------
# Services CRUD
# ---------------------------------------------------------------------------


def test_service_lifecycle(admin_client: TestClient) -> None:
    resp = admin_client.post(
        "/settings/services/new",
        data={"name_uz": "Konsultatsiya", "name_ru": "Консультация", "price": "100000"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    services = service_service.list_all()
    s = next(x for x in services if x.name_uz == "Konsultatsiya")
    assert s.is_active

    resp = admin_client.post(
        f"/settings/services/{s.id}/edit",
        data={"name_uz": "Konsultatsiya", "name_ru": "Консультация", "price": "120000"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert int(service_service.get(s.id).price) == 120000

    admin_client.post(f"/settings/services/{s.id}/toggle", follow_redirects=False)
    assert service_service.get(s.id).is_active is False


# ---------------------------------------------------------------------------
# Users CRUD
# ---------------------------------------------------------------------------


def test_user_lifecycle(admin_client: TestClient) -> None:
    # Create staff user
    resp = admin_client.post(
        "/settings/users/new",
        data={"username": "recepcia", "password": "pass1", "role": "staff",
              "full_name": "Registratura"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    u = user_service.get_by_username("recepcia")
    assert u is not None and u.role == "staff"

    # Update role
    resp = admin_client.post(
        f"/settings/users/{u.id}/edit",
        data={"role": "admin", "full_name": "Bosh registratura"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    updated = user_service.get(u.id)
    assert updated.role == "admin"
    assert updated.full_name == "Bosh registratura"

    # Reset password
    resp = admin_client.post(
        f"/settings/users/{u.id}/reset-password",
        data={"password": "newpass"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    # New password works
    assert user_service.authenticate("recepcia", "newpass") is not None
    assert user_service.authenticate("recepcia", "pass1") is None


def test_last_admin_cannot_be_deactivated(admin_client: TestClient) -> None:
    admin = user_service.get_by_username(ADMIN_USER)
    assert admin is not None
    resp = admin_client.post(
        f"/settings/users/{admin.id}/toggle",
        follow_redirects=False,
    )
    assert resp.status_code == 303  # flash-and-return, no error
    still = user_service.get(admin.id)
    assert still is not None and still.is_active is True


def test_second_admin_can_be_deactivated(admin_client: TestClient) -> None:
    # Create a second admin
    admin_client.post(
        "/settings/users/new",
        data={"username": "admin2", "password": "pass2", "role": "admin", "full_name": ""},
        follow_redirects=False,
    )
    admin2 = user_service.get_by_username("admin2")
    assert admin2 is not None
    resp = admin_client.post(f"/settings/users/{admin2.id}/toggle", follow_redirects=False)
    assert resp.status_code == 303
    assert user_service.get(admin2.id).is_active is False


def test_duplicate_username_is_rejected(admin_client: TestClient) -> None:
    # First succeeds
    admin_client.post(
        "/settings/users/new",
        data={"username": "duplicate", "password": "pass", "role": "staff",
              "full_name": ""},
        follow_redirects=False,
    )
    # Second attempt for the same name flashes an error but returns 303
    resp = admin_client.post(
        "/settings/users/new",
        data={"username": "duplicate", "password": "other", "role": "staff",
              "full_name": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    # Still only one user with that name
    users = [u for u in user_service.list_all() if u.username == "duplicate"]
    assert len(users) == 1


# ---------------------------------------------------------------------------
# Backup UI
# ---------------------------------------------------------------------------


def test_backup_page_renders(admin_client: TestClient) -> None:
    resp = admin_client.get("/settings/backup")
    assert resp.status_code == 200


def test_backup_create_then_list(admin_client: TestClient) -> None:
    # DB may not exist yet, so trigger something that writes to disk first.
    doctor_service.create(full_name="Nurmatov Ozod", phone="+998901112233")
    resp = admin_client.post("/settings/backup/create", follow_redirects=False)
    assert resp.status_code == 303
    listing = admin_client.get("/settings/backup")
    assert listing.status_code == 200
    # At least one .db filename should appear
    assert "clinic_" in listing.text


def test_backup_path_traversal_is_rejected(admin_client: TestClient) -> None:
    # A relative path escaping the backups dir must 404, not touch the file.
    resp = admin_client.post(
        "/settings/backup/..%2Fclinic.db/delete",
        follow_redirects=False,
    )
    assert resp.status_code in {404, 405}
