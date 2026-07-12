# 🔬 LOR STATUS katalogi

Bu hujjatda LOR ko'rigining strukturaviy shakli batafsil keltirilgan. 4 asosiy ko'rik metodi bo'yicha guruhlangan:

1. **РИНОСКОПИЯ / RINOSKOPIYA** — burun va burun-halqum
2. **ФАРИНГОСКОПИЯ / FARINGOSKOPIYA** — og'iz va oral halqum
3. **ОТОСКОПИЯ / OTOSKOPIYA** — quloqlar (AD/AS alohida)
4. **ЛАРИНГОСКОПИЯ / LARINGOSKOPIYA** — hiqildoq-halqum va hiqildoq

**Muhim:** LOR STATUS **majburiy emas** — bo'sh saqlash mumkin. "Norma" tugmasi barcha bo'limlarni normal holatga o'tkazadi.

---

## 1. Katalog tuzilishi (JSON namunasi)

```json
{
  "methods": [
    {
      "code": "rhinoscopy",
      "icon": "👃",
      "name": {"uz": "RINOSKOPIYA", "ru": "РИНОСКОПИЯ"},
      "sections": [
        {
          "code": "external_nose",
          "name": {"uz": "Tashqi burun", "ru": "Наружный нос"},
          "fields": [
            {
              "code": "state",
              "type": "radio",
              "options": [
                {"code": "unchanged", "uz": "O'zgarmagan", "ru": "Не изменен", "is_norm": true},
                {"code": "deformed", "uz": "Deformatsiya", "ru": "Деформация"}
              ]
            },
            {
              "code": "deformity_type",
              "type": "checkbox_multi",
              "visible_when": {"state": "deformed"},
              "options": [
                {"code": "sunken", "uz": "Cho'kish", "ru": "Западение"},
                {"code": "hump", "uz": "Bukrilik", "ru": "Горбинка"},
                {"code": "scoliosis", "uz": "Skolioz", "ru": "Сколиоз"}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 2. Element turlari

| Turi | Tavsif | UI |
|------|--------|-----|
| `radio` | Bittasini tanlash (bir-birini istisno qiladi) | ○ ○ ○ |
| `checkbox_multi` | Ko'p tanlash mumkin | ☐ ☐ ☐ |
| `side` | Tomon (chap/o'ng/ikkalasi) | 3 tugma |
| `degree` | Daraja (yo'q, I, II, III) | 4 radio |
| `text` | Erkin matn | Input |

**Qo'shimcha atributlar:**
- `is_norm: true` — "Norma" tugmasi bosilganda avtomatik tanlanadi
- `visible_when` — boshqa maydonga bog'liq shartli ko'rsatish
- `required: false` — barcha maydonlar ixtiyoriy (standart)

---

## 3. РИНОСКОПИЯ / RINOSKOPIYA

### 3.1 Tashqi burun / Наружный нос

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | O'zgarmagan (norma) / Deformatsiya |
| Deformatsiya turi | checkbox_multi (agar Deformatsiya) | Cho'kish, Bukrilik, Skolioz |
| Tomon | side | Chap / O'ng / Ikkalasi |
| Qismi | radio | Suyak qismi / Tog'ay qismi |
| Joylashuvi | checkbox_multi | Burun orqasi, Qanotlari, Uchi, Burun teshiklari |

### 3.2 Uch shoxli nerv chiqish nuqtalari (I–II–III shoxlar)

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Og'riqsiz (norma) / Og'riqli |
| Tomon (og'riqli bo'lsa) | side | Chap / O'ng / Ikkalasi |
| Shox (og'riqli bo'lsa) | checkbox_multi | I / II / III |

### 3.3 Burun orqali nafas olish / Дыхание через нос

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Erkin (norma) / Qiyinlashgan / Mavjud emas |
| Tomon | side | Chap / O'ng / Ikkalasi |

### 3.4 Burun dahlizi / Преддверие

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | O'zgarmagan (norma) / Toraygan |
| Tomon (toraygan bo'lsa) | side | Chap / O'ng / Ikkalasi |

### 3.5 Hid bilish / Обоняние

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Saqlangan (norma) / Giposmiya / Anosmiya / Giperosmiya |
| Tomon | side | Chap / O'ng / Ikkalasi |

### 3.6 Shilliq qavat / Слизистая оболочка

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Rang | radio | Pushti (norma) / Oqartirilgan pushti / Ko'kimtir / Giperemiyalangan |
| Namlik | radio | Nam (norma) / Quruq |
| Holati | checkbox_multi | Gipertrofiyalangan, Yaralangan |
| Joylashuvi | checkbox_multi | Burun to'sig'i sohasi, Pastki chig'anoq, O'rta chig'anoq, Yuqori chig'anoq, Pastki burun yo'li, O'rta burun yo'li, Yuqori burun yo'li, Oldingi uchi, Orqa uchi |

### 3.7 Burun to'sig'i / Носовая перегородка

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | O'rta chiziqda (norma) / Qiyshaygan |
| Xarakteri | checkbox_multi | Bo'rtma, Qirra, Tikancha |
| Shakli | radio | C-simon / S-simon |
| Tomon | side | Chap / O'ng |
| Qismi | radio | Tog'ay qismida / Suyak qismida |

### 3.8 Orqa rinoskopiya / Burun-halqum (Задняя риноскопия / Носоглотка)

**Xoanalar:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Erkin (norma) / Yopilgan |
| Sabab | checkbox_multi | Pastki chig'anoqlar gipertrofiyasi, O'rta chig'anoqlar gipertrofiyasi, Polip, O'sma, Adenoidlar |

**Gumbaz:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Erkin (norma) / O'sma / Adenoidlar |
| Adenoid darajasi | degree | I / II / III |
| Shilliq qavat | radio | Nam, pushti (norma) / O'zgargan |

**Eshituv naylari og'zi:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Yaxshi ko'rinadi, erkin (norma) / Toraygan |
| Tarkibi | checkbox_multi | Shilliq, Yiring |
| Boshqa | checkbox | Nay valiklari va bodomsimon bezlar gipertrofiyasi |

---

## 4. ФАРИНГОСКОПИЯ / FARINGOSKOPIYA

### 4.1 Og'iz bo'shlig'i / Полость рта

**Og'iz ochilishi:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Erkin (norma) / Trizm / Og'riqli |

**Og'iz shilliq qavati:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Rang | radio | Oqartirilgan pushti (norma) / Giperemiyalangan |
| Patologiya | checkbox_multi | Aftalar, Yaralar |
| Joylashuvi | checkbox_multi | Til, Yumshoq tanglay, Og'iz tubi |

**Til:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Toza, nam (norma) / Oq karash bilan qoplangan |
| Patologiya | checkbox_multi | Afta, Yara, Infiltratsiya |
| Og'riq | radio | Yo'q (norma) / Bor |
| Tomon | side | Chap / O'ng / Ikkalasi |

**Tishlar:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Sog'lom (norma) / Sanatsiya qilingan / Karies |
| Boshqa | checkbox | Protezlar mavjud |

### 4.2 Oral halqum / Ротоглотка

**Tanglay yoylari:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Ko'rinishi | radio | Yaxshi ko'rinadi (norma) / O'zgargan |
| Patologiya | checkbox_multi | Shishgan, Giperemiyalangan, Infiltratsiyalangan, Bodomsimon bez bilan yopishgan |
| Boshqa | checkbox_multi | Yostiqsimon bo'rtish, Giss burmasi qalinlashgan |

**Tanglay bodomsimon bezlari:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Tanglay yoyidan chiqmaydi (norma) / Gipertrofiya |
| Gipertrofiya darajasi | degree | I / II / III |
| Yuza | radio | Silliq (norma) / G'adir-budir |
| Lakunalar | radio | Kengaymagan (norma) / Kengaygan |
| Lakunalar tarkibi | checkbox_multi | Yo'q (norma), Kazeoz tiqinlar, Yiringli tiqinlar, Shilliq tiqinlar, Yiring, Shilliq |

**Halqum orqa devori:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Pushti, silliq (norma) / O'zgargan |
| Patologiya | checkbox_multi | Limfoid granulalar gipertrofiyasi, Yon valiklar gipertrofiyasi, Atrofiya |
| Tarkibi | checkbox_multi | Yiring, Qobiqlar, Shilliq, Qon |

**Halqum refleksi:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Saqlangan (norma) / Pasaygan / Yuqori |

---

## 5. ОТОСКОПИЯ / OTOSKOPIYA

**Otoskopiya har ikkala quloq uchun alohida to'ldiriladi: `AD` (o'ng, Auris Dextra) va `AS` (chap, Auris Sinistra).**

**"Ikkalasi bir xil"** tugmasi — bir tomonni to'ldirib, ikkinchisiga nusxa ko'chirishga imkon beradi.

### 5.1 Quloq suprasi va tashqi eshituv yo'li

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Shakli | radio | To'g'ri shaklda (norma) / O'zgargan |
| Kengligi | radio | Normal (norma) / Keng / Tor |
| Patologiya | checkbox_multi | Ekzostoz, Og'riq, Infiltratsiya, Giperemiya |
| Qismi (og'riqli bo'lsa) | radio | Suyak qismi / Tog'ay qismi |
| Tarkibi | checkbox_multi | Toza (norma), Oltingugurt, Qobiqlar, Tiqin, Yiring, Qon, Pardalar |

### 5.2 Baraban pardasi

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Rang | radio | Marvaridsimon kulrang (norma) / Giperemiyalangan |
| Belgilar | radio | Yaxshi ko'rinadi (norma) / Yaxshi ko'rinmaydi |
| Perforatsiya | radio | Yo'q (norma) / Chekka / Markaziy |
| Patologiya | checkbox_multi | Pulsatsiyalovchi refleks, Infiltratsiya, Retraksiya, Chandiqlar, Kalsinatlar |

### 5.3 Baraban bo'shlig'i (perforatsiya bo'lgan holatda ko'rinadi)

| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Tarkibi | checkbox_multi | Yiring, Granulyatsiyalar, Polip, Xolesteatoma massalari, Qon |

---

## 6. ЛАРИНГОСКОПИЯ / LARINGOSKOPIYA

### 6.1 Hiqildoq-halqum / Гортаноглотка

**Til bodomsimon bezi:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Kattalashmagan (norma) / Kattalashgan |
| Boshqa | checkbox_multi | Karash yo'q (norma), Giperemiyalangan |

**Vallekulalar:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Erkin (norma) / O'zgargan |
| Rang | radio | Oqartirilgan pushti (norma) / Giperemiyalangan |

**Orqa va yon devorlar:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Rang | radio | Oqartirilgan pushti (norma) / Giperemiyalangan |
| Patologiya | checkbox_multi | Shishgan, Infiltratsiyalangan |

### 6.2 Hiqildoq / Гортань

**Tashqi ko'rik:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Konturi | radio | Yaxshi konturlanadi (norma) / O'zgargan |
| Harakat | radio | Passiv harakatchan (norma) / Harakatsiz |
| Shakli | radio | To'g'ri shaklda (norma) / Deformatsiya |
| «Tog'ay qirsillashi» simptomi | radio | Manfiy (norma) / Musbat |

**Ovoz boylamlari:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Rang | radio | Oqartirilgan (norma) / Giperemiyalangan |
| Toza/patologiya | radio | Toza (norma) / Karashlar mavjud / O'sma / Gipertrofiya |
| Fonatsiyada yopilish | radio | To'liq yopiladi (norma) / To'liq yopilmaydi |
| Harakat | radio | Erkin (norma) / Harakati cheklangan / Harakatsiz |
| Tomon (agar patologiya bo'lsa) | side | Chap / O'ng / Ikkalasi |

**Ovoz:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Jarangdor (norma) / Xirillagan / Afoniya |

**Hansirash:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Holati | radio | Yo'q (norma) / Bor |
| Turi | radio | Inspirator / Ekspirator / Aralash |
| Vaqti | radio | Tinch holatda / Yuklamada |

**Hiqildoq stenozi:**
| Maydon | Turi | Variantlar |
|--------|------|-----------|
| Darajasi | degree | Yo'q (norma) / I / II / III |

---

## 7. "Norma" tugmasi logikasi

Foydalanuvchi **"Norma"** tugmasini bosganda quyidagilar sodir bo'ladi:

1. Barcha 4 metod (rinoskopiya, faringoskopiya, otoskopiya, laringoskopiya) bo'ylab yuriladi
2. Har bir maydonda `is_norm: true` deb belgilangan variant tanlanadi
3. Ochiq bo'lgan tabli qismlar ham to'ldiriladi
4. Otoskopiyada AD va AS uchun ham norma qo'yiladi
5. Preview matnda ko'rinadi:

```
Rinoskopiya: Tashqi burun o'zgarmagan. Uch shoxli nerv chiqish 
nuqtalari og'riqsiz. Burun orqali nafas olish erkin. Hid bilish 
saqlangan. Burun dahlizi o'zgarmagan. Shilliq qavat pushti, nam. 
Burun to'sig'i o'rta chiziqda. Xoanalar erkin. Gumbaz erkin.

