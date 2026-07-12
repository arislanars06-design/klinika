# 🏗 Arxitektura va texnologiyalar

## 1. Texnologiya to'plami (Tech Stack)

### 1.1 Asosiy komponentlar

| Qatlam | Texnologiya | Versiya | Vazifasi |
|--------|-------------|---------|----------|
| **Til** | Python | 3.11+ | Asosiy dasturlash tili |
| **GUI framework** | PySide6 | 6.6+ | Grafik interfeys (Qt for Python) |
| **ORM** | SQLAlchemy | 2.0+ | Ma'lumotlar bazasi bilan ishlash |
| **DB** | SQLite | 3.35+ | Lokal ma'lumotlar bazasi |
| **Migratsiya** | Alembic | 1.13+ | Baza sxemasi o'zgarishlari |
| **Word** | python-docx | 1.1+ | Word hujjatlarini yaratish |
| **Word shablon** | docxtpl | 0.16+ | Jinja placeholder'lar bilan shablon to'ldirish |
| **Grafik** | matplotlib | 3.8+ | Statistika diagrammalari |
| **Loglash** | loguru | 0.7+ | Log yozish |
| **Konfiguratsiya** | pydantic-settings | 2.1+ | Sozlamalarni yuklash |
| **Sana/vaqt** | python-dateutil | 2.8+ | Davrlarni hisoblash |

### 1.2 Rivojlantirish uchun

| Vosita | Vazifasi |
|--------|----------|
| **pytest** | Unit va integration testlar |
| **ruff** | Kod formatlash va linting |
| **mypy** | Turdorlar tekshirish |
| **pre-commit** | Commit oldidan avtomatik tekshirish |

### 1.3 Paketlash

- **PyInstaller** — bitta `.exe` fayl yaratish
- **Inno Setup** (ixtiyoriy) — Windows uchun o'rnatuvchi

---

## 2. Loyiha strukturasi

```
clinic-lor-desktop/
├── README.md
├── SPEC.md
├── LICENSE
├── pyproject.toml               # Loyiha metadata + bog'liqliklar
├── requirements.txt             # Bog'liqliklar (dublikat)
├── .gitignore
├── .env.example
│
├── docs/                        # Hujjatlar
│   ├── architecture.md
│   ├── database_schema.md
│   ├── complaints_catalog.md
│   └── lor_status_catalog.md
│
├── src/                         # Manba kodi
│   └── clinic/
│       ├── __init__.py
│       ├── main.py              # Kirish nuqtasi
│       ├── config.py            # Sozlamalar
│       │
│       ├── db/                  # Ma'lumotlar bazasi
│       │   ├── __init__.py
│       │   ├── database.py      # Session, engine
│       │   ├── models.py        # SQLAlchemy modellari
│       │   └── repository.py    # CRUD operatsiyalari
│       │
│       ├── domain/              # Biznes-mantiq (UI'dan mustaqil)
│       │   ├── __init__.py
│       │   ├── patient_service.py
│       │   ├── reception_service.py
│       │   ├── cashier_service.py
│       │   ├── stats_service.py
│       │   └── catalog_service.py
│       │
│       ├── i18n/                # Tarjimalar
│       │   ├── __init__.py
│       │   ├── translator.py    # t() funksiyasi
│       │   ├── uz.json
│       │   └── ru.json
│       │
│       ├── catalogs/            # Static kataloglar
│       │   ├── complaints.json  # Shikoyatlar (30+ element)
│       │   ├── lor_status.json  # LOR STATUS bandlari
│       │   └── discharge_types.json  # Ajralma turlari
│       │
│       ├── ui/                  # PySide6 oynalari
│       │   ├── __init__.py
│       │   ├── app.py           # QApplication + boshlash
│       │   ├── main_window.py   # Bosh menyu
│       │   │
│       │   ├── reception/       # Qabul oynasi
│       │   │   ├── __init__.py
│       │   │   ├── window.py
│       │   │   ├── patient_widget.py
│       │   │   ├── complaints_widget.py
│       │   │   └── lor_status_widget.py
│       │   │
│       │   ├── patients/        # Bemorlar tarixi
│       │   │   ├── window.py
│       │   │   ├── search_widget.py
│       │   │   ├── card_dialog.py
│       │   │   └── stats_widget.py
│       │   │
│       │   ├── cashier/         # Kassa
│       │   │   ├── window.py
│       │   │   ├── services_widget.py
│       │   │   └── stats_widget.py
│       │   │
│       │   ├── settings/        # Sozlamalar
│       │   │   ├── window.py
│       │   │   ├── clinic_tab.py
│       │   │   ├── doctors_tab.py
│       │   │   ├── services_tab.py
│       │   │   └── catalogs_tab.py
│       │   │
│       │   └── widgets/         # Umumiy widget'lar
│       │       ├── language_switcher.py
│       │       ├── date_range_picker.py
│       │       ├── searchable_combo.py
│       │       └── styled_button.py
│       │
│       ├── printing/            # Chop etish
│       │   ├── __init__.py
│       │   ├── docx_builder.py  # Word yaratish
│       │   ├── text_composer.py # Checkboxlarni matnga aylantirish
│       │   └── stats_export.py  # Statistika Word'ga
│       │
│       ├── infrastructure/      # Yordamchi
│       │   ├── logging_setup.py
│       │   ├── backup.py        # Baza backup
│       │   └── validators.py    # F.I.O, telefon va h.k.
│       │
│       └── resources/           # Rasmlar, iconlar, stillar
│           ├── icons/
│           ├── styles.qss       # Qt stylesheet
│           └── fonts/
│
├── templates/                   # Word shablonlari
│   ├── reception_template.docx  # Qabul varaqasi
│   ├── stats_patients.docx      # Bemorlar statistikasi
│   └── stats_cashier.docx       # Kassa statistikasi
│
├── migrations/                  # Alembic migratsiyalari
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
│
├── tests/                       # Testlar
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_validators.py
│   ├── test_text_composer.py
│   ├── test_stats_service.py
│   └── test_repository.py
│
├── scripts/                     # Yordamchi skriptlar
│   ├── seed_data.py             # Test ma'lumotlari
│   ├── build_exe.py             # PyInstaller
│   └── generate_translations.py # Tarjimalarni sinxronlashtirish
│
└── data/                        # Ma'lumotlar (gitignore'da)
    ├── clinic.db                # SQLite bazasi
    ├── backups/                 # Zaxira nusxalar
    └── logs/                    # Log fayllar
```

