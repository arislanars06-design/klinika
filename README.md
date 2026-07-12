# 🏥 Clinic LOR Desktop

**LOR (otorinolaringologiya) klinikasi uchun oflayn desktop dastur**

Shifokorlar va klinika administratorlari uchun mo'ljallangan, ikkita tilda ishlaydigan (o'zbek/rus) Windows/Linux/macOS desktop dasturi.

---

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
- **PySide6 (Qt 6)** — grafik interfeys
- **SQLite + SQLAlchemy** — mahalliy ma'lumotlar bazasi
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

---

## 🚦 Loyiha holati

**Bosqich: Logika (SPEC) yozish** — kod yozish hali boshlanmagan.

- ✅ Talablar yig'ildi
- ✅ Interfeys logikasi ishlab chiqildi
- ✅ Ma'lumotlar bazasi sxemasi tayyor
- ✅ Shikoyatlar va LOR STATUS kataloglari tuzildi
- ⏳ Chop etish Word shablonini kutish (foydalanuvchi jo'natadi)
- ⏳ Kodni yozish (SPEC tasdiqlangandan so'ng)

---

## 📅 Yo'l xaritasi

**Faza 1 — Skelet (1-hafta):**
- Loyiha strukturasi, DB migratsiyalari
- Til tanlash + bosh menyu
- Sozlamalar (xizmatlar, shifokorlar)

**Faza 2 — Qabul (2-hafta):**
- Qabul oynasi (barcha maydonlar)
- Bemor qidiruv/avtoto'ldirish
- Shikoyatlar strukturaviy tanlash
- LOR STATUS strukturaviy tanlash

**Faza 3 — Tarix va Kassa (3-hafta):**
- Bemorlar tarixi + qidiruv
- Kassa bo'limi
- Statistika (ikkala bo'lim uchun)

**Faza 4 — Chop etish va yakunlash (4-hafta):**
- Word shabloni bilan chop etish
- Word'ga statistika eksporti
- Backup tizimi
- `.exe` paketlash

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
