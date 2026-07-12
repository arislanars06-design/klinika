# 🗄 Ma'lumotlar bazasi sxemasi

**Baza:** SQLite 3
**ORM:** SQLAlchemy 2.0
**Migratsiya:** Alembic

---

## 1. Umumiy sxema (ER diagramma)

```
┌─────────────┐         ┌───────────────┐         ┌──────────────┐
│  patients   │─────< ──│  receptions   │─────>───│   doctors    │
└─────────────┘         └───────────────┘         └──────────────┘
                              │
                              │
                              ▼
                        ┌────────────────────┐         ┌──────────────┐
                        │ cashier_records    │─────>───│   services   │
                        └────────────────────┘         └──────────────┘

┌─────────────┐    ┌─────────────────────────┐    ┌──────────────────┐
│  settings   │    │ complaint_catalog_custom│    │ lor_catalog_custom│
└─────────────┘    └─────────────────────────┘    └──────────────────┘
```

---

## 2. Jadvallar

### 2.1 `patients` — Bemorlar

| Ustun | Turi | Cheklovlar | Izoh |
|-------|------|-----------|------|
| `id` | INTEGER | PK, AUTO | |
| `full_name` | TEXT | NOT NULL, INDEXED | F.I.O |
| `birth_year` | INTEGER | NOT NULL | 1900 – joriy yil |
| `address` | TEXT | NULL | Yashash manzili |
| `phone` | TEXT | NULL | `+998XXXXXXXXX` |
| `created_at` | DATETIME | NOT NULL, default=NOW | Birinchi kelgan sanasi |
| `updated_at` | DATETIME | NOT NULL, default=NOW | Oxirgi tahrir |

**Indekslar:**
- `idx_patients_full_name` — F.I.O bo'yicha qidiruv uchun
- `idx_patients_phone` — telefon qidiruv
- `idx_patients_created` — statistika uchun

---

### 2.2 `doctors` — Shifokorlar

| Ustun | Turi | Cheklovlar | Izoh |
|-------|------|-----------|------|
| `id` | INTEGER | PK, AUTO | |
| `full_name` | TEXT | NOT NULL | |
| `phone` | TEXT | NULL | |
| `is_active` | BOOLEAN | NOT NULL, default=TRUE | Ishdanmi |
| `created_at` | DATETIME | NOT NULL, default=NOW | |

---

### 2.3 `receptions` — Qabullar

| Ustun | Turi | Cheklovlar | Izoh |
|-------|------|-----------|------|
| `id` | INTEGER | PK, AUTO | |
| `patient_id` | INTEGER | FK → patients(id), NOT NULL, ON DELETE CASCADE | |
| `doctor_id` | INTEGER | FK → doctors(id), NOT NULL | |
| `reception_date` | DATETIME | NOT NULL, INDEXED | Qabul sanasi |
| **Shikoyatlar** | | | |
| `complaints_codes` | JSON | NOT NULL | `["ear_pain", "nose_congestion"]` |
| `complaints_details` | JSON | NULL | `{"ear_discharge": "purulent", ...}` |
| `complaints_note` | TEXT | NULL | Qo'shimcha erkin matn |
| **Boshqa maydonlar** | | | |
| `anamnesis` | TEXT | NULL | |
| `lor_status` | JSON | NULL | To'liq LOR STATUS (4 bo'lim) |
| `diagnosis` | TEXT | NOT NULL | Tashxis |
| `recommendation` | TEXT | NULL | Tavsiya |
| **Metadata** | | | |
| `created_at` | DATETIME | NOT NULL, default=NOW | |
| `updated_at` | DATETIME | NOT NULL, default=NOW | |

**Indekslar:**
- `idx_receptions_date` — statistika va filtr
- `idx_receptions_patient` — bemor tarixi
- `idx_receptions_diagnosis` — tashxis bo'yicha qidiruv

**JSON namunalar:**

```json
// complaints_codes
["ear_pain", "ear_noise", "nose_congestion"]

// complaints_details
{
  "ear_discharge": "purulent",
  "nose_discharge": "mucous"
}

// lor_status (soddalashtirilgan)
{
  "rhinoscopy": {
    "external_nose": {"state": "unchanged"},
    "breathing": {"state": "free"},
    "olfaction": {"state": "preserved"},
    "mucosa": {"color": "pink", "moisture": "moist"},
    "septum": {"state": "midline"}
  },
  "pharyngoscopy": {...},
  "otoscopy": {
    "AD": {...},
    "AS": {...}
  },
  "laryngoscopy": {...}
}
```

