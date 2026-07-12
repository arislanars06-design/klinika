"""Populate a fresh database with realistic test data.

Handy when you clone the repo and want to click around the UI immediately
without inventing patients from scratch. Safe to run more than once — every
row uses ``find_or_create`` semantics, so re-runs are no-ops on the same DB.

Usage::

    python scripts/seed_data.py            # 1 doctor, 6 services, 8 patients
    python scripts/seed_data.py --reset    # wipe data/clinic.db first
    python scripts/seed_data.py --minimal  # skip patient/reception seeding
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Ensure the local ``src`` package is importable when running ad-hoc.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from clinic.config import settings  # noqa: E402
from clinic.db.database import init_db  # noqa: E402
from clinic.domain import (  # noqa: E402
    cashier_service,
    clinic_info_service,
    doctor_service,
    reception_service,
    service_service,
)
from clinic.domain.dto import (  # noqa: E402
    CashierItemInput,
    CashierPaymentInput,
    PatientInput,
    ReceptionInput,
)

DOCTORS = [
    {"full_name": "Karimov Alisher", "phone": "+998901234567"},
    {"full_name": "Aliyeva Nigora", "phone": "+998901112233"},
]

SERVICES = [
    ("Konsultatsiya", "Консультация", Decimal("100000")),
    ("Audiometriya", "Аудиометрия", Decimal("150000")),
    ("Kompressni qo'yish", "Наложение компресса", Decimal("50000")),
    ("Burun yuvish", "Промывание носа", Decimal("70000")),
    ("Injeksiya", "Инъекция", Decimal("30000")),
    ("Endoskopiya", "Эндоскопия", Decimal("200000")),
]

PATIENTS = [
    # (full_name, birth_year, address, phone, complaints, diagnosis, recommendation)
    (
        "Aliyev Anvar",
        1990,
        "Toshkent sh., Yunusobod tumani, 4-kvartal",
        "+998901112233",
        (["ear_pain", "ear_discharge"], {"ear_discharge": "purulent"}, "3 kundan beri"),
        "Otitis media akuta",
        "Antibiotik (Amoxiclav 500mg 2 marta), quloqqa borik spirti kompressi",
    ),
    (
        "Karimova Zulfiya",
        1985,
        "Toshkent sh., Chilonzor tumani",
        "+998902223344",
        (["nose_congestion", "nose_discharge"], {"nose_discharge": "mucous"}, None),
        "Akutik rinit",
        "Burun yuvish (fiziologik eritma), Xilo-Comod tomchilari",
    ),
    (
        "Toshmatov Bekzod",
        1978,
        "Samarqand sh.",
        "+998903334455",
        (["pharynx_pain", "pharynx_cough"], {}, "haroratning ko'tarilishi bilan"),
        "Akutik faringit",
        "Tomoq chayish (romashka), Faringosept",
    ),
    (
        "Nazarova Malika",
        1995,
        "Toshkent sh., Mirzo Ulug'bek tumani",
        "+998904445566",
        (["larynx_voice_change", "larynx_cough"], {}, None),
        "Akutik laringit",
        "Ovoz rejimi (2 kun gapirmaslik), sut+asal, Bronhosan",
    ),
    (
        "Yusupov Sardor",
        2010,
        "Farg'ona vil., Marg'ilon",
        "+998905556677",
        (["ear_pain", "ear_hearing_loss"], {}, "sovuq oldi kelgan"),
        "Otitis externa",
        "Otipax quloq tomchilari 3x2, sovuqdan ehtiyot",
    ),
    (
        "Rakhimov Timur",
        1965,
        "Toshkent sh., Yakkasaroy tumani",
        "+998906667788",
        (["ear_hearing_loss", "ear_noise"], {}, "yillar davomida"),
        "Sensonevral eshitish pasayishi",
        "Audiogramma tekshiruvi + neurolog konsultatsiyasi",
    ),
    (
        "Ismoilova Feruza",
        1982,
        "Namangan sh.",
        "+998907778899",
        (["pharynx_lump", "pharynx_swallowing"], {}, None),
        "Surunkali tonzillit",
        "Bodomsimon bezlarni yuvish 5 seansda, immunomodulyator",
    ),
    (
        "Boboyev Otabek",
        2001,
        None,
        None,
        (["nose_breathing"], {}, "burun ichida asymmetriya bor"),
        "Burun to'sig'i qiyshiqligi",
        "LOR-jarrohga yo'llash — septoplastika muhokamasi",
    ),
]


def _reset_db() -> None:
    settings.ensure_dirs()
    if settings.db_path.exists():
        print(f"[reset] deleting {settings.db_path}")
        settings.db_path.unlink()
    for suffix in ("-wal", "-shm"):
        extra = settings.db_path.parent / (settings.db_path.name + suffix)
        if extra.exists():
            extra.unlink()


def _seed_clinic() -> None:
    info = clinic_info_service.load()
    if info.name_uz:
        return  # already configured
    print("[clinic] populating default clinic info")
    clinic_info_service.save(
        clinic_info_service.ClinicInfo(
            name_uz="LOR klinikasi \u201cTest\u201d",
            name_ru="ЛОР клиника \u201cТест\u201d",
            address_uz="Toshkent sh., Yunusobod, Amir Temur ko'ch. 1",
            address_ru="г. Ташкент, Юнусабад, ул. Амира Темура 1",
            phone="+998 71 123 45 67",
            logo_path="",
            language="uz",
        )
    )


def _seed_doctors() -> list:
    doctors: list = []
    for spec in DOCTORS:
        existing = next(
            (d for d in doctor_service.list_all() if d.full_name == spec["full_name"]),
            None,
        )
        if existing:
            doctors.append(existing)
            continue
        d = doctor_service.create(**spec)
        print(f"[doctor] created {d.full_name}")
        doctors.append(d)
    return doctors


def _seed_services() -> list:
    services: list = []
    existing_by_name = {s.name_uz: s for s in service_service.list_all()}
    for name_uz, name_ru, price in SERVICES:
        if name_uz in existing_by_name:
            services.append(existing_by_name[name_uz])
            continue
        svc = service_service.create(name_uz=name_uz, name_ru=name_ru, price=price)
        print(f"[service] created {svc.name_uz} ({svc.price})")
        services.append(svc)
    return services


def _seed_receptions(doctors: list, services: list) -> None:
    if not doctors or not services:
        return
    # Skip if we already have any receptions — signals a re-run.
    from clinic.db.database import session_scope
    from clinic.db.models import Reception

    with session_scope() as session:
        if session.query(Reception).first() is not None:
            print("[seed] receptions already exist, skipping patient/reception seeding")
            return

    base = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    for i, entry in enumerate(PATIENTS):
        name, year, address, phone, complaints, diagnosis, recommendation = entry
        codes, details, note = complaints
        r, patient, _ = reception_service.save(
            ReceptionInput(
                patient=PatientInput(
                    full_name=name,
                    birth_year=year,
                    address=address,
                    phone=phone,
                ),
                patient_id=None,
                doctor_id=doctors[i % len(doctors)].id,
                reception_date=base - timedelta(days=i * 2),
                complaints_codes=list(codes),
                complaints_details=dict(details),
                complaints_note=note,
                anamnesis="Test seed skript orqali yaratilgan.",
                lor_status={
                    "rhinoscopy": {
                        "breathing": {"state": "free"},
                        "mucosa": {"color": "pink", "moisture": "moist"},
                    },
                },
                diagnosis=diagnosis,
                recommendation=recommendation,
            )
        )
        # Every other patient also gets a paid consultation.
        if i % 2 == 0:
            cashier_service.save_payment(
                CashierPaymentInput(
                    patient_id=patient.id,
                    reception_id=r.id,
                    items=[
                        CashierItemInput(service_id=services[0].id, quantity=1),
                        CashierItemInput(service_id=services[(i + 1) % len(services)].id, quantity=1),
                    ],
                )
            )
        print(f"[patient] created {name}  (reception #{r.id})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the SQLite database before seeding.",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Only seed clinic info + doctors + services (no patients).",
    )
    args = parser.parse_args()

    if args.reset:
        _reset_db()

    init_db()
    _seed_clinic()
    doctors = _seed_doctors()
    services = _seed_services()

    if not args.minimal:
        _seed_receptions(doctors, services)

    print("\nDone. Launch the UI with:  python -m clinic.main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
