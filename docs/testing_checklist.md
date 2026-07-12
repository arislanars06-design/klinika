# ✅ Sinov ro'yxati (Testing Checklist)

Bu hujjat Klinika LOR dasturini **mahalliy mashinada** manual sinash uchun
qadam-baqadam yo'l-yo'riqni beradi. Har bir qadamning kutilgan natijasi
belgilangan — kutilmagan xatti-harakat bo'lsa GitHub Issue oching yoki
xabar bering.

---

## 🚀 0-qadam: Muhitni tayyorlash

**Talablar:** Python 3.11+ va Git.

```bash
git clone https://github.com/arislanars06-design/klinika.git
cd klinika
python -m venv .venv
source .venv/bin/activate            # Linux/macOS
# .venv\Scripts\activate.bat        # Windows PowerShell
pip install -e ".[dev]"
```

**Windows:** Word bilan chop etish uchun **Microsoft Word** yoki **LibreOffice**
o'rnatilgan bo'lishi kerak (dastur `.docx` yaratadi va default handler bilan
ochadi).

**Linux/macOS:** Qt uchun tizim kutubxonalari kerak bo'lishi mumkin:

```bash
# Amazon Linux / Fedora
sudo dnf install -y mesa-libGL mesa-libEGL libxkbcommon fontconfig freetype dbus-libs

# Ubuntu / Debian
sudo apt install -y libgl1 libegl1 libxkbcommon0 libfontconfig1 libfreetype6 libdbus-1-3
```

---

## 🌱 1-qadam: Test ma'lumotlarni yuklash *(ixtiyoriy, lekin tavsiya qilinadi)*

```bash
python scripts/seed_data.py --reset
```

Natija: bazada 2 shifokor, 6 xizmat, 8 bemor va 4 to'lov paydo bo'ladi.
"Toza" tajriba uchun `--reset`siz ishga tushirsangiz, bo'sh bazadan
boshlashingiz mumkin.

---

## 🖥 2-qadam: Dasturni ishga tushirish

```bash
python -m clinic.main
```

**Kutiladi:**
- Birinchi ishga tushirishda **Til tanlash** oynasi (O'ZBEKCHA / РУССКИЙ).
- Keyingi ishga tushirishlarda darhol **Bosh menyu** ochiladi.
- Yuqorida "🏥 LOR klinikasi «Test»" (seed'da o'rnatilgan nom).
- 3 katta tugma: 🩺 Qabulni boshlash · 📋 Bemorlar tarixi · 💰 Kassa
- Pastda: ⚙️ Sozlamalar · ❓ Yordam

---

## ⚙️ 3-qadam: Sozlamalar oynasi

**Klinika tab:**

- [ ] Klinika nomini o'zbekcha va ruscha o'zgartiring → **Saqlash**
- [ ] Bosh menyudagi klinika nomi darhol yangilanadi
- [ ] Til almashtirgichni bosing → butun UI oniy tarjima qilinadi
- [ ] Logo tanlash tugmasini bosing → PNG rasm tanlang → preview'da paydo bo'ladi
- [ ] Backup bo'limi: "Hozir zaxira yaratish" → ✅ muvaffaqiyat xabari, jadvalda yangi qator
- [ ] "Boshqa joyga saqlash..." → tanlangan yo'lga `.db` yaratiladi
- [ ] "Tanlanganini tiklash..." → tasdiq → engine qayta quriladi

**Shifokorlar tab:**

- [ ] "Shifokor qo'shish" → dialog ochiladi
- [ ] Bo'sh F.I.O bilan saqlash → **qizil xato xabari**
- [ ] To'g'ri to'ldirib saqlash → jadvalga qo'shiladi
- [ ] Qatorni tanlab "Arxivlash" → tasdiq → qator kul rang bo'ladi
- [ ] "Tiklash" → yana faol

**Xizmatlar tab:**

- [ ] Yangi xizmat qo'shing (uz + ru + narx) → jadvalga tushadi
- [ ] Xato narx (masalan `abc`) → qabul qilmaydi
- [ ] Manfiy narx → xato

**Kataloglar tab:** M4'da placeholder — kelajakda qo'shiladi.

---

## 🩺 4-qadam: Qabulni boshlash

- [ ] Bosh menyudan **🩺 Qabulni boshlash** ni bosing
- [ ] Bemor F.I.O ga "Ali" yozing → **avtoto'ldirish** ochiladi (seed'dagi bemorlar chiqadi)
- [ ] "Aliyev Anvar" ni tanlang → barcha maydonlar avtomatik to'ldiriladi
- [ ] "Mavjud bemor tanlandi" xabari ko'rinadi (status ostidagi qatorda)
- [ ] Shikoyatlar akkordeoni: **👂 QULOQ** bo'limini oching
- [ ] "Quloqda og'riq" ni belgilang → "Tanlangan: 1 ta" hisoblagichi yangilanadi
- [ ] "Quloqdan ajralma kelishi" ni belgilang → ajralma turi dropdown yoqiladi → "Yiringli"ni tanlang
- [ ] LOR STATUS: **Rinoskopiya** tabi → "Norma" tugmasini bosing → hamma radio maydonlar to'ldiriladi
- [ ] Preview matnida "LOR STATUS: RINOSKOPIYA: ..." ko'rinadi
- [ ] Otoskopiya tabini oching → AD va AS ustunlari yonma-yon ko'rinadi
- [ ] Tashxis: "Otitis media" yozing
- [ ] Shifokorni tanlang
- [ ] **💾 Saqlash** → ✅ muvaffaqiyat → oyna yopiladi
- [ ] Bosh menyuga qaytib **📋 Bemorlar tarixi** → jadval boshida yangi qabul ko'rinadi