---

### 2.4 `services` — Xizmatlar katalogi

| Ustun | Turi | Cheklovlar | Izoh |
|-------|------|-----------|------|
| `id` | INTEGER | PK, AUTO | |
| `name_uz` | TEXT | NOT NULL | O'zbekcha nomi |
| `name_ru` | TEXT | NOT NULL | Ruscha nomi |
| `price` | DECIMAL(12,2) | NOT NULL | So'mda |
| `is_active` | BOOLEAN | NOT NULL, default=TRUE | |
| `created_at` | DATETIME | NOT NULL, default=NOW | |
| `updated_at` | DATETIME | NOT NULL, default=NOW | |

---

### 2.5 `cashier_records` — Kassa yozuvlari

| Ustun | Turi | Cheklovlar | Izoh |
|-------|------|-----------|------|
| `id` | INTEGER | PK, AUTO | |
| `patient_id` | INTEGER | FK → patients(id), NOT NULL | |
| `reception_id` | INTEGER | FK → receptions(id), NULL | Ixtiyoriy bog'lanish |
| `service_id` | INTEGER | FK → services(id), NOT NULL | |
| `quantity` | INTEGER | NOT NULL, default=1 | |
| `price_at_moment` | DECIMAL(12,2) | NOT NULL | O'sha paytdagi narx |
| `total` | DECIMAL(12,2) | NOT NULL | quantity × price_at_moment |
| `paid_at` | DATETIME | NOT NULL, default=NOW, INDEXED | |
| `note` | TEXT | NULL | |

**Indekslar:**
- `idx_cashier_paid` — statistika
- `idx_cashier_patient` — bemor to'lovlar tarixi

**Muhim:** Bitta to'lovda bir necha xizmat bo'lsa — har bir xizmat **alohida qator** sifatida yoziladi. Bu statistika uchun qulay.

---

### 2.6 `settings` — Dastur sozlamalari

**Key-Value formatda:**

| Ustun | Turi | Cheklovlar |
|-------|------|-----------|
| `key` | TEXT | PK |
| `value` | TEXT | NOT NULL |

**Standart kalitlar:**

| Kalit | Qiymat namunasi |
|-------|-----------------|
| `language` | `uz` yoki `ru` |
| `clinic_name_uz` | "LOR klinikasi" |
| `clinic_name_ru` | "ЛОР клиника" |
| `clinic_address_uz` | "Toshkent sh., Yunusobod, ..." |
| `clinic_address_ru` | "г. Ташкент, Юнусабад, ..." |
| `clinic_phone` | `+998 71 XXX XX XX` |
| `clinic_logo_path` | `data/logo.png` |
| `first_run_done` | `true` |
| `last_backup_date` | `2026-07-12` |

---

### 2.7 `complaint_catalog_custom` — Foydalanuvchi qo'shgan shikoyatlar

Standart shikoyatlar **dastur ichida qat'iy** (JSON fayl), lekin foydalanuvchi qo'shimcha shikoyat qo'shishi mumkin.

| Ustun | Turi | Cheklovlar | Izoh |
|-------|------|-----------|------|
| `id` | INTEGER | PK, AUTO | |
| `code` | TEXT | UNIQUE, NOT NULL | `custom_ear_pressure` |
| `section` | TEXT | NOT NULL | `ear`, `nose`, `pharynx`, `larynx` |
| `name_uz` | TEXT | NOT NULL | |
| `name_ru` | TEXT | NOT NULL | |
| `has_discharge_type` | BOOLEAN | default=FALSE | Ajralma turi kerakmi |
| `is_active` | BOOLEAN | default=TRUE | |
| `created_at` | DATETIME | default=NOW | |

---

### 2.8 `lor_catalog_custom` — Foydalanuvchi qo'shgan LOR STATUS bandlari

| Ustun | Turi | Cheklovlar | Izoh |
|-------|------|-----------|------|
| `id` | INTEGER | PK, AUTO | |
| `code` | TEXT | UNIQUE, NOT NULL | |
| `method` | TEXT | NOT NULL | `rhinoscopy`/`pharyngoscopy`/`otoscopy`/`laryngoscopy` |
| `section` | TEXT | NOT NULL | Kichik bo'lim, masalan `external_nose` |
| `field_type` | TEXT | NOT NULL | `radio` / `checkbox` / `text` |
| `label_uz` | TEXT | NOT NULL | |
| `label_ru` | TEXT | NOT NULL | |
| `options_json` | JSON | NULL | Radio/checkbox variantlari |
| `is_active` | BOOLEAN | default=TRUE | |

