# 🩺 Shikoyatlar katalogi

Bu hujjatda dastur ichidagi **standart shikoyatlar katalogi** batafsil keltirilgan. Katalog `src/clinic/catalogs/complaints.json` faylida saqlanadi va dasturga birga jo'natiladi.

Foydalanuvchi qo'shimcha shikoyat qo'sha oladi (Sozlamalar → Kataloglar), ular `complaint_catalog_custom` jadvalida saqlanadi.

---

## 1. Umumiy tuzilma

| Element | Tavsif |
|---------|--------|
| **4 bo'lim** | Quloq, Burun, Halqum, Hiqildoq |
| **30 element** | Standart shikoyatlar |
| **2 til** | O'zbekcha va ruscha |
| **Ajralma turi** | 3 shikoyatga qo'shimcha dropdown |

---

## 2. Katalog (JSON struktura namunasi)

```json
{
  "sections": [
    {
      "code": "ear",
      "icon": "👂",
      "name": {"uz": "QULOQ", "ru": "УШИ"},
      "items": [
        {
          "code": "ear_cosmetic",
          "uz": "Quloq suprasida kosmetik nuqson (shalpang quloqlik, deformatsiya, o'sma, otogematoma)",
          "ru": "Ушная раковина — косметический дефект (лопоухость, деформация, новообразование, отогематома)",
          "has_discharge_type": false
        },
        {
          "code": "ear_discharge",
          "uz": "Quloqdan ajralma kelishi",
          "ru": "Выделения из уха",
          "has_discharge_type": true
        }
      ]
    }
  ]
}
```

---

## 3. To'liq katalog

### 3.1 👂 QULOQ / УШИ

| Kod | O'zbekcha | Русский | Ajralma turi |
|-----|-----------|---------|:---:|
| `ear_cosmetic` | Quloq suprasida kosmetik nuqson (shalpang quloqlik, deformatsiya, o'sma, otogematoma) | Ушная раковина — косметический дефект (лопоухость, деформация, новообразование, отогематома) | — |
| `ear_pain` | Quloqda og'riq | Боль в ухе | — |
| `ear_noise` | Quloqda shovqin | Шум в ушах | — |
| `ear_hearing_loss` | Eshitish pasayishi | Снижение слуха | — |
| `ear_congestion` | Quloq bitishi | Заложенность уха | — |
| `ear_discharge` | Quloqdan ajralma kelishi | Выделения из уха | ✅ |
| `ear_itching` | Quloqda qichishish | Зуд в ухе | — |
| `ear_discomfort` | Quloqda noqulaylik hissi | Чувство дискомфорта | — |

### 3.2 👃 BURUN VA YONDOSH BURUN BO'SHLIQLARI / НОС И ОКОЛОНОСОВЫЕ ПАЗУХИ

| Kod | O'zbekcha | Русский | Ajralma turi |
|-----|-----------|---------|:---:|
| `nose_cosmetic` | Kosmetik nuqson yoki hosila | Косметический дефект, образования | — |
| `nose_congestion` | Burun bitishi | Заложенность носа | — |
| `nose_breathing` | Burun orqali nafas olishning qiyinlashishi | Затруднение дыхания через нос | — |
| `nose_discharge` | Burundan ajralma kelishi | Выделения из носа | ✅ |
| `nose_itching` | Burunda qichishish | Зуд в носу | — |
| `nose_pain` | Burun og'rig'i | Боль в носу | — |
| `nose_trigeminal_pain` | Uch shoxli nervning I–II shoxlari chiqish nuqtalarida og'riq | Болезненность точек выхода I–II ветвей тройничного нерва | — |
| `nose_face_heaviness` | Yuz sohasida og'irlik hissi | Тяжесть в области лица | — |

### 3.3 😮 HALQUM / ГЛОТКА

| Kod | O'zbekcha | Русский | Ajralma turi |
|-----|-----------|---------|:---:|
| `pharynx_pain` | Tomoq og'rig'i | Боль в горле | — |
| `pharynx_tickling` | Qirilish yoki achishish hissi | Першение | — |
| `pharynx_itching` | Qichishish | Зуд | — |
| `pharynx_lump` | «Tomoqda tugun» hissi | Чувство «комка» | — |
| `pharynx_foreign_body` | «Begona jism» hissi | Чувство инородного тела | — |
| `pharynx_discharge` | Ajralma | Отделяемое | ✅ |
| `pharynx_swallowing` | Yutishning qiyinlashishi | Затрудненное глотание | — |
| `pharynx_cough` | Yo'tal | Кашель | — |

### 3.4 🗣 HIQILDOQ / ГОРТАНЬ

| Kod | O'zbekcha | Русский | Ajralma turi |
|-----|-----------|---------|:---:|
| `larynx_voice_change` | Ovoz funksiyasining o'zgarishi (xirillash, bo'g'ilish, ovoz yo'qolishi) | Изменение голосовой функции (охриплость, осиплость, афония) | — |
| `larynx_cough` | Yo'tal | Кашель | — |
| `larynx_pain` | Og'riq | Боль | — |
| `larynx_foreign_body` | Begona jism hissi | Чувство инородного тела | — |
| `larynx_breathing` | Nafas olishning qiyinlashishi | Затрудненное дыхание | — |
| `larynx_swallowing` | Yutishning qiyinlashishi | Затрудненное глотание | — |

