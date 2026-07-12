# 🏥 Klinika LOR

**LOR (otorinolaringologiya) klinikasi uchun lokal web-ilova.**

Bir server, brauzer orqali kirish, uz/ru tilida ishlaydi.

---

## ⚡ Asosiy imkoniyatlar

- 🩺 **Qabul qilish** — bemor + strukturaviy shikoyatlar (30 element) + LOR STATUS + tashxis
- 📋 **Bemorlar tarixi** — qidiruv, kartochka, statistika
- 💰 **Kassa** — xizmatlar, hisob-kitob, statistika
- 🌍 **Ikki til** — o'zbekcha va ruscha (bir bosishda almashadi)
- 🖨 **Word chop etish** — klinika shabloni asosida qabul varaqasi
- 📊 **Statistika** — Word formatida eksport (kunlik/haftalik/oylik/yillik)
- ⚙️ **Sozlamalar** — klinika ma'lumotlari, shifokorlar, xizmatlar

---

## 🚀 Tez ishga tushirish

### Docker orqali (osonroq)

```bash
docker compose up -d
python -c "from scripts.seed_data import main; main()"  # boshlang'ich ma'lumotlar
```

Brauzerda: `http://localhost:8000/`

### Python orqali

```bash
python3.11 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
python -m scripts.seed_data    # boshlang'ich ma'lumotlar
python -m clinic.main --host 0.0.0.0
```

To'liq o'rnatish yo'riqnomasi: [`INSTALL_uz.md`](INSTALL_uz.md)

---

## 🛠 Texnologiyalar

| Qatlam | Vosita |
|--------|--------|
| **Backend** | Python 3.11 + FastAPI + SQLAlchemy 2.0 |
| **Frontend** | Jinja2 shablonlar + Tailwind CSS + HTMX + Alpine.js |
| **Ma'lumotlar** | SQLite (bitta fayl, backup oson) |
| **Chop etish** | python-docx + docxtpl |
| **Loglash** | loguru |

---

## 📁 Loyiha strukturasi

```
src/clinic/
├── main.py               # uvicorn kirish nuqtasi
├── config.py             # sozlamalar
├── db/                   # SQLAlchemy modellari
├── domain/               # biznes-mantiq (patient, doctor, reception, cashier, stats)
├── i18n/                 # uz/ru tarjimalar
├── catalogs/             # shikoyat/LOR STATUS/ajralma turlari JSON
├── infrastructure/       # loglash, backup
├── printing/             # Word hujjatlar (text_composer, docx_builder)
└── web/
    ├── app.py            # FastAPI factory
    ├── deps.py           # dependencies
    ├── routes/           # HTTP endpointlar
    ├── templates/        # Jinja2 shablonlar
    └── static/           # CSS/JS

templates/                # foydalanuvchining Word shablonlari
data/                     # runtime ma'lumotlar (baza, backup, log)
scripts/
├── seed_data.py          # boshlang'ich ma'lumotlar
└── backup.py             # kundalik zaxira
deploy/
└── clinic-lor.service    # systemd unit fayli
```

---

## 🧪 Testlar

```bash
pip install -e '.[dev]'
pytest
```

---

## 📖 Hujjatlar

- [`SPEC.md`](SPEC.md) — texnik topshiriq
- [`INSTALL_uz.md`](INSTALL_uz.md) — o'rnatish (klinika uchun)
- [`docs/architecture.md`](docs/architecture.md) — arxitektura
- [`docs/database_schema.md`](docs/database_schema.md) — ma'lumotlar bazasi
- [`docs/complaints_catalog.md`](docs/complaints_catalog.md) — shikoyatlar katalogi
- [`docs/lor_status_catalog.md`](docs/lor_status_catalog.md) — LOR STATUS katalogi

---

## 🔒 Ma'lumotlar xavfsizligi

- Barcha ma'lumotlar **lokal SQLite** faylida (`data/clinic.db`)
- Har kuni avtomatik backup (`data/backups/`)
- 30 kundan eski backup'lar avtomatik o'chiriladi
- Internet talab qilinmaydi

---

## 📞 Aloqa

Muammo yuzaga kelsa, `data/logs/` papkasidagi log faylni ishlab chiquvchiga yuboring.
