# 🚀 Deployment — Klinika LOR web

Uch xil variant: **local sinov**, **klinika ichki tarmog'i**, **bulut (Docker+nginx)**.

---

## 1) Local (bitta kompyuter, Python bilan)

Sinash uchun eng oson yo'l. Talab: Python 3.11+.

```bash
git clone https://github.com/arislanars06-design/klinika.git
cd klinika
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m clinic.web.main   # → http://127.0.0.1:8000
```

Birinchi kirish uchun:
- Foydalanuvchi: `admin`
- Parol: `clinic` (yoki `CLINIC_WEB_PASSWORD` env qiymati)

Kirishdan keyin darhol **Sozlamalar → Foydalanuvchilar** ochib parolni yangilang.

---

## 2) Klinika ichki tarmog'ida (LAN, bir necha kompyuter)

Bitta server kompyuter (masalan, registratura) — u yoqilib turadi. Boshqa
kompyuterlar unga Wi-Fi orqali brauzerdan kiradi.

**Server kompyuterda (Windows PowerShell):**

```powershell
# Kuchli tasodifiy secret yasang (bir marta)
$env:CLINIC_WEB_SECRET  = python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:CLINIC_WEB_PASSWORD = "SizningKuchliParolingiz"
$env:CLINIC_WEB_HOST     = "0.0.0.0"     # tarmoqqa ochish
$env:CLINIC_WEB_PORT     = "8000"

python -m clinic.web.main
```

Server IP manzilini oling: `ipconfig` (Windows) yoki `ip a` (Linux). Masalan
`192.168.1.100`.

**Boshqa kompyuterlar (shifokor kabineti, kassa) — brauzer:**

`http://192.168.1.100:8000` → `admin` / (parol) bilan kiring.

**Muhim:**
- Server kompyuter yoqilib turishi shart
- Wi-Fi router internetsiz ham lokal ulanish beradi — internet o'chsa ham web ishlaydi
- Backup: server kompyuterni haftada bir marta external HDD'ga ko'chiring

---

## 3) Bulutda (Docker + nginx + TLS)

Klinika tashqarisidan (uydan/telefondan) kirish uchun. Server ijaraga olish
kerak (masalan, Hetzner / DigitalOcean / Timeweb — oyiga $5-10).

### 3.1 Talablar

- Serverda: Docker + docker-compose
- Domain nomi (masalan, `klinika.example.com`) — DNS A-record server IP'ga qaratilgan
- TLS sertifikat (Let's Encrypt — bepul)

### 3.2 Setup

```bash
git clone https://github.com/arislanars06-design/klinika.git
cd klinika

# 1) Sirlarni tayyorlash
cat > .env <<EOF
CLINIC_WEB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
CLINIC_WEB_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
EOF
chmod 600 .env

# 2) Templates (agar sizning shabloningizni ishlatmoqchi bo'lsangiz)
# ./templates/ papkasiga reception_template.docx qo'ying

# 3) Serverni ishga tushirish
docker compose up -d --build

# 4) Log'ni tekshirish — "Bootstrap admin user 'admin' created" xabarini toping.
docker compose logs web | grep -i bootstrap
```

Endi `http://server-ip:8000` orqali kiring (parolni `.env`dan oling).

### 3.3 TLS bilan (production)

1. Let's Encrypt sertifikatini oling:
   ```bash
   docker run --rm -it \
     -v $PWD/deploy/certs:/etc/letsencrypt \
     -p 80:80 \
     certbot/certbot certonly --standalone -d klinika.example.com
   ```
2. Sertifikat faylini ko'chiring:
   ```bash
   cp deploy/certs/live/klinika.example.com/fullchain.pem deploy/certs/
   cp deploy/certs/live/klinika.example.com/privkey.pem   deploy/certs/
   ```
3. `docker-compose.yml` ichida `nginx` blokini kommentdan chiqaring va
   qayta ishga tushiring:
   ```bash
   docker compose up -d --build
   ```

Endi `https://klinika.example.com` orqali kiring.

### 3.4 Yangilash

```bash
git pull
docker compose up -d --build
```

Baza avtomatik migrate qilinadi (SQLAlchemy `create_all` idempotent).

### 3.5 Backup + restore

- **Avtomatik**: har kuni bir marta `data/backups/clinic_YYYYMMDD.db` yaratiladi
- **Qo'lda**: Sozlamalar → Zaxira → "Hozir zaxira yaratish"
- **Serverdan tashqariga**: `scp` yoki `rsync` bilan `clinic_data` volume'ni
  boshqa mashinaga muntazam ko'chiring:
  ```bash
  docker run --rm -v clinic_data:/data -v $PWD:/backup \
    alpine tar czf /backup/clinic-$(date +%F).tar.gz -C /data .
  ```

---

## Env o'zgaruvchilari (to'liq ro'yxat)

| O'zgaruvchi | Default | Tavsif |
|---|---|---|
| `CLINIC_WEB_PASSWORD` | `clinic` | Bootstrap admin parolini o'rnatadi (faqat 1-marta yoqilganda) |
| `CLINIC_WEB_SECRET` | random | Sessiya cookie imzo kaliti. Restart'da o'zgarmasligi uchun aniq belgilang. |
| `CLINIC_WEB_HOST` | `127.0.0.1` | Bind manzili. LAN uchun `0.0.0.0` |
| `CLINIC_WEB_PORT` | `8000` | Bind porti |
| `CLINIC_WEB_SESSION_MAX_AGE` | `43200` | Sessiya muddati (soniya, default 12 soat) |
| `CLINIC_DATA_DIR` | `data/` | Baza + backup fayllari joyi |

---

## Xavfsizlik tekshiruvi

- [ ] `CLINIC_WEB_PASSWORD` va `CLINIC_WEB_SECRET` production'da o'zgartirilgan
- [ ] `admin` foydalanuvchisining parolini birinchi kirishdan keyin yangilagan
- [ ] Har bir xodim uchun **alohida akkaunt** (bitta parolga bir necha odam kirmasligi kerak)
- [ ] Internet orqali chiqarishdan avval **TLS** (HTTPS) o'rnatilgan
- [ ] Backup faylini boshqa fizik joyga (external HDD / bulut) ko'chirilgan

---

*Hujjat versiyasi: 1.0 · Sana: 2026-07-13*
