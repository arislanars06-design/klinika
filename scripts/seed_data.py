"""Populate a fresh clinic DB with sensible defaults.

Run once after ``clinic-lor`` is installed:

    python -m scripts.seed_data

Adds:
- Klinika ma'lumotlari (namuna)
- 2 shifokor (namuna)
- 12 ENT xizmati (klinikalarda ko'p uchraydigan)

Existing rows are not modified; this script is idempotent by name.
"""

from __future__ import annotations

from decimal import Decimal

from loguru import logger

from clinic.db.database import init_db, session_scope
from clinic.domain import doctor_service, service_catalog_service, settings_service
from clinic.infrastructure.logging_setup import configure_logging

DEFAULT_CLINIC_SETTINGS = {
    "clinic_name_uz": "LOR Klinikasi",
    "clinic_name_ru": "ЛОР Клиника",
    "clinic_address_uz": "Toshkent shahri",
    "clinic_address_ru": "г. Ташкент",
    "clinic_phone": "+998 71 000 00 00",
}

DEFAULT_DOCTORS = [
    ("Karimov Alisher", "+998 90 111 22 33"),
    ("Yusupova Zulfiya", "+998 90 444 55 66"),
]

DEFAULT_SERVICES = [
    ("Konsultatsiya", "Консультация",                       Decimal("100000")),
    ("Audiometriya", "Аудиометрия",                         Decimal("150000")),
    ("Otoskopiya", "Отоскопия",                             Decimal("80000")),
    ("Rinoskopiya", "Риноскопия",                           Decimal("80000")),
    ("Faringoskopiya", "Фарингоскопия",                     Decimal("80000")),
    ("Laringoskopiya", "Ларингоскопия",                     Decimal("100000")),
    ("Burun yuvish", "Промывание носа",                     Decimal("50000")),
    ("Quloq yuvish", "Промывание уха",                      Decimal("50000")),
    ("Kompress", "Компресс",                                Decimal("40000")),
    ("Sertifikat / Ma'lumotnoma", "Справка",                Decimal("30000")),
    ("Yuqori chastotali terapiya", "УВЧ-терапия",           Decimal("60000")),
    ("Antibiotik in'ektsiya", "Инъекция антибиотика",       Decimal("50000")),
]


def seed_settings() -> int:
    added = 0
    for key, value in DEFAULT_CLINIC_SETTINGS.items():
        if settings_service.get(key) is None:
            settings_service.set_value(key, value)
            added += 1
    return added


def seed_doctors() -> int:
    added = 0
    with session_scope() as session:
        existing = {d.full_name for d in doctor_service.list_all(session)}
        for name, phone in DEFAULT_DOCTORS:
            if name in existing:
                continue
            doctor_service.create(session, doctor_service.DoctorInput(full_name=name, phone=phone))
            added += 1
    return added


def seed_services() -> int:
    added = 0
    with session_scope() as session:
        existing = {s.name_uz for s in service_catalog_service.list_all(session)}
        for uz, ru, price in DEFAULT_SERVICES:
            if uz in existing:
                continue
            service_catalog_service.create(
                session,
                service_catalog_service.ServiceInput(name_uz=uz, name_ru=ru, price=price),
            )
            added += 1
    return added


def main() -> None:
    configure_logging()
    init_db()

    n_settings = seed_settings()
    n_doctors = seed_doctors()
    n_services = seed_services()

    logger.info(
        "Seed complete: settings +{}, doctors +{}, services +{}",
        n_settings,
        n_doctors,
        n_services,
    )
    print(f"OK — settings: +{n_settings}, doctors: +{n_doctors}, services: +{n_services}")


if __name__ == "__main__":
    main()
