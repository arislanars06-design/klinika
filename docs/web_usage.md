# 🌐 Klinika LOR — websayt versiyasi (Bosqich 1)

Desktop dasturi bilan yonma-yon ishlaydigan **websayt** — brauzer orqali
qabul yaratish, bemorlar tarixini ko'rish, Word'ga chop etish.

- Kutubxona: **FastAPI + Jinja2 + Bootstrap 5 + HTMX**
- Ma'lumotlar bazasi: **desktop bilan bir xil** (bir joyda ishlagan
  `data/clinic.db` faylini o'qiydi va yozadi)
- Til: **o'zbek / rus** (yuqori o'ng burchakdagi almashtirgichdan)
- Chop etish: **sizning `templates/reception_template.docx` shabloningiz**
- Autentifikatsiya: **bitta umumiy parol** (Bosqich 3'da hodim akkauntlari
  qo'shiladi)

---

## Ishga tushirish

### 1) Local (bitta kompyuterda sinov uchun)

```bash
git clone https://github.com/arislanars06-design/klinika.git
cd klinika
python -m venv .venv
source .venv/bin/activate            # Linux/macOS
# .venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -e ".[dev]"

python -m clinic.web.main
```

Brauzer'da oching: **<http://127.0.0.1:8000>**
- Parol: `clinic` (default)
- O'zgartirish: `export CLINIC_WEB_PASSWORD=YourStrongPassword`

### 2) Klinika ichki tarmog'ida (bir necha kompyuter uchun)

**Server kompyuter** (masalan registratura):

```bash
# Butun tarmoq uchun ochish
export CLINIC_WEB_HOST=0.0.0.0
export CLINIC_WEB_PORT=8000
export CLINIC_WEB_PASSWORD=YourStrongPassword
export CLINIC_WEB_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")

python -m clinic.web.main
```

Server kompyuterning IP manzilini oling (`ipconfig` Windows'da yoki `ip a`
Linux'da) — masalan `192.168.1.100`.

**Boshqa kompyuterlar** (shifokor kabineti, kassa):
- Brauzer oching → **<http://192.168.1.100:8000>**
- Bir xil parol bilan kiring.

**Muhim:** Server kompyuter yoqilib turishi va WiFi/Ethernet tarmoqda
bo'lishi kerak.

### 3) Bulutda (Internet orqali)

Reverse proxy (nginx/Caddy) orqasida ishga tushiring, TLS bilan (Let's Encrypt).
Namuna `docker-compose.yml` fayl Bosqich 3'da qo'shiladi.

---

## Muhit o'zgaruvchilari (`.env` fayl yoki `export`)

| O'zgaruvchi | Default | Tavsif |
|---|---|---|
| `CLINIC_WEB_HOST` | `127.0.0.1` | Bind manzili. Tarmoq uchun `0.0.0.0` |
| `CLINIC_WEB_PORT` | `8000` | Bind porti |
| `CLINIC_WEB_PASSWORD` | `clinic` | Umumiy parol |
| `CLINIC_WEB_SECRET` | random | Cookie imzo kaliti — production'da o'rnating |
| `CLINIC_WEB_SESSION_MAX_AGE` | `43200` (12 soat) | Sessiya muddati (soniyalarda) |
| `CLINIC_DATA_DIR` | `data/` | Baza fayli qayerda saqlanadi |

---

## Bosqich 1'da nima bor

- ✅ **Kirish sahifasi** — parol bilan
- ✅ **Bosh menyu** — 3 karta + statistika (bemorlar/qabullar/shifokorlar/xizmatlar soni)
- ✅ **Yangi qabul** formasi — shikoyatlar (accordion), LOR STATUS (metod bo'yicha tab), tashxis, tavsiya
- ✅ **Qabulni tahrirlash**
- ✅ **Qabul tafsilotlari** ko'rinishi
- ✅ **Bemorlar ro'yxati** — qidiruv + maydon filtri + sahifalash
- ✅ **Bemor kartochkasi** — barcha qabullari
- ✅ **HTMX autocomplete** — F.I.O. yozganda dropdown
- ✅ **Word chop etish** — sizning shabloningizni ishlatadi
- ✅ **Til almashtirish** — uz/ru
- ✅ **Chiqish**

## Bosqich 2 (rejalashtirilgan) — Kassa + Statistika

- Kassa oynasi (xizmatlar jadvali, chek yaratish)
- Statistika + Chart.js grafiklar
- Word'ga eksport

## Bosqich 3 (rejalashtirilgan) — Sozlamalar + polish

- Sozlamalar (klinika, shifokorlar, xizmatlar)
- Backup boshqaruvi
- Hodim akkauntlari (rollar bilan)
- Docker compose + nginx yo'riqnomasi

---

## Desktop bilan farqi

Ikkalasi ham **bir xil `data/clinic.db` bazani** ishlatadi — desktop'da
yaratilgan bemor websaytda ko'rinadi va aksincha. Bir vaqtda ikkalasini
ochish xavfsiz (SQLite WAL rejimida).

| | 🖥 Desktop | 🌐 Web |
|---|---|---|
| Kirish | Bevosita | Parol bilan |
| Til almashtirish | Sozlamalarda | Yuqorida droplist |
| LOR STATUS | To'liq strukturaviy (radio/checkbox/tab) | **Metod bo'yicha erkin matn** (Bosqich 1) |
| Grafiklar | matplotlib | Bosqich 2 (Chart.js) |
| Kassa | Bor | Bosqich 2 |
| Sozlamalar | Bor | Bosqich 3 |

---

## Xavfsizlik eslatmalari

1. **Production'da `CLINIC_WEB_PASSWORD` va `CLINIC_WEB_SECRET`ni o'zgartiring.**
2. Internet orqali chiqarsangiz — **TLS (HTTPS)** kerak (bulutda).
3. Ichki tarmoqda ishlashda — kirish faqat klinika Wi-Fi orqali bo'lishini ta'minlang.
4. Bemor ma'lumotlari mahalliy SQLite'da — server kompyuterni zaxiralang.

---

*Hujjat versiyasi: 1.0 · Sana: 2026-07-13*