**Validatsiya:**

- [ ] Bo'sh F.I.O + tashxissiz "Saqlash" → maydonlar **qizil chegara** bilan belgilanadi
- [ ] Shikoyat tanlanmagan → validatsiya xatosi
- [ ] Shifokor tanlanmagan → xato

---

## 📋 5-qadam: Bemorlar tarixi

- [ ] Jadvalda seed'dagi 8 bemor ko'rinadi
- [ ] "Ali" yozing → filter "Aliyev Anvar" + "Ismoilova Feruza" ni topadi
- [ ] Maydon filtri: "Tashxis" → "Otitis" yozing → 2 ta natija
- [ ] Sana filter checkbox'ni yoqing → 1 hafta oldin bo'yicha filter
- [ ] 👁 tugmasi → **Bemor kartochkasi** ochiladi (qabullar + to'lovlar)
- [ ] Kartochkada ✏ → **Reception oynasi** edit rejimida ochiladi
- [ ] Diagnozni o'zgartirib saqlash → yangilanadi
- [ ] Kartochkada 🖨 → Word hujjat saqlash dialogi
- [ ] Saqlangan `.docx` ni ochib tekshiring — barcha ma'lumotlar mavjud
- [ ] 🗑 → tasdiq → bemor va uning barcha qabullari o'chadi
- [ ] Pagination: 20 dan ortiq bemor bo'lsa Prev/Next ishlaydi

**📊 Statistika:**

- [ ] Statistika tugmasi → dialog ochiladi
- [ ] "Bugun" / "Hafta" / "Oy" / "Yil" ni almashtiring — KPI'lar va grafik yangilanadi
- [ ] TOP tashxislar jadvali — seed'dagi tashxislar ro'yxati
- [ ] 📄 **Word'ga eksport** → hujjat saqlanadi va ochiladi

---

## 💰 6-qadam: Kassa

- [ ] Bosh menyudan **💰 Kassa** → oyna ochiladi
- [ ] "Bemorni tanlash..." → Patient picker dialogi
- [ ] Qidiruvda "Karim" yozing → jadvalda bir bemor
- [ ] "OK" → bemor ma'lumotlari yuklanadi + qabul selector paydo bo'ladi
- [ ] Xizmat combo'dan "Konsultatsiya" ni tanlang → **Qo'shish**
- [ ] Jadvalga qator qo'shiladi, JAMI = 100 000 so'm
- [ ] Sonini 2 ga oshiring → JAMI = 200 000 so'm
- [ ] Yana bir xizmat qo'shing → JAMI qayta hisoblanadi
- [ ] 🗑 qator o'chirish → JAMI kamayadi
- [ ] **💾 To'lovni saqlash** → ✅ muvaffaqiyat
- [ ] **🖨 Kvitansiya** → Word saqlash dialogi
- [ ] `.docx` ni oching — chiroyli jadval bilan

**📊 Kassa statistikasi:**

- [ ] Statistika tugmasi → tushum KPI'lari
- [ ] Xizmatlar bo'yicha jadval to'g'ri hisoblangan
- [ ] Kunlik tushum grafigi ko'rinadi

---

## 🖨 7-qadam: Reception → Kassa oqimi

- [ ] Qabulni boshlash → to'ldirib saqlang
- [ ] **💰 Kassa** tugmasini bosing (Qabul oynasidan)
- [ ] Kassa oynasi bemor + qabul **avtomatik to'ldirilgan** holda ochiladi
- [ ] Xizmat qo'shib saqlang → Reception uchun bog'langan chek yaratiladi
- [ ] Bemor kartochkasida to'lov ko'rinadi

---

## 💾 8-qadam: Backup + Restore

- [ ] Sozlamalar → Klinika → **Hozir zaxira yaratish**
- [ ] Yangi bemor qo'shing
- [ ] Backup ro'yxatidan avvalgi snapshot'ni tanlab **Tanlanganini tiklash**
- [ ] Tasdiqlagach, dastur qayta yuklanadi (o'zi) yoki **dasturni qayta ishga tushiring**
- [ ] Yangi qo'shilgan bemor yo'q — tiklash to'g'ri ishladi
- [ ] `data/clinic.db.old-YYYYMMDD-HHMMSS` fayli mavjud (agar chalkash kelsa, undan qaytadan tiklash mumkin)

---

## 🌍 9-qadam: Ko'p tillilik

- [ ] Har qanday oynada til almashtiring
- [ ] Barcha yorliqlar, tugma matnlari, jadval sarlavhalari darhol tarjima qilinadi
- [ ] Bemor ma'lumotlari **o'zgarmaydi** (matnlar bir xil qoladi — bu to'g'ri)
- [ ] Ruscha rejimda Word chop etish → **KVITANSIYA → КВИТАНЦИЯ**, **ЛОР СТАТУС** va h.k.

---

## 📦 10-qadam: `.exe` yig'ish *(Windows uchun)*

```bash
python scripts/build_exe.py --onefile --clean
```

**Natija:** `dist/ClinicLOR.exe` (~120 MB, bir fayl).

- [ ] Faylni ikki marta bosing → dastur ochiladi
- [ ] `data/`, `templates/` papkalari `.exe` yonida yaratiladi
- [ ] Barcha oqim ishlaydi

Papka rejimi (kichikroq har ishga tushish, lekin ko'p fayl):

```bash
python scripts/build_exe.py
```

**Natija:** `dist/ClinicLOR/` papkasi.

---

## 🐞 Xatolik topsangiz

Har xatolikni **iloji boricha reproducer** bilan yozib bering:
1. Qaysi qadamda? (yuqoridagi ro'yxatdan)
2. Kutilgan xatti-harakat
3. Haqiqiy xatti-harakat
4. Log fayl parchasi — `data/logs/clinic_YYYY-MM-DD.log`
5. Ekran surati (agar UI xatosi)

Loglar `DEBUG` darajasida fayllarga yoziladi — muammoni izlab topish oson.

---

## ✅ Xulosa

Yuqoridagi 10 qadam butun asosiy oqimni qamrab oladi:
- Sozlamalar (klinika, shifokorlar, xizmatlar, backup)
- Qabul (yangi + tahrirlash + shikoyatlar + LOR STATUS + tashxis)
- Bemorlar tarixi (qidiruv + kartochka + statistika)
- Kassa (bemor + qabul + xizmatlar + kvitansiya + statistika)
- Chop etish (5 turdagi Word hujjatlar)
- Backup (avtomatik + qo'lda + tiklash)
- `.exe` paketlash

Barchasi qadam-baqadam ishlagach — dastur klinika foydalanuvchisi qo'liga
berilishga tayyor. 🚀

---

*Hujjat versiyasi: 1.0 · Sana: 2026-07-12*
