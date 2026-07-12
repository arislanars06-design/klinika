# 🏥 Klinika LOR — O'rnatish yo'riqnomasi

Bu hujjat klinikada dasturni o'rnatishni **bosqichma-bosqich** ko'rsatadi. Texnik bilim shart emas — har bir buyruqni ko'chirib qo'yishingiz kifoya.

---

## 1. Kompyuter tayyorlash

**Talab:** Klinikada bitta kompyuter (Windows 10/11 yoki Linux).

Bu kompyuter **"server"** vazifasini bajaradi — dastur shu yerda ishlaydi. Boshqa kompyuterlar (registratura, shifokor xonalari) brauzer orqali unga ulanadi.

**Tavsiya:** Server kompyuteri doim yoqilgan holda tursin (kuchlanish uzilishida ham davom etishi uchun UPS bo'lsa yaxshi).

---

## 2. Python o'rnatish

### Windows uchun

1. [https://www.python.org/downloads/](https://www.python.org/downloads/) sahifasiga o'ting
2. **"Download Python 3.11"** tugmasini bosing
3. Yuklab olingan faylni ishga tushiring
4. ⚠️ **MUHIM:** "Add Python to PATH" katakchasini belgilashni unutmang
5. "Install Now" bosing va tugashini kuting

### Linux uchun (Ubuntu/Amazon Linux)

```bash
sudo dnf install -y python3.11 python3.11-pip
# yoki Ubuntu'da:
sudo apt install -y python3.11 python3.11-venv python3-pip
```

---

## 3. Dasturni yuklab olish

### Variant A — GitHub'dan (tavsiya qilinadi)

```bash
cd /opt              # yoki C:\ (Windows'da)
git clone https://github.com/arislanars06-design/klinika.git clinic-lor
cd clinic-lor
```

### Variant B — ZIP fayl

1. GitHub sahifasidan **"Code"** → **"Download ZIP"**
2. Faylni `C:\clinic-lor\` (yoki Linux'da `/opt/clinic-lor/`) papkasiga chiqaring
3. Buyruq satrida shu papkaga o'ting

---

## 4. Dasturni sozlash

Papka ichida quyidagi buyruqlarni birma-bir bajaring:

```bash
# 1. Virtual muhit yaratish
python3.11 -m venv .venv

# 2. Muhitni faollashtirish
# Linux/Mac uchun:
source .venv/bin/activate
# Windows uchun:
.venv\Scripts\activate

# 3. Dasturni o'rnatish
pip install -e .

# 4. Boshlang'ich ma'lumotlarni yuklash (klinika nomi, xizmatlar, shifokorlar)
python -m scripts.seed_data
```

---

## 5. Dasturni ishga tushirish

```bash
python -m clinic.main --host 0.0.0.0
```

**Sinash:** shu kompyuterda brauzerni ochib `http://127.0.0.1:8000/` manziliga o'ting.

Klinika ichidagi boshqa kompyuterlar bilan ulanish uchun:
- Server kompyuterining lokal IP manzilini bilib oling (masalan `192.168.1.10`)
- Boshqa kompyuterda brauzer ochib `http://192.168.1.10:8000/` yozing

---

## 6. Doim ishlab turadigan xizmatga aylantirish

### Linux (systemd)

```bash
sudo useradd -r -s /bin/false clinic
sudo chown -R clinic:clinic /opt/clinic-lor
sudo cp deploy/clinic-lor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now clinic-lor
sudo systemctl status clinic-lor
```

### Windows (Task Scheduler)

1. **"Task Scheduler"** dasturini oching
2. **"Create Basic Task"** → nom: "Klinika LOR"
3. Trigger: "When the computer starts"
4. Action: "Start a program"
5. Program: `C:\clinic-lor\.venv\Scripts\python.exe`
6. Arguments: `-m clinic.main --host 0.0.0.0`
7. Start in: `C:\clinic-lor`

---

## 7. Ma'lumotlarni zaxiralash (backup)

Har kuni avtomatik zaxira nusxa yaratish uchun:

### Linux (cron)

```bash
crontab -e
# Quyidagi qatorni qo'shing (har kuni soat 23:00'da):
0 23 * * * /opt/clinic-lor/.venv/bin/python -m scripts.backup
```

### Windows (Task Scheduler)

- Har kuni soat 23:00'da `.venv\Scripts\python.exe -m scripts.backup` ishga tushirilsin

Zaxira fayllar `data/backups/` papkasida saqlanadi va 30 kundan eski nusxalar avtomatik o'chiriladi.

---

## 8. Klinika ma'lumotlarini kiritish

Brauzerda `http://127.0.0.1:8000/settings` manziliga o'ting va:

1. **Klinika ma'lumotlari** — nomi, manzili, telefon
2. **Shifokorlar** — F.I.O va telefon (yangi yoki mavjudlarni tahrirlash)
3. **Xizmatlar** — nomi va narxi (namuna xizmatlar allaqachon mavjud)

---

## 9. Chop etish shabloni

Klinikangizning **Word shablonini** (agar bor bo'lsa) `templates/reception_template.docx` fayl nomi bilan `templates/` papkasiga qo'ying.

Placeholder'lar (o'zgaradigan qismlar):
- `{{ clinic.name }}`, `{{ clinic.address }}`, `{{ clinic.phone }}`
- `{{ reception.date }}`
- `{{ patient.full_name }}`, `{{ patient.birth_year }}`, `{{ patient.age }}`, `{{ patient.address }}`, `{{ patient.phone }}`
- `{{ reception.complaints }}`, `{{ reception.anamnesis }}`, `{{ reception.lor_status }}`, `{{ reception.diagnosis }}`, `{{ reception.recommendation }}`
- `{{ doctor.full_name }}`, `{{ doctor.phone }}`

Agar shablon yo'q bo'lsa — dastur o'zining oddiy standart shaklini ishlatadi (avtomatik yaratiladi).

---

## 10. Docker orqali (ilg'or foydalanuvchilar uchun)

Agar Docker o'rnatilgan bo'lsa, hammasini bitta buyruq bilan ishga tushirish mumkin:

```bash
docker compose up -d
```

Bu holda dastur `http://<server-ip>:8000/` orqali kirish mumkin.

---

## ❓ Muammolar

### Brauzer sahifani ochmayapti
- Server kompyuterida dastur ishlab turibdimi? (buyruq oynasida loglar chiqib turishi kerak)
- Antivirus yoki Windows Firewall to'sib qo'ymadimi? (portni ochib qo'ying)

### "Port already in use" xatosi
- Boshqa dastur portni band qilgan. Buyruqqa `--port 8001` qo'shib boshqa raqamdan foydalaning

### Ma'lumotlar yo'qolib qoldi
- `data/clinic.db` faylni `data/backups/` papkasidan tiklang

---

## 📞 Yordam

Muammo yuzaga kelsa:
1. `data/logs/` papkasidagi so'nggi log faylini oching
2. Xato xabarini olib, ishlab chiquvchiga yuboring

**Muvaffaqiyatli ish!** 🩺