---

## 3. Qatlamli arxitektura

Dastur **4 qatlamli arxitektura**ga asoslanadi:

```
┌──────────────────────────────────────────────┐
│  Presentation Layer (ui/)                    │
│  PySide6 oynalari, widget'lar                │
└──────────────────────────────────────────────┘
              ↕ (signal/slot)
┌──────────────────────────────────────────────┐
│  Domain Layer (domain/)                      │
│  Biznes-mantiq, servislar                    │
│  (UI'dan mustaqil, sinash oson)              │
└──────────────────────────────────────────────┘
              ↕
┌──────────────────────────────────────────────┐
│  Data Layer (db/)                            │
│  SQLAlchemy repository'lar                   │
└──────────────────────────────────────────────┘
              ↕
┌──────────────────────────────────────────────┐
│  Infrastructure (infrastructure/, catalogs/) │
│  Logging, backup, tarjimalar, kataloglar     │
└──────────────────────────────────────────────┘
```

### 3.1 Presentation Layer (UI)

- Faqat ko'rsatish va foydalanuvchi kiritish
- Signal/slot orqali Domain servislarini chaqiradi
- Biznes-mantiqni o'zida saqlamaydi

**Misol:**
```python
# ui/reception/window.py (namuna, hozircha yozilmagan)
def on_save_clicked(self):
    data = self._collect_form_data()
    try:
        reception_id = self._reception_service.save(data)
        show_success_message(t("reception.saved"))
    except ValidationError as e:
        show_error(e.messages)
```

### 3.2 Domain Layer

- Barcha biznes-qoidalar shu yerda
- UI framework'dan mustaqil (PySide6 haqida bilmaydi)
- Testlar bilan qoplangan

**Misol:**
```python
# domain/reception_service.py
class ReceptionService:
    def save(self, data: ReceptionInput) -> int:
        self._validate(data)
        patient = self._patient_repo.find_or_create(data.patient)
        reception = Reception(
            patient_id=patient.id,
            complaints_codes=data.complaints_codes,
            complaints_details=data.complaints_details,
            lor_status=data.lor_status,
            diagnosis=data.diagnosis,
            ...
        )
        return self._reception_repo.save(reception)
```

### 3.3 Data Layer

- SQLAlchemy Session boshqarish
- Repository pattern — har bir jadval uchun alohida repository

