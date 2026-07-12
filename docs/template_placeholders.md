# 📝 Word shabloni placeholder'lari

`templates/` papkasidagi `.docx` shablonlari **Jinja2** (docxtpl) sintaksisidan
foydalanadi. Quyida har bir shablon uchun mavjud kalitlar keltirilgan.

Placeholder yozuvlari standart docxtpl formatidadir:

```
{{ patient.full_name }}
{% for item in items %}{{ item.service }}: {{ item.total }}{% endfor %}
```

---

## 1. `reception_template.docx` — Qabul varaqasi

### Klinika

| Kalit                | Namuna                              |
|----------------------|-------------------------------------|
| `clinic.name`        | LOR klinikasi                       |
| `clinic.address`     | Toshkent sh., Yunusobod ...         |
| `clinic.phone`       | +998 71 XXX XX XX                   |
| `clinic.logo_path`   | Absolute path (fayl yo'li)          |
| `clinic.logo`        | `InlineImage` (docxtpl orqali)      |

### Bemor

| Kalit                | Namuna                              |
|----------------------|-------------------------------------|
| `patient.id`         | `42`                                |
| `patient.full_name`  | Aliyev Anvar                        |
| `patient.birth_year` | `1990`                              |
| `patient.age`        | `36`                                |
| `patient.address`    | Toshkent, Yunusobod                 |
| `patient.phone`      | +998 90 XXX XX XX                   |

### Qabul (reception)

| Kalit                              | Namuna |
|------------------------------------|--------|
| `reception.id`                     | `123` |
| `reception.date`                   | `12.07.2026 10:30` |
| `reception.complaints_text`        | Erkin matn — kompozitsiya |
| `reception.complaints_codes`       | `["ear_pain", "ear_discharge"]` |
| `reception.complaints_note`        | Erkin matn |
| `reception.anamnesis`              | Erkin matn |
| `reception.lor_status_text`        | Ko'p qatorli matn (RINOSKOPIYA, ...) |
| `reception.diagnosis`              | Erkin matn (**majburiy**) |
| `reception.recommendation`         | Erkin matn |

### Shifokor

| Kalit                | Namuna                              |
|----------------------|-------------------------------------|
| `doctor.full_name`   | Karimov Ali                         |
| `doctor.phone`       | +998 90 XXX XX XX                   |

### Umumiy

- `today` — hujjat yaratilgan sana (`12.07.2026`).
- `lang` — joriy til (`uz` / `ru`).

---

## 2. `receipt_template.docx` — Kassa kvitansiyasi

### Klinika + Bemor

Yuqoridagi bilan bir xil (`clinic.*`, `patient.*`).

### Kvitansiya

| Kalit                | Namuna                              |
|----------------------|-------------------------------------|
| `receipt.id`         | `1234` (birinchi qator ID'si)       |
| `receipt.date`       | `12.07.2026 10:45`                  |
| `receipt.note`       | Barcha qatorlar izohlari birlashgan |

### Xizmatlar (loop)

```
{% for item in items %}
{{ item.num }} | {{ item.service }} | {{ item.quantity }} | {{ item.price }} | {{ item.total }}
{% endfor %}
```

| Kalit             | Namuna                    |
|-------------------|---------------------------|
| `item.num`        | `1`                       |
| `item.service`    | Konsultatsiya             |
| `item.quantity`   | `1`                       |
| `item.price`      | `100 000` (space-formatted) |
| `item.total`      | `100 000`                  |

### Yakuniy

| Kalit                | Namuna                              |
|----------------------|-------------------------------------|
| `grand_total`        | `250 000`                           |
| `currency`           | `so'm` yoki `сум`                   |

---

## 3. `patients_stats_template.docx` — Bemorlar statistikasi

### Umumiy

| Kalit                         | Namuna                    |
|-------------------------------|---------------------------|
| `clinic.name`, `.address`, ... | Yuqoridagi bilan bir xil |
| `period.start`                | `01.07.2026`              |
| `period.end`                  | `31.07.2026`              |
| `period.label`                | `01.07.2026 — 31.07.2026` |

### KPI'lar

| Kalit                            | Namuna |
|----------------------------------|--------|
| `kpis.total_patients`            | `42`   |
| `kpis.new_patients`              | `12`   |
| `kpis.repeat_receptions`         | `30`   |

### TOP tashxislar (loop)

```
{% for row in top_diagnoses %}
{{ row.diagnosis }} — {{ row.count }}
{% endfor %}
```

### Kunlar bo'yicha (loop)

```
{% for row in by_day %}
{{ row.date }} — {{ row.value }}
{% endfor %}
```

`row.value` — kun uchun qabullar soni (`float`, matnda `int` sifatida
ko'rsating: `{{ row.value|int }}`).

---

## 4. `cashier_stats_template.docx` — Kassa statistikasi

### KPI'lar

| Kalit                          | Namuna       |
|--------------------------------|--------------|
| `kpis.total_revenue`           | `5 250 000`  |
| `kpis.payment_count`           | `42`         |
| `kpis.receipts_count`          | `18`         |
| `kpis.average_receipt`         | `291 666.67` |
| `currency`                     | `so'm`       |

### Xizmatlar bo'yicha (loop)

```
{% for row in by_service %}
{{ row.service }} | {{ row.units }} | {{ row.revenue }} {{ currency }}
{% endfor %}
```

### Kunlar bo'yicha

```
{% for row in by_day %}
{{ row.date }} — {{ row.value }} {{ currency }}
{% endfor %}
```

---

## Shablonlarni sinash

Shablonni tayyorlagach quyidagi Python skript orqali sinash mumkin:

```python
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from clinic.printing.docx_builder import save_reception_document
from clinic.domain.dto import ReceptionDTO, PatientDTO, DoctorDTO

# ... test ma'lumotlarni yig'ing va save_reception_document ga bering ...
```

Yoki dastur ichida real qabul yaratib, "Chop etish" tugmasini bosing —
shablon `templates/` papkasida bo'lsa avtomatik ishlatiladi.

---

## O'z shablonini tayyorlash

`templates/reception_template.docx` fayli **klinika sarlavhasi** (nomi,
xizmatlar ro'yxati, manzil, telefonlar) hamda `docxtpl` placeholder'lari
bilan tayyorlangan. Uni istagan vaqtingizda MS Word'da ochib:

1. Sarlavha (logo, klinika ma'lumotlari, ranglar, shrift) ni o'zgartirishingiz mumkin.
2. Placeholder'lar (`{{ patient.full_name }}`, `{{ reception.diagnosis }}`, ...) **matnda saqlanib qolishi kerak** — aks holda bu joyga real ma'lumot yozilmaydi.
3. Fayl yaratilgan `scripts/build_reception_template.py` skript orqali qayta yaratish uchun:
   ```bash
   python scripts/build_reception_template.py
   ```

Agar shablonni butunlay o'chirsangiz, dastur avtomatik ravishda o'zining
**default** renderer (python-docx orqali chiroyli, minimal hujjat) ga
o'tadi. Har ikkalasi ham bir xil kontekstdan foydalanadi — mos kelmaslik
yo'q.

---

*Hujjat versiyasi: 1.1 · Sana: 2026-07-12*
