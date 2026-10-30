'use strict';
/*
 * Markaziy ma'lumotlar bazasi (SQLite, Node.js ichki moduli node:sqlite).
 * Fayl: data/nurmed.db. Barcha kompyuterlar shu server orqali bitta bazaga ulanadi.
 */
const fs = require('node:fs');
const path = require('node:path');
const { DatabaseSync } = require('node:sqlite');

const DATA_DIR = process.env.NURMED_DATA_DIR || path.join(__dirname, '..', 'data');
const DB_PATH = path.join(DATA_DIR, 'nurmed.db');

fs.mkdirSync(DATA_DIR, { recursive: true });

const db = new DatabaseSync(DB_PATH);
db.exec('PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA busy_timeout = 5000;');
// SQLite'ning LIKE va NOCASE faqat lotin harflarida katta-kichik harfni farqlamaydi.
// Kirill (Алиев = алиев) qidiruvi uchun Unicode kichik harfga o'tkazuvchi funksiya.
db.function('ulower', { deterministic: true }, (v) => (v === null || v === undefined ? v : String(v).toLowerCase()));

const SCHEMA = `
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash TEXT NOT NULL,
  full_name TEXT NOT NULL,
  roles TEXT NOT NULL,                 -- JSON massiv: ["doctor","admin"]
  phone TEXT NOT NULL DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1,
  must_change_password INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  created_at TEXT NOT NULL,
  expires_at INTEGER NOT NULL          -- unix ms
);

CREATE TABLE IF NOT EXISTS patients (
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE,
  full_name TEXT NOT NULL,
  birth_date TEXT NOT NULL DEFAULT '', -- YYYY yoki YYYY-MM-DD
  gender TEXT NOT NULL DEFAULT '',     -- '', 'm', 'f'
  phone TEXT NOT NULL DEFAULT '',
  address TEXT NOT NULL DEFAULT '',
  archived INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  created_by INTEGER REFERENCES users(id),
  updated_at TEXT,
  updated_by INTEGER REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(full_name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);

CREATE TABLE IF NOT EXISTS visits (
  id INTEGER PRIMARY KEY,
  patient_id INTEGER NOT NULL REFERENCES patients(id),
  doctor_id INTEGER REFERENCES users(id),
  visit_at TEXT NOT NULL,              -- mahalliy vaqt: YYYY-MM-DD HH:MM:SS
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','done','cancelled')),
  complaints TEXT NOT NULL DEFAULT '[]',
  complaints_text TEXT NOT NULL DEFAULT '',
  anamnesis TEXT NOT NULL DEFAULT '',
  lor_status TEXT NOT NULL DEFAULT '{}',
  diagnosis_main TEXT NOT NULL DEFAULT '',
  diagnosis_extra TEXT NOT NULL DEFAULT '',
  treatment TEXT NOT NULL DEFAULT '',
  recommendation TEXT NOT NULL DEFAULT '',
  prescriptions TEXT NOT NULL DEFAULT '[]',
  exams TEXT NOT NULL DEFAULT '',
  followup_date TEXT NOT NULL DEFAULT '',
  followup_note TEXT NOT NULL DEFAULT '',
  cancel_reason TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  created_by INTEGER REFERENCES users(id),
  updated_at TEXT,
  updated_by INTEGER REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id);
CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(visit_at);

CREATE TABLE IF NOT EXISTS services (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  price INTEGER NOT NULL CHECK (price >= 0),  -- so'm
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
  id INTEGER PRIMARY KEY,
  number TEXT UNIQUE,
  patient_id INTEGER NOT NULL REFERENCES patients(id),
  visit_id INTEGER REFERENCES visits(id),
  subtotal INTEGER NOT NULL,
  discount INTEGER NOT NULL DEFAULT 0,
  total INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','cancelled')),
  cancel_reason TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  created_by INTEGER REFERENCES users(id),
  cancelled_at TEXT,
  cancelled_by INTEGER REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_invoices_patient ON invoices(patient_id);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(created_at);

CREATE TABLE IF NOT EXISTS invoice_items (
  id INTEGER PRIMARY KEY,
  invoice_id INTEGER NOT NULL REFERENCES invoices(id),
  service_id INTEGER REFERENCES services(id),
  name TEXT NOT NULL,
  unit_price INTEGER NOT NULL,
  qty INTEGER NOT NULL,
  amount INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY,
  invoice_id INTEGER NOT NULL REFERENCES invoices(id),
  kind TEXT NOT NULL CHECK (kind IN ('payment','refund')),
  amount INTEGER NOT NULL CHECK (amount > 0),
  method TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT '',
  paid_at TEXT NOT NULL,
  created_by INTEGER REFERENCES users(id),
  voided INTEGER NOT NULL DEFAULT 0,
  void_reason TEXT NOT NULL DEFAULT '',
  voided_at TEXT,
  voided_by INTEGER REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(paid_at);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY,
  at TEXT NOT NULL,
  user_id INTEGER REFERENCES users(id),
  action TEXT NOT NULL,
  entity TEXT NOT NULL DEFAULT '',
  entity_id INTEGER,
  details TEXT NOT NULL DEFAULT '{}',
  ip TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_audit_at ON audit_logs(at);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
`;

