# 📦 Paketlash (Build) yo'riqnomasi

Ushbu hujjat **Clinic LOR** dasturini bitta `.exe` yoki papka shaklida
paketlash tartibini tavsiflaydi. Asosiy vosita — **PyInstaller** (`pyproject.toml`
`[project.optional-dependencies].dev` ichida).

## Talablar

- **Python 3.11** (asosiy tavsiya). Loyiha `.python-version` bilan `3.11.15`
  ni tanlaydi.
- **PyInstaller ≥ 6.3** — `pip install -e ".[dev]"` bilan o'rnatiladi.
- **Windows 10/11** yakuniy `.exe` ni yaratish uchun (mos platformada
  yig'ish shart, `.exe` boshqa OS'da to'g'ridan-to'g'ri chiqarilmaydi).

## Tez boshlash

```bash
pip install -e ".[dev]"
python scripts/build_exe.py            # dist/ClinicLOR/ (papka rejimi)
python scripts/build_exe.py --onefile  # dist/ClinicLOR.exe (yagona fayl)
python scripts/build_exe.py --clean    # avval build/ + dist/ ni tozalaydi
```

Skript orqasidan PyInstaller `clinic.spec` faylini o'qib chiqadi. `ONEFILE`
muhit o'zgaruvchisi orqali papka/yagona rejim tanlanadi (skript avtomatik
sozlaydi).

## Nima birga paketlanadi

- `src/clinic/catalogs/*.json` — shikoyatlar va LOR STATUS kataloglari.
- `src/clinic/i18n/*.json` — o'zbek + rus tarjimalari (270 kalit).
- `templates/` — foydalanuvchi Word shablonlari (agar bo'sh bo'lmasa).

Ma'lumotlar bazasi (`data/clinic.db`), log fayllari va zaxira nusxalar
foydalanuvchi kompyuterida birinchi ishga tushirishda avtomatik yaratiladi.

## Papka rejimi natijasi

```
dist/
└── ClinicLOR/
    ├── ClinicLOR.exe        # asosiy dastur
    ├── _internal/           # Python + kutubxonalar
    ├── clinic/
    │   ├── catalogs/*.json
    │   └── i18n/*.json
    └── templates/           # shablonlar (agar mavjud bo'lsa)
```

Butun `ClinicLOR/` papkasini foydalanuvchi kompyuteriga ko'chirib qo'yish
kifoya. Papka ichida `ClinicLOR.exe` fayli ishga tushiriladi.

Birinchi ishga tushirishda dastur o'zi yaratadi:
- `data/clinic.db` — ma'lumotlar bazasi
- `data/backups/` — kunlik zaxiralar
- `data/logs/` — kunlik log fayllar

## Yagona fayl rejimi (`--onefile`)

`dist/ClinicLOR.exe` — bitta ~120 MB fayl. Ishga tushganda vaqtincha papka
ochiladi va u yerdan yuklanadi. Yuklash biroz sekinroq.

## Foydalanuvchi Word shablonlarini qo'shish

Klinika bo'yicha maxsus Word shablon jo'natilganda uni `templates/` papkasiga
qo'ying va qayta yig'ing:

| Fayl nomi                              | Vazifasi                               |
|----------------------------------------|-----------------------------------------|
| `templates/reception_template.docx`    | Qabul varaqasi                         |
| `templates/receipt_template.docx`      | Kassa kvitansiyasi                     |
| `templates/patients_stats_template.docx` | Bemorlar statistikasi eksporti       |
| `templates/cashier_stats_template.docx` | Kassa statistikasi eksporti          |

Placeholder ro'yxati:
[`docs/template_placeholders.md`](template_placeholders.md).

Shablonlar bo'lmasa dastur o'z ichida qat'iy standart layoutdan foydalanadi —
hech narsa ishlamay qolmaydi.

## Inno Setup o'rnatuvchisi (ixtiyoriy)

Windows uchun oddiy `.msi` yoki `.exe` o'rnatuvchi yaratish uchun
[Inno Setup](https://jrsoftware.org/isinfo.php) yordamida:

1. `dist/ClinicLOR/` papkasini tayyorlang.
2. Inno Setup Compiler'da yangi skript yarating, `Source: dist\ClinicLOR\*`
   qo'shing, `Icon: <ico fayl>` va Start Menu yorlig'i belgilang.
3. Kompilyatsiya qilib chiqarilgan `.exe` ni foydalanuvchiga bering.

Skript namunasi keyingi milestone doirasida ishlab chiqiladi.

## Xatoliklar

| Muammo                                       | Yechim                                     |
|----------------------------------------------|--------------------------------------------|
| `ModuleNotFoundError: sqlalchemy.dialects.sqlite` | `clinic.spec` `collect_submodules` bilan hal etiladi — spec faylini o'zgartirmang. |
| `matplotlib` fontlari yuklanmaydi           | Windows 10/11 default fontlari yetarli — muammo Linux'da yuz beradi. |
| `docxtpl` shablonini o'qiy olmaydi          | `.docx` binaryda `{{placeholder}}` yozuvi buzilgan — Word'da ochib qayta saqlang. |
| `.exe` katta hajmda                          | UPX (`upx=True`) allaqachon yoqilgan. Yagona-faylda ~120 MB oddiy hol. |

## CI / Avtomatlashtirish

`scripts/build_exe.py` ni bevosita GitHub Actions Windows runner'ida
chaqirish mumkin:

```yaml
- uses: actions/setup-python@v5
  with: { python-version: '3.11' }
- run: pip install -e ".[dev]"
- run: python scripts/build_exe.py --onefile --clean
- uses: actions/upload-artifact@v4
  with:
    name: ClinicLOR-windows
    path: dist/ClinicLOR.exe
```

---

*Hujjat versiyasi: 1.0 · Sana: 2026-07-12*
