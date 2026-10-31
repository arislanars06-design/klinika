# NURMED — LOR klinikasi tizimi

Klinikaning lokal tarmog'ida ishlaydigan web-tizim: qabul (elektron LOR karta), bemorlar tarixi, kassa, hisobotlar, xodimlar va rollar, audit, zaxira nusxalari.

## Qanday ishlaydi

- Bitta **markaziy kompyuter (server)** dasturni ishga tushiradi. Barcha ma'lumot shu kompyuterdagi bitta bazada (`data/nurmed.db`, SQLite) saqlanadi.
- Boshqa kompyuterlar (shifokor, registrator, kassa) **brauzer** orqali `http://<server-IP>:3000` manzilini ochadi. Ularga hech narsa o'rnatilmaydi.
- Qo'shimcha kutubxona kerak emas: faqat Node.js.

## O'rnatish (server kompyuterda)

1. [Node.js](https://nodejs.org) **22.13 yoki undan yangi** versiyasini o'rnating (LTS, 22 yoki 24).
2. `nurmed` papkasini kompyuterga ko'chiring.
3. Shu papkada terminal ochib, quyidagini ishga tushiring:
   ```
   npm start
   ```
4. Birinchi ishga tushirishda terminalda **administrator logini (`admin`) va vaqtinchalik parol** chiqadi. Kirgandan keyin tizim parolni almashtirishni talab qiladi.
5. Server kompyuterning IP manzilini aniqlang (Windows: `ipconfig`) va boshqa kompyuterlarda `http://192.168.x.x:3000` ni oching.
6. Server kompyuterga **doimiy IP** bering (routerda) va Windows Firewall'da 3000-portni faqat lokal tarmoq uchun oching.
7. Server kompyuter yoqilganda dastur o'zi ishga tushishi va PowerShell oynasisiz ishlashi uchun pastdagi **«Windows'da fonda ishlatish»** bo'limiga qarang.

## Windows'da fonda ishlatish (PowerShell oynasisiz)

`windows` papkasidagi fayllar serverni Task Scheduler'dagi **NURMED** vazifasi qilib o'rnatadi:

- kompyuter yoqilganda server o'zi ishga tushadi (hech kim tizimga kirmasa ham);
- oyna ochilmaydi, PowerShell'ni yopsangiz ham sayt ishlayveradi;
- server to'xtab qolsa, 1 daqiqadan keyin qayta ishga tushadi;
- jurnal `data\logs\server.log` fayliga yoziladi (10 MB dan oshsa `server.old.log` ga o'tadi).

| Fayl (ikki marta bosing) | Vazifasi |
|---|---|
| `windows\install.bat` | **Bir marta**: o'rnatadi va ishga tushiradi. Ochiq `npm start` oynasi bo'lsa, uni o'zi to'xtatadi. 3000-portni lokal tarmoq uchun ochadi |
| `windows\update.bat` | Yangilash: `git pull` qiladi va serverni qayta ishga tushiradi |
| `windows\restart.bat` | Serverni qayta ishga tushiradi |
| `windows\status.bat` | Holat, sayt manzillari va jurnalning oxirgi qatorlari |
| `windows\uninstall.bat` | Vazifani olib tashlaydi (ma'lumotlar o'chmaydi) |

Har bir fayl administrator huquqini so'raydi: «Ҳа / Да / Yes» ni bosing.

Eslatmalar:
- Server **SYSTEM** hisobida ishlaydi. «Word fayllar saqlanadigan papka» uchun lokal diskni ko'rsating (masalan, `D:\NURMED\Ҳужжатлар`). Tarmoq diskiga (`Z:\` kabi) SYSTEM yoza olmaydi.
- Windows tarmog'i **«Общественная / Public»** turida bo'lsa, firewall qoidasi ishlamaydi. Tarmoqni «Частная / Private» qiling.
- Birinchi o'rnatishda administratorning vaqtinchalik paroli oynada emas, `data\logs\server.log` faylida bo'ladi.

### Sozlamalar (muhit o'zgaruvchilari)

| O'zgaruvchi | Standart | Vazifasi |
|---|---|---|
| `PORT` | `3000` | Port |
| `HOST` | `0.0.0.0` | Tinglanadigan manzil |
| `NURMED_DATA_DIR` | `./data` | Baza va zaxira papkasi |
| `NURMED_BACKUP_DIR` | `./data/backups` | Zaxira nusxalar papkasi (masalan, ikkinchi disk) |
| `NURMED_BACKUP_KEEP` | `30` | Saqlanadigan avtomatik nusxalar soni |
| `NURMED_TZ` | `Asia/Tashkent` | Vaqt mintaqasi |
| `NURMED_SESSION_HOURS` | `12` | Sessiya muddati |
| `NURMED_TLS_CERT`, `NURMED_TLS_KEY` | — | Berilsa, HTTPS yoqiladi |

## Rollar

| Rol | Nima qila oladi |
|---|---|
| Administrator | **Barcha huquqlar**: qabul o'tkazish (shifokor sifatida), bemorni ro'yxatga olish, kassa, hisobotlar, hamda xodimlar, narxlar, rekvizitlar, audit va zaxira nusxalari |
| Shifokor | Bemor kartasi, qabul, shikoyat, LOR STATUS, tashxis, tavsiya, chop etish, CSV eksport, **kassa (hisob, to'lov, qaytarish, kunlik hisobot)** va qabul hamda moliyaviy statistika |
| Registrator | Bemorni ro'yxatga olish, shifokor navbatiga yozish, qidiruv. Tibbiy yozuvlarni ko'rmaydi |
| Kassir | Hisob, to'lov, qisman to'lov, qaytarish, bekor qilish, chek, kunlik hisobot, moliyaviy statistika. Tibbiy yozuvlarni ko'rmaydi |

Huquqlar **serverda** tekshiriladi.

## Interfeys

- Interfeys tili: o'zbekcha (kirill yozuvida) va ruscha. Tepadagi "Ўзб / Рус" tugmasi bilan almashtiriladi.
- Kunduzgi va tungi rejim: tepadagi quyosh/oy tugmasi. Tanlov brauzerda saqlanadi. Birinchi ochilganda kompyuterning o'z rejimi olinadi.
- Yangi qabul bitta oynada: **Паспорт маълумотлари** → shikoyatlar → LOR STATUS (metodlar tablarda) → tashxis va tavsiya. Bemor F.I.Sh. yoki telefoni yozilganda bazadagi mos bemorlar taklif qilinadi; tanlanmasa, saqlashda yangi bemor kartasi avtomatik ochiladi.
- Pastdagi amallar paneli: Сақлаш, Якунлаш, Сақлаш ва чоп этиш, **Касса** (qabulni saqlab, shu bemor va qabul bilan yangi hisob ochadi).

## Chop etish

- **"Созламалар → Клиника → Чоп этиш усули"**:
  - **Word** (standart): "Чоп этиш" tugmasi hujjatni A5 o'lchamli `.docx` fayl qilib yuklab beradi. Uni Word'da tahrirlab, chop etasiz.
  - **Brauzer**: "Чоп этиш" brauzerning chop etish oynasini ochadi (A5). Bu rejimda yonida alohida "Word" tugmasi ham bo'ladi.
- Word fayl o'zi ochilishi uchun har bir kompyuterda bir marta sozlang: Chrome yoki Edge'da yuklab olingan fayl yonidagi «⋯» (yoki strelka) → **«Всегда открывать файлы этого типа»**.

## Kassa chegirmalari

Har bir xizmatga "Чегирма гуруҳи" belgilanadi ("Созламалар → Хизматлар ва нархлар"). Chegirma kassada avtomatik hisoblanadi, server ham qayta hisoblaydi. Qoidalar `public/js/pricing.js` faylida:

- **ЛОР кўриги + муолажалар** (томоқ/бурун ювиш, қулоқ тозалаш, лимфотроп блокада): 1 ta → 70 000, 2 ta → 100 000, keyingi har biri +35 000.
- **Капельница**: 1 ta → 25 000, 2 ta va ko'p → har biri 20 000.
- **Венадан секин**: yolg'iz bitta → 15 000; 2 ta va ko'p yoki капельница / мушак орасига bilan birga → har biri 10 000.

## Word fayllar papkasi

"Созламалар → Клиника → Word файллар сақланадиган папка" maydoniga server kompyuterdagi to'liq yo'lni yozing (masalan, `D:\NURMED\Ҳужжатлар`). Shunda har bir Word faylning nusxasi shu papkaga oy bo'yicha ichki papkalarga (`2026-10`, `2026-11` …) yoziladi. Brauzer boshqa kompyuterlarda faylni baribir o'sha kompyuterning "Загрузки" papkasiga yuklaydi.

## Asosiy qoidalar

- Bemor kartasi bitta, qabullar alohida. Yangi qabul eskisini ustidan yozmaydi.
- LOR STATUSda tanlanmagan maydon "norma" deb to'ldirilmaydi va hujjatga chiqmaydi.
- Qabul va hisoblar o'chirilmaydi, sabab ko'rsatilib **bekor qilinadi**. Har bir o'zgarish (kim, qachon, nima o'zgardi) audit jurnaliga yoziladi. Tibbiy yozuvni ko'rish va chop etish ham qayd etiladi.
- Jami = Σ(narx × miqdor) − chegirma. Summani server qayta hisoblaydi.
- Uzcard yoki Humo tanlash pul bankka tushganini tasdiqlamaydi. Bank integratsiyasi yo'q.
- Chek klinikaning ichki cheki, fiskal chek emas.

## Zaxira nusxasi va tiklash

- Server har 24 soatda `data/backups/` papkasiga bazaning to'liq nusxasini oladi. Administrator "Sozlamalar → Zaxira nusxalari" bo'limida qo'lda nusxa olishi va yuklab olishi mumkin.
- Nusxalarni muntazam **boshqa qurilmaga** (tashqi disk, ikkinchi kompyuter) ko'chiring.
- **Tiklash:** serverni to'xtating, `data/nurmed.db` faylini (va bo'lsa `nurmed.db-wal`, `nurmed.db-shm` fayllarini) boshqa joyga olib qo'ying, kerakli nusxani `data/nurmed.db` nomi bilan joylashtiring va serverni qayta ishga tushiring.
- Tiklashni oyiga kamida bir marta boshqa kompyuterda sinab ko'ring.

## Haqiqiy bemorlar bilan ishlashdan oldin

- Server kompyuterga parol qo'ying, diskni shifrlang (BitLocker), unga faqat administrator kirsin.
- Portni internetga ochmang. Tizim faqat lokal tarmoq uchun mo'ljallangan.
- Lokal tarmoqda ham HTTPS yoqish tavsiya etiladi (`NURMED_TLS_CERT` / `NURMED_TLS_KEY`).
- Zaxira nusxasini boshqa qurilmaga ko'chirish va tiklash tartibini sinab ko'ring.
- Shaxsiy va tibbiy ma'lumotlarni saqlash bo'yicha O'zbekiston qonunchiligi talablarini yurist bilan tekshiring.

## Tuzilishi

```
nurmed/
├── server/
│   ├── server.js      HTTP server, sessiya, CSRF himoyasi
│   ├── routes.js      API: bemorlar, qabullar, kassa, hisobotlar, xodimlar, audit
│   ├── db.js          Baza sxemasi: users, sessions, patients, visits, services,
│   │                  invoices, invoice_items, payments, audit_logs, settings
│   ├── security.js    Parollar (scrypt), sessiyalar, rollar, kirishga urinishlarni cheklash
│   ├── backup.js      Zaxira nusxalari
│   └── http.js        Router, xavfsizlik sarlavhalari, statik fayllar
└── public/
    ├── index.html, css/app.css
    └── js/
        ├── lor-template.js   Shikoyatlar, LOR STATUS va tashxislar shabloni (uz/ru)
        ├── i18n.js           Interfeys matnlari (uz/ru)
        ├── core.js, main.js
        └── views/            Bosh oyna, qabul, tarix, kassa, hisobotlar, sozlamalar
```

Shikoyatlar, ajralma turlari va LOR STATUS katalogi eski "Clinic LOR Desktop" dasturidan (`src/clinic/catalogs/*.json`) ko'chirilgan. O'zbekcha matnlar lotin yozuviga o'girilgan. LOR STATUS 4 ta metoddan iborat: rinoskopiya, faringoskopiya, otoskopiya (AD va AS alohida) va laringoskopiya. Shartli maydonlar saqlangan: masalan, deformatsiya turi faqat "Deformatsiya" tanlanganda chiqadi, baraban bo'shlig'i esa faqat perforatsiya bo'lsa ko'rinadi. Tekshirilmagan maydon avtomatik "norma" deb yozilmaydi. Har bir metodda "Norma (bo'sh maydonlarga)" tugmasi bor, uni shifokor o'zi bosadi. Tugma faqat bo'sh maydonlarga norma variantini qo'yadi, shifokor tanlagan qiymatlarni o'zgartirmaydi. Shartli maydonlarni (masalan, gipertrofiya darajasini) ham to'ldirmaydi. Shuning uchun avval patologiyani belgilab, keyin "Norma" tugmasini bosish mumkin.

Variantlarni `public/js/lor-template.js` faylida o'zgartirish mumkin. Server saqlashdan oldin ma'lumotni shu shablon bo'yicha tekshiradi.

## Hali yo'q (keyingi bosqichlar)

- Bank yoki to'lov provayderi integratsiyasi, fiskal chek.
- Kassa smenasini ochish va yopish (hozir kunlik hisobot bor).
- Telegram bildirishnomalari.
- Avtomatik testlar to'plami.
