"""End-to-end smoke tests for the FastAPI web layer."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from clinic.web.app import create_app

    return TestClient(create_app())


def test_healthcheck(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_first_run_redirects_to_language_dialog(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.text
    assert "O'ZBEKCHA" in body
    assert "РУССКИЙ" in body


def test_setting_language_takes_effect(client: TestClient) -> None:
    # Choose Russian
    resp = client.post("/language/ru", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.cookies.get("clinic_lang") == "ru"

    # Home now renders in Russian
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Начать приём" in resp.text

    # ...and Uzbek strings should be absent
    assert "Qabulni boshlash" not in resp.text


def test_rejects_unsupported_language(client: TestClient) -> None:
    resp = client.post("/language/xx")
    assert resp.status_code == 400


def test_placeholder_pages_load(client: TestClient) -> None:
    # Warm up the language cookie first
    client.post("/language/uz", follow_redirects=False)

    for path, label in [
        ("/reception", "Qabulni boshlash"),
        ("/patients", "Bemorlar tarixi"),
        ("/cashier", "Kassa"),
        ("/settings", "Sozlamalar"),
    ]:
        resp = client.get(path)
        assert resp.status_code == 200, path
        assert label in resp.text, f"expected '{label}' in {path}"


def test_404_page_is_friendly(client: TestClient) -> None:
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert "404" in resp.text


def test_htmx_language_switch_returns_hx_redirect(client: TestClient) -> None:
    resp = client.post(
        "/language/ru",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert resp.status_code == 204
    assert resp.headers.get("HX-Redirect") == "/"
    assert resp.cookies.get("clinic_lang") == "ru"