---

## 4. Ajralma turlari (Discharge types)

`has_discharge_type: true` bo'lgan shikoyatlar tanlanganda quyidagi dropdown chiqadi:

| Kod | O'zbekcha | Русский |
|-----|-----------|---------|
| `purulent` | Yiringli | Гнойное |
| `serous` | Seroz | Серозное |
| `mucous` | Shilliq | Слизистое |
| `mucopurulent` | Shilliq-yiringli | Слизисто-гнойное |
| `bloody` | Qonli | Кровянистое |
| `sanguineous` | Suvli-qonli | Сукровичное |
| `caseous` | Kazeoz | Казеозное |
| `watery` | Suvli | Водянистое |
| `other` | Boshqa (matn) | Другое |

**Qoidalar:**
- ✅ "other" tanlanganda **erkin matn maydoni** ochiladi
- ✅ Bir vaqtda faqat bitta tur tanlanadi (radio)
- ⚠️ Ajralma tanlangan bo'lsa, turi kiritilishi majburiy emas (agar aniq bo'lmasa qoldirsa bo'ladi)

---

## 5. Validatsiya qoidalari

### 5.1 Saqlash paytida

- ✅ **Kamida bittasi:** yoki checkbox tanlangan bo'lishi kerak, yoki qo'shimcha erkin matn to'ldirilgan
- ❌ Ikkalasi bo'sh bo'lsa — saqlashga ruxsat berilmaydi, xato xabari ko'rsatiladi:
  - **uz:** "Kamida bitta shikoyatni tanlang yoki qo'shimcha matn kiriting"
  - **ru:** "Выберите хотя бы одну жалобу или введите дополнительный текст"

### 5.2 Ma'lumot butunligi

- Katalog kodlari o'zgartirilmaydi (backward compatibility)
- Yangi shikoyat qo'shilsa — yangi kod (`custom_` prefiksi bilan)
- O'chirilgan shikoyatlar `is_active=false` bo'ladi, lekin eski qabullarda ko'rinadi

---

## 6. Matn shakllantirish (chop etish uchun)

Tanlangan shikoyat kodlari **tabiiy tibbiy matn**ga aylantiriladi.

### 6.1 O'zbekcha misol

**Tanlangan:**
```json
{
  "complaints_codes": ["ear_pain", "ear_noise", "nose_congestion", "pharynx_discharge"],
  "complaints_details": {"pharynx_discharge": "purulent"},
  "complaints_note": "3 kundan beri, kunduzi kuchayadi"
}
```

**Chiqadi (chop etishda):**
```
SHIKOYATLAR:

Quloq: quloqda og'riq, quloqda shovqin.
Burun: burun bitishi.
Halqum: ajralma (yiringli).

Qo'shimcha: 3 kundan beri, kunduzi kuchayadi.
```

### 6.2 Ruscha misol

**Chiqadi:**
```
ЖАЛОБЫ:

Уши: боль в ухе, шум в ушах.
Нос: заложенность носа.
Глотка: отделяемое (гнойное).

Дополнительно: беспокоит 3 дня, усиливается днём.
```

### 6.3 Algoritm

1. `complaints_codes` bo'yicha shikoyat bo'limlarini guruhlash
2. Har bir bo'lim uchun matnni yaratish:
   - Bo'lim sarlavhasi (Quloq / Burun / Halqum / Hiqildoq)
   - `:` dan keyin vergul bilan ajratilgan shikoyatlar
   - Agar `has_discharge_type=true` bo'lsa — `(turi)` qo'shiladi
3. `complaints_note` bo'lsa — "Qo'shimcha: ..." bilan qo'shiladi

---

## 7. Bemorlar tomonidan aytilishi (yumshoq shakl)

Chop etishda shikoyatlarni "bemor aytadi" tarzida yozish uchun (agar shifokor xohlasa) shablon o'zgartirilishi mumkin:

**Shakl 1 (nominal, standart):**
> "Quloqda og'riq, quloqda shovqin."

**Shakl 2 (predikativ):**
> "Bemor quloqda og'riqqa, quloqda shovqinga shikoyat qiladi."

Sozlamalarda tanlash imkoniyati bo'lishi mumkin. Boshida **Shakl 1** ishlatiladi.

---

## 8. Katalog kengaytmalari (kelajakda)

- 🔮 **Bola/kattaga alohida shikoyatlar** — pediatriyaga xos qatorlar
- 🔮 **Shikoyat davomiyligi** — har bir shikoyatga vaqt (kun, hafta, oy)
- 🔮 **Kuchayish/pasayish holati** — belgilar
- 🔮 **ICD-10 kodlari bilan bog'lash**

---

*Hujjat versiyasi: 1.0 · Sana: 2026-07-12*