db.exec(SCHEMA);

// Migratsiyalar: eski bazalarga yangi ustunlarni qo'shish
function addColumn(table, column, ddl) {
  const cols = db.prepare(`PRAGMA table_info(${table})`).all().map((c) => c.name);
  if (!cols.includes(column)) db.exec(`ALTER TABLE ${table} ADD COLUMN ${column} ${ddl}`);
}
addColumn('visits', 'recommendation', "TEXT NOT NULL DEFAULT ''");
addColumn('users', 'deleted', 'INTEGER NOT NULL DEFAULT 0');
addColumn('services', 'deleted', 'INTEGER NOT NULL DEFAULT 0');
addColumn('services', 'sort_order', 'INTEGER NOT NULL DEFAULT 0');
addColumn('services', 'price_group', "TEXT NOT NULL DEFAULT ''"); // paket chegirmasi guruhi (public/js/pricing.js)
addColumn('invoices', 'discount_note', "TEXT NOT NULL DEFAULT '[]'"); // avtomatik chegirma qatorlari (JSON)

const TZ = process.env.NURMED_TZ || 'Asia/Tashkent';
const fmt = new Intl.DateTimeFormat('en-CA', {
  timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
});

/** Klinika vaqt mintaqasidagi joriy vaqt: "YYYY-MM-DD HH:MM:SS" */
function nowLocal(date = new Date()) {
  const p = Object.fromEntries(fmt.formatToParts(date).map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}:${p.second}`;
}
const todayLocal = () => nowLocal().slice(0, 10);

/** Tranzaksiya ichida bajarish */
function tx(fn) {
  db.exec('BEGIN IMMEDIATE');
  try {
    const r = fn();
    db.exec('COMMIT');
    return r;
  } catch (e) {
    db.exec('ROLLBACK');
    throw e;
  }
}

const DEFAULT_SETTINGS = {
  clinic_name: 'NURMED ЛОР клиникаси',
  clinic_address: '',
  clinic_phone: '',
  clinic_requisites: '',
  clinic_logo: '', // data:image/... (ixtiyoriy)
  word_save_dir: '', // bo'sh bo'lmasa, Word fayllarning nusxasi server kompyuterdagi shu papkaga yoziladi
  print_mode: 'word', // 'word' — Чоп этиш Word fayl ochadi; 'browser' — brauzer orqali chop etiladi
};

// Klinika narx ro'yxati (Оториноларинголог хизматлари). Rasmdagi tartib va matn saqlangan.
const PRICE_LIST_VERSION = '2026-10-30';
const PRICE_LIST = [
  ['ЛОР врач бирламчи куриги ва консультацияси', 60000],
  ['Ревматолог врач бирламчи куриги ва консультацияси', 100000],
  ['Ревматолог врачни кайта куриги ва консультацияси', 50000],
  ['Эндоскопик текширув', 40000],
  ['Бурун бушлигини ювиш (Проетц усулида)', 35000],
  ['Бодомча безлари лакуналарини ювиш', 35000],
  ['Ташки кулок йулини тозалаш (бир томон)', 35000],
  ['Лимфотроп блокада 1 сеанс', 35000],
  ['Томокдан ёт жисмларни олиб ташлаш', 70000],
  ['Кулок, бурун ёт жисмларни олиб ташлаш', 60000],
  ['Политцер буйича кулокларни пуфлаш', 35000],
  ['Юкори жаг бушлигини (бир томон) пункция килиш', 200000],
  ['Юкори жаг бушлигини (икки томон) пункция килиш', 300000],
  ['Паратонзилляр абцессни кесиб очиш', 200000],
  ['Бурун, ташки кулок фурункулини кесиб очиш', 100000],
  ['Бурун суяги репозицияси', 300000],
  ['Бурунни олдинги тампонадаси', 100000],
  ['Тил ости пардасини кесиш', 200000],
  ['Тубус кварц (бурун, томок)', 20000],
  ['Дори воситалар ингаляцияси', 20000],
  ['Дарсонвал', 20000],
  ['Вена ичига дори моддасини томчилатиб юбориш (1 фл)', 25000],
  ['Вена ичига дори юбориш', 15000],
  ['Мушак орасига дори юбориш', 10000],
];

/**
 * Narx ro'yxatini bir marta o'rnatish. Eski xizmatlar katalogdan olib tashlanadi:
 * hisoblarda ishlatilmaganlari o'chiriladi, ishlatilganlari yashiriladi (eski hisoblar o'zgarmaydi).
 */
function applyPriceList() {
  const done = db.prepare('SELECT value FROM settings WHERE key = ?').get('price_list_version');
  if (done && done.value === PRICE_LIST_VERSION) return;
  tx(() => {
    const now = nowLocal();
    const old = db.prepare('SELECT id FROM services WHERE deleted = 0').all();
    const used = db.prepare('SELECT 1 FROM invoice_items WHERE service_id = ? LIMIT 1');
    for (const { id } of old) {
      if (used.get(id)) db.prepare('UPDATE services SET deleted = 1, active = 0 WHERE id = ?').run(id);
      else db.prepare('DELETE FROM services WHERE id = ?').run(id);
    }
    const ins = db.prepare('INSERT INTO services(name, price, active, sort_order, created_at) VALUES (?, ?, 1, ?, ?)');
    PRICE_LIST.forEach(([n, p], i) => ins.run(n, p, i + 1, now));
    db.prepare('INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value')
      .run('price_list_version', PRICE_LIST_VERSION);
    db.prepare('INSERT INTO audit_logs(at, user_id, action, entity, details) VALUES (?, NULL, ?, ?, ?)')
      .run(now, 'service.price_list', 'service', JSON.stringify({ version: PRICE_LIST_VERSION, items: PRICE_LIST.length, replaced: old.length }));
  });
}

// Klinika narx ro'yxatidagi xizmatlarning chegirma guruhlari (bir marta o'rnatiladi; keyin admin o'zgartiradi)
const PRICE_GROUPS = [
  ['ЛОР врач бирламчи куриги ва консультацияси', 'lor_exam'],
  ['Бурун бушлигини ювиш (Проетц усулида)', 'lor_proc'],
  ['Бодомча безлари лакуналарини ювиш', 'lor_proc'],
  ['Ташки кулок йулини тозалаш (бир томон)', 'lor_proc'],
  ['Лимфотроп блокада 1 сеанс', 'lor_proc'],
  ['Вена ичига дори моддасини томчилатиб юбориш (1 фл)', 'inj_drip'],
  ['Вена ичига дори юбориш', 'inj_iv'],
  ['Мушак орасига дори юбориш', 'inj_im'],
];
function applyPriceGroups() {
  const done = db.prepare('SELECT value FROM settings WHERE key = ?').get('price_groups_version');
  if (done) return;
  const upd = db.prepare("UPDATE services SET price_group = ? WHERE name = ? AND deleted = 0 AND price_group = ''");
  for (const [name, g] of PRICE_GROUPS) upd.run(g, name);
  db.prepare('INSERT INTO settings(key, value) VALUES (?, ?)').run('price_groups_version', '1');
}

function seed() {
  const ins = db.prepare('INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)');
  for (const [k, v] of Object.entries(DEFAULT_SETTINGS)) ins.run(k, v);
  applyPriceList();
  applyPriceGroups();
}
seed();

module.exports = { db, DB_PATH, DATA_DIR, nowLocal, todayLocal, tx, TZ };