### 3.4 Infrastructure

- Log, backup, tarjima, validatsiya
- Barcha qatlamlar foydalanadi

---

## 4. Muhim texnik qarorlar

### 4.1 JSON maydonlar bilan ishlash

Shikoyatlar va LOR STATUS — **JSON** shaklida saqlanadi. Sabablari:

**Afzalliklari:**
- ✅ Katta jadvalga bo'lish shart emas (500+ munosabat qatorlari)
- ✅ Struktura moslashuvchan — yangi maydon qo'shish oson
- ✅ SQLite `json_extract()` orqali qidirish mumkin
- ✅ Bir bemorning to'liq qabul rekordi bir qatorda ko'rinadi

**Zaifliklari:**
- ⚠️ JSON qismini indekslash qiyin
- ⚠️ Katta hajmda bo'lsa sekinlashishi mumkin

**Yechim:** kichik ma'lumotlar (bir qabul ~ 2-5 KB), bir kompyuterda ishlaydi — bu muammo emas.

### 4.2 Til almashtirish

- **JSON tarjima fayllari** — sodda, versionlaydi oson
- Katta framework (`gettext`) shart emas — dastur nisbatan kichik
- `t("kalit")` chaqirish orqali barcha matnlar bir joyda

### 4.3 Bemor takrorlanishining oldini olish

**Muammo:** F.I.O va tug'ilgan yili bir xil ikki alohida bemor bo'lishi mumkin (masalan, aka-uka).

**Yechim:** Faqat **avtomatik ogohlantirish** — "Bunday bemor bazada bor. Xohlaganingizni tanlang" (yangi yaratish / mavjudga qabul qo'shish).

### 4.4 Narx tarixi

To'lov yozuvida `price_at_moment` — o'sha paytdagi narxni saqlaydi. Keyin xizmat narxi oshsa ham eski to'lov o'zgarmaydi.

### 4.5 Soft delete

- Xizmatlar, shifokorlar — **o'chirilmaydi**, faqat `is_active = false` bo'ladi
- Sababi: eski qabul/to'lovlarda ular ko'rinishi kerak
- Bemor esa **o'chiriladi** (kaskadli — barcha qabullar va to'lovlar bilan)

### 4.6 Threading

- **Uzoq operatsiyalar** (chop etish, statistika hisobi, backup) — `QThread` yoki `QtConcurrent`
- UI bloklanmasin

---

## 5. Bog'liqliklar (dependencies)

`pyproject.toml` (namuna):

```toml
[project]
name = "clinic-lor-desktop"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.6",
    "SQLAlchemy>=2.0",
    "alembic>=1.13",
    "python-docx>=1.1",
    "docxtpl>=0.16",
    "matplotlib>=3.8",
    "loguru>=0.7",
    "pydantic>=2.5",
    "pydantic-settings>=2.1",
    "python-dateutil>=2.8",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "ruff>=0.1",
    "mypy>=1.7",
    "pre-commit>=3.5",
    "pyinstaller>=6.3",
]
```

---

## 6. Paketlash

### 6.1 PyInstaller

```bash
pyinstaller \
    --name ClinicLOR \
    --windowed \
    --icon src/clinic/resources/icons/app.ico \
    --add-data "src/clinic/catalogs:catalogs" \
    --add-data "src/clinic/i18n:i18n" \
    --add-data "templates:templates" \
    src/clinic/main.py
```

### 6.2 Natijaviy struktura

```
dist/ClinicLOR/
├── ClinicLOR.exe
├── _internal/  (kutubxonalar)
├── catalogs/
├── i18n/
└── templates/
```

Foydalanuvchi bir marta ishga tushirganda `data/` papkasi avtomatik yaratiladi.

---

## 7. Sifat kafolatlari

### 7.1 Testlar

- **Unit testlar** — domain servislari (validatsiya, matn shakllantirish)
- **Integration testlar** — DB bilan aloqa
- **Manual smoke** — UI oqimlari

### 7.2 Kod sifati

- **ruff** — PEP 8 va format
- **mypy** — statik tur tekshirish
- **pre-commit hooks** — commit oldidan tekshirish

### 7.3 Loglash

- Har bir muhim harakat log'ga yoziladi
- Xatolar batafsil traceback bilan
- Foydalanuvchi log fayllarini backup bilan birga jo'natishi mumkin

---

*Hujjat versiyasi: 1.0 · Sana: 2026-07-12*