Faringoskopiya: Og'iz ochilishi erkin. Og'iz shilliq qavati 
oqartirilgan pushti. Til toza, nam. Tishlar sog'lom.
Tanglay yoylari yaxshi ko'rinadi. Tanglay bodomsimon bezlari 
tanglay yoyidan chiqmaydi. Halqum orqa devori pushti, silliq. 
Halqum refleksi saqlangan.

Otoskopiya:
  AD (o'ng): Quloq suprasi to'g'ri shaklda. Tashqi eshituv yo'li 
  toza. Baraban pardasi marvaridsimon kulrang, belgilari yaxshi 
  ko'rinadi. Perforatsiya yo'q.
  AS (chap): [xuddi shu matn]

Laringoskopiya: Til bodomsimon bezi kattalashmagan. Vallekulalar 
erkin. Orqa va yon devorlar oqartirilgan pushti. Hiqildoq yaxshi 
konturlanadi, passiv harakatchan. Ovoz boylamlari oqartirilgan, 
toza, fonatsiyada to'liq yopiladi. Ovoz jarangdor. Hansirash yo'q. 
Stenoz yo'q.
```

---

## 8. Matn shakllantirish algoritmi

Har bir bo'lim uchun **shablonli jumla** shakllantiriladi:

```
{bo'lim_nomi}: {maydon1_matni} {maydon2_matni} ... 
```

Har bir maydon uchun **shablonlar**:

**Namuna (rinoskopiya → tashqi burun):**
- `state=unchanged` → `"Tashqi burun o'zgarmagan."`
- `state=deformed` (with details) → `"Tashqi burun deformatsiyalashgan (bukrilik), o'ng tomonda, suyak qismida."`

**Namuna (otoskopiya → baraban pardasi):**
- `color=pearly_gray, marks=visible, perforation=none` → `"Baraban pardasi marvaridsimon kulrang, belgilari yaxshi ko'rinadi."`
- `color=hyperemic, perforation=central` → `"Baraban pardasi giperemiyalangan, markaziy perforatsiya."`

Kod dagi `TextComposer` klassi bu logikani bajaradi.

---

## 9. Preview real vaqtda

Har bir checkbox/radio o'zgarganda matn qayta hisoblanadi va **pastki panelda** ko'rsatiladi:

```
┌──────────────────────────────────────────────┐
│ [Tab: Rinoskopiya]                           │
│ ...                                          │
├──────────────────────────────────────────────┤
│ 📋 KO'RINISH (real vaqtda):                  │
│ Rinoskopiya: Tashqi burun deformatsiyalashgan│
│ (bukrilik), o'ng tomonda, suyak qismida.     │
│ Burun orqali nafas olish qiyinlashgan.       │
│ ...                                          │
└──────────────────────────────────────────────┘
```

---

## 10. Baza saqlanishi

`receptions.lor_status` maydonida to'liq JSON saqlanadi:

```json
{
  "rhinoscopy": {
    "external_nose": {
      "state": "deformed",
      "deformity_type": ["hump"],
      "side": "right",
      "part": "bone",
      "location": ["dorsum"]
    },
    "trigeminal": {"state": "painless"},
    "breathing": {"state": "free"},
    "vestibule": {"state": "unchanged"},
    "olfaction": {"state": "preserved"},
    "mucosa": {
      "color": "pink",
      "moisture": "moist",
      "condition": [],
      "location": []
    },
    "septum": {"state": "midline"},
    "posterior": {
      "choanae": {"state": "free"},
      "vault": {"state": "free"},
      "tubes": {"state": "well_visible"}
    }
  },
  "pharyngoscopy": { ... },
  "otoscopy": {
    "AD": { ... },
    "AS": { ... }
  },
  "laryngoscopy": { ... }
}
```

Faqat to'ldirilgan bo'limlar saqlanadi (bo'sh bo'limlar `null` yoki umuman yo'q).

---

## 11. Kelajakdagi kengaytmalar

- 🔮 **Shablonlar** (v2): "Surunkali tonzillit", "Otit media", "Rinit" kabi tez-tez uchraydigan holatlar uchun tayyor to'plamlar
- 🔮 **Fotosuratlar** — otoskopiya rasm biriktirish
- 🔮 **Audiometriya natijasi** — alohida jadval
- 🔮 **Endoskopik rasm** — bir vaqtda rasm biriktirish

---

*Hujjat versiyasi: 1.0 · Sana: 2026-07-12*