---

## 3. Munosabatlar (Relationships)

```
patients (1) ─── (N) receptions        [ON DELETE CASCADE]
doctors  (1) ─── (N) receptions        [ON DELETE RESTRICT]

patients (1) ─── (N) cashier_records   [ON DELETE CASCADE]
services (1) ─── (N) cashier_records   [ON DELETE RESTRICT]
receptions(1) ─ (0..N) cashier_records [ON DELETE SET NULL]
```

**Qoidalar:**
- Bemor o'chirilsa — barcha qabul va to'lovlari ham o'chadi (kaskad)
- Shifokorni o'chirib bo'lmaydi — faqat `is_active=false` (soft delete)
- Xizmat o'chirilsa — kassa yozuvlari qoladi (RESTRICT); soft delete tavsiya
- Qabul o'chirilsa — unga bog'liq to'lovlar bemorda qoladi (`reception_id = NULL`)

---

## 4. Migratsiyalar (Alembic)

**Boshlang'ich versiya:**
- `001_initial.py` — barcha jadvallar
- `002_seed_default_services.py` — standart xizmatlar (konsultatsiya, audiometriya...)

**Kelajakdagi versiyalar (namuna):**
- `003_add_patient_photos.py` — bemor rasmlari (v2)
- `004_add_users_table.py` — login/parol (v2)

---

## 5. Baza fayl joylashuvi

```
<dastur_papkasi>/data/clinic.db
<dastur_papkasi>/data/backups/clinic_YYYYMMDD.db
```

**Backup logikasi:**
- Har kuni dastur ochilganda joriy sana bilan backup yaratiladi
- Agar shu kunning backup'i mavjud bo'lsa — takrorlanmaydi
- 30 kundan eski backup'lar o'chiriladi

---

## 6. Statistika so'rovlari (namuna SQL)

### 6.1 Bemorlar statistikasi

```sql
-- Davrdagi jami bemorlar (noyob)
SELECT COUNT(DISTINCT patient_id) 
FROM receptions 
WHERE reception_date BETWEEN :start AND :end;

-- Yangi bemorlar (birinchi marta kelgan)
SELECT COUNT(*) 
FROM patients 
WHERE created_at BETWEEN :start AND :end;

-- TOP tashxislar
SELECT diagnosis, COUNT(*) AS cnt
FROM receptions
WHERE reception_date BETWEEN :start AND :end
GROUP BY diagnosis
ORDER BY cnt DESC
LIMIT 10;

-- Shikoyatlar bo'yicha (JSON qidiruv)
SELECT json_each.value AS code, COUNT(*) AS cnt
FROM receptions, json_each(receptions.complaints_codes)
WHERE reception_date BETWEEN :start AND :end
GROUP BY json_each.value
ORDER BY cnt DESC;
```

### 6.2 Kassa statistikasi

```sql
-- Jami tushum
SELECT SUM(total) 
FROM cashier_records 
WHERE paid_at BETWEEN :start AND :end;

-- Xizmatlar bo'yicha
SELECT 
    s.name_uz,
    COUNT(*) AS records_cnt,
    SUM(cr.quantity) AS units_sold,
    SUM(cr.total) AS revenue
FROM cashier_records cr
JOIN services s ON cr.service_id = s.id
WHERE cr.paid_at BETWEEN :start AND :end
GROUP BY s.id
ORDER BY revenue DESC;

-- O'rtacha chek (bemor+qabul bo'yicha)
SELECT AVG(reception_total) FROM (
    SELECT SUM(total) AS reception_total
    FROM cashier_records
    WHERE paid_at BETWEEN :start AND :end
    GROUP BY patient_id, reception_id
);
```

---

## 7. Ma'lumotlar butunligi (Integrity)

- **Referential integrity** — barcha FK to'g'ri ishlashi kerak
- **Check constraints:**
  - `patients.birth_year BETWEEN 1900 AND 2100`
  - `cashier_records.quantity > 0`
  - `cashier_records.total = quantity * price_at_moment`
- **Trigger'lar** (SQLite'da) — `updated_at` avtomatik yangilanadi

---

## 8. Migratsiya strategiyasi

- Har o'zgarish yangi Alembic revision
- Dastur ishga tushganda joriy versiyani tekshiradi, kerak bo'lsa `alembic upgrade head`
- Migratsiya oldidan avtomatik backup

---

*Hujjat versiyasi: 1.0 · Sana: 2026-07-12*
