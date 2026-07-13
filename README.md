# 🏥 Clinic LOR Desktop

**LOR (otorinolaringologiya) klinikasi uchun oflayn desktop dastur**

Shifokorlar va klinika administratorlari uchun mo'ljallangan, ikkita tilda ishlaydigan (o'zbek/rus) Windows/Linux/macOS desktop dasturi.

---

> 🌐 **Web versiyasi ham mavjud!** Xuddi shu ma'lumotlar bazasi bilan brauzerdan
> ishlaydigan FastAPI qatlami. Ichki tarmoqda bir necha kompyuterdan foydalanish
> uchun ideal. Ko'rsatmalar: [`docs/web_usage.md`](docs/web_usage.md).
>
> ```bash
> python -m clinic.web.main  # → http://127.0.0.1:8000
> ```

## ⚡ Asosiy imkoniyatlar

- 🩺 **Qabulni boshlash** — bemor ma'lumotlari, strukturaviy shikoyatlar, LOR STATUS, tashxis, tavsiya
- 📋 **Bemorlar tarixi** — qidiruv, tahrirlash, filter, statistika (kunlik/haftalik/oylik/yillik)
- 💰 **Kassa** — xizmatlar, hisob-kitob, kvitansiya, statistika
- 🌍 **Ikki til** — o'zbekcha va ruscha (bir bosishda almashadi)
- 🖨 **Word/PDF chop etish** — klinika shabloni asosida qabul varaqasi
- 📊 **Statistika** — Word formatida eksport
- ⚙️ **Sozlamalar** — xizmatlar, shifokorlar, katalog tahrirlash

---

## 🛠 Texnologiyalar

- **Python 3.11+** — asosiy dasturlash tili
- **PySide6 (Qt 6)** — desktop grafik interfeys
- **FastAPI + Jinja2 + Bootstrap 5 + HTMX** — web versiyasi
- **SQLite + SQLAlchemy** — mahalliy ma'lumotlar bazasi (desktop va web bir xil bazani ishlatadi)
- **python-docx + docxtpl** — Word hujjatlarini yaratish va shablonlarni to'ldirish
- **PyInstaller** — bitta `.exe` faylga paketlash

---

## 📁 Hujjatlar

Loyihaning to'liq logikasi va texnik topshirig'i quyidagi fayllarda:

| Fayl | Tavsif |
|------|--------|
| [`SPEC.md`](SPEC.md) | Asosiy texnik topshiriq — barcha ekranlar, oqimlar, qoidalar |
| [`docs/architecture.md`](docs/architecture.md) | Loyiha strukturasi, texnologiyalar, modullar |
| [`docs/database_schema.md`](docs/database_schema.md) | Ma'lumotlar bazasi jadvallari va bog'lanishlari |
| [`docs/complaints_catalog.md`](docs/complaints_catalog.md) | Shikoyatlar katalogi (30+ element, uz/ru) |
| [`docs/lor_status_catalog.md`](docs/lor_status_catalog.md) | LOR STATUS katalogi (4 ko'rik metodi) |
| [`docs/web_usage.md`](docs/web_usage.md) | 🌐 Web versiyasini ishga tushirish (local / ichki tarmoq / bulut) |
| [`docs/template_placeholders.md`](docs/template_placeholders.md) | Word shabloni uchun placeholder'lar |

---

## 🚦 Loyiha holati

**Bosqich: To'liq ishlaydi** — barcha 4 milestone tugagan (134 avtomatik test o'tadi).

- ✅ **M1** — Skelet, ma'lumotlar bazasi, Sozlamalar (klinika/shifokorlar/xizmatlar)
- ✅ **M2** — Qabul oynasi (bemor + shikoyat + LOR STATUS + tashxis)
- ✅ **M3** — Bemorlar tarixi + Kassa + Statistika (grafiklar bilan)
- ✅ **M4** — Chop etish (Word) + Backup tizimi + PyInstaller
- ⏳ Klinika Word shabloni (ixtiyoriy — hozircha default layout ishlaydi)

## 🚀 Tez boshlash

```bash
git clone https://github.com/arislanars06-design/klinika.git
cd klinika
pip install -e ".[dev]"

python scripts/seed_data.py --reset      # test ma'lumotlarni yuklash
python -m clinic.main                    # dasturni ishga tushirish
```

Manual sinov uchun to'liq yo'l-yo'riq: [`docs/testing_checklist.md`](docs/testing_checklist.md).

Windows uchun `.exe` yig'ish: [`docs/build_instructions.md`](docs/build_instructions.md).

---

## 📅 Yakunlangan yo'l xaritasi

| Faza | Holat | PR |
|------|-------|-----|
| **Faza 1** — Skelet + DB + Sozlamalar | ✅ Tugatildi | [#1](https://github.com/arislanars06-design/klinika/pull/1) + [#3](https://github.com/arislanars06-design/klinika/pull/3) |
| **Faza 2** — Qabul oynasi + bemor + shikoyat + LOR STATUS | ✅ Tugatildi | [#3](https://github.com/arislanars06-design/klinika/pull/3) |
| **Faza 3** — Tarix + Kassa + Statistika (matplotlib) | ✅ Tugatildi | [#4](https://github.com/arislanars06-design/klinika/pull/4) |
| **Faza 4** — Word chop etish + Backup + PyInstaller | ✅ Tugatildi | [#5](https://github.com/arislanars06-design/klinika/pull/5) |

Kelajakdagi (v2) kengaytmalari [`SPEC.md`](SPEC.md) §14 da: login/parol, ICD-10, qabul jadvali, SMS eslatma, bulut backup.

---

## 👥 Foydalanuvchilar

- **Shifokor** — bemor qabul qilish, ko'rik, tashxis, tavsiya berish
- **Klinika administratori** — bemorlar, to'lovlar, statistika bilan ishlash

*Birinchi versiyada rol/parol yo'q — bir kompyuterda ishlaydi.*

---

## 🔒 Ma'lumotlar xavfsizligi

- Barcha ma'lumotlar **lokal SQLite** faylida saqlanadi (bulut yo'q)
- Har kuni avtomatik **backup** yaratiladi (`data/backups/`)
- 30 kundan eski backup'lar avtomatik o'chiriladi

---

## 📞 Aloqa

Loyiha egasi: *(to'ldiriladi)*

---

*Bu hujjat SPEC yozish jarayonida yaratilgan.*
