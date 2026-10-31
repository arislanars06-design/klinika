'use strict';
const { db, nowLocal, todayLocal, tx } = require('./db');
const sec = require('./security');
const fs = require('node:fs');
const path = require('node:path');
const { HttpError, Router, json, send, readJson, readRaw } = require('./http');
const backup = require('./backup');
const LOR = require('../public/js/lor-template.js');
const PRICING = require('../public/js/pricing.js');

const router = new Router();
const PAGE_SIZE = 20;
const EXPORT_LIMIT = 5000;
const PAY_METHODS = ['cash', 'uzcard', 'humo', 'card_other', 'transfer', 'other'];

/* ================= Yordamchilar ================= */
function need(ctx, perm) {
  if (!ctx.user) throw new HttpError(401, 'unauthorized');
  if (ctx.user.must_change_password) throw new HttpError(403, 'password_change_required');
  if (perm && !sec.can(ctx.user, perm)) throw new HttpError(403, 'forbidden');
}

function str(v, max, field, required = false) {
  if (v === undefined || v === null) v = '';
  if (typeof v !== 'string' && typeof v !== 'number') throw new HttpError(400, 'invalid', { field });
  const s = String(v).trim();
  if (required && !s) throw new HttpError(400, 'required', { field });
  if (s.length > max) throw new HttpError(400, 'too_long', { field });
  return s;
}

function int(v, field, min = 0, max = Number.MAX_SAFE_INTEGER) {
  const n = typeof v === 'string' && v.trim() !== '' ? Number(v) : v;
  if (!Number.isInteger(n) || n < min || n > max) throw new HttpError(400, 'invalid', { field });
  return n;
}

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
function isDate(s) {
  if (!DATE_RE.test(s)) return false;
  const d = new Date(s + 'T00:00:00Z');
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s;
}
function dateParam(v, field, fallback) {
  if (v === undefined || v === null || v === '') return fallback;
  if (!isDate(String(v))) throw new HttpError(400, 'invalid', { field });
  return String(v);
}

function birthDate(v) {
  const s = str(v, 10, 'birth_date');
  if (!s) return '';
  const year = Number(s.slice(0, 4));
  const thisYear = Number(todayLocal().slice(0, 4));
  const okShape = /^\d{4}$/.test(s) || isDate(s);
  if (!okShape || year < 1900 || year > thisYear || (s.length === 10 && s > todayLocal())) {
    throw new HttpError(400, 'invalid', { field: 'birth_date' });
  }
  return s;
}

function phone(v) {
  const s = str(v, 30, 'phone');
  if (!s) return '';
  const d = s.replace(/\D/g, '');
  if (d.length === 9) return '+998' + d;
  if (d.length === 12 && d.startsWith('998')) return '+' + d;
  if (d.length >= 7 && d.length <= 15) return (s.trim().startsWith('+') ? '+' : '') + d;
  throw new HttpError(400, 'invalid', { field: 'phone' });
}

function page(q) {
  const p = Math.max(1, Math.min(100000, parseInt(q.get('page') || '1', 10) || 1));
  return { page: p, offset: (p - 1) * PAGE_SIZE };
}

const likeEsc = (s) => '%' + s.replace(/[\\%_]/g, (c) => '\\' + c) + '%';
const pad = (n, w = 6) => String(n).padStart(w, '0');

function patientExists(id) {
  const p = db.prepare('SELECT * FROM patients WHERE id = ?').get(id);
  if (!p) throw new HttpError(404, 'patient_not_found');
  return p;
}

/* ================= Autentifikatsiya ================= */
router.post('/api/login', async (ctx) => {
  const body = await readJson(ctx.req);
  const username = str(body.username, 60, 'username', true).toLowerCase();
  const password = typeof body.password === 'string' ? body.password : '';
  const key = ctx.ip + '|' + username;
  if (sec.isLocked(key)) throw new HttpError(429, 'too_many_attempts');

  const row = db.prepare('SELECT * FROM users WHERE username = ?').get(username);
  const ok = row && row.active && password && sec.verifyPassword(password, row.password_hash);
  if (!ok) {
    sec.registerFailure(key);
    sec.audit(row || null, 'login.failed', 'user', row ? row.id : null, { username }, ctx.ip);
    throw new HttpError(401, 'bad_credentials');
  }
  sec.clearFailures(key);
  const token = sec.createSession(row.id);
  const user = sec.loadUser(row);
  sec.audit(user, 'login', 'user', user.id, {}, ctx.ip);
  ctx.setSession(token);
  return { user: publicUser(user) };
});

router.post('/api/logout', async (ctx) => {
  if (ctx.user) sec.audit(ctx.user, 'logout', 'user', ctx.user.id, {}, ctx.ip);
  sec.destroySession(ctx.token);
  ctx.clearSession();
  return { ok: true };
});

function publicUser(u) {
  return { id: u.id, username: u.username, full_name: u.full_name, phone: u.phone,
    roles: u.roles, perms: u.perms, must_change_password: u.must_change_password };
}

router.get('/api/me', async (ctx) => {
  if (!ctx.user) throw new HttpError(401, 'unauthorized');
  return { user: publicUser(ctx.user), settings: getSettings(false) };
});

router.post('/api/me/password', async (ctx) => {
  if (!ctx.user) throw new HttpError(401, 'unauthorized');
  const body = await readJson(ctx.req);
  const row = db.prepare('SELECT * FROM users WHERE id = ?').get(ctx.user.id);
  if (typeof body.old_password !== 'string' || !sec.verifyPassword(body.old_password, row.password_hash)) {
    throw new HttpError(400, 'bad_old_password');
  }
  if (!sec.validatePasswordStrength(body.new_password)) throw new HttpError(400, 'weak_password');
  if (body.new_password === body.old_password) throw new HttpError(400, 'same_password');
  db.prepare('UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?')
    .run(sec.hashPassword(body.new_password), ctx.user.id);
  // Boshqa qurilmalardagi sessiyalarni yopamiz, joriysini yangilaymiz
  sec.destroyUserSessions(ctx.user.id);
  ctx.setSession(sec.createSession(ctx.user.id));
  sec.audit(ctx.user, 'user.password_change', 'user', ctx.user.id, {}, ctx.ip);
  return { ok: true };
});

/* ================= Sozlamalar ================= */
const SETTING_KEYS = { clinic_name: 200, clinic_address: 300, clinic_phone: 100, clinic_requisites: 500,
  clinic_ministry: 200, clinic_subtitle: 300, clinic_services: 600, clinic_telegram: 60, clinic_instagram: 60 };

function getSettings() {
  const out = {};
  for (const r of db.prepare('SELECT key, value FROM settings').all()) out[r.key] = r.value;
  return out;
}

router.put('/api/settings', async (ctx) => {
  need(ctx, 'settings.clinic');
  const body = await readJson(ctx.req);
  // Server papkasi (fayllar yoziladigan joy) faqat administrator tomonidan o'zgartiriladi
  if ('word_save_dir' in body && !sec.can(ctx.user, 'admin')) {
    const cur = (db.prepare("SELECT value FROM settings WHERE key = 'word_save_dir'").get() || {}).value || '';
    if (String(body.word_save_dir || '').trim() !== cur) throw new HttpError(403, 'forbidden');
    delete body.word_save_dir;
  }
  const upd = db.prepare('INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value');
  const changed = [];
  for (const [k, max] of Object.entries(SETTING_KEYS)) {
    if (k in body) { upd.run(k, str(body[k], max, k, k === 'clinic_name')); changed.push(k); }
  }
  if ('word_save_dir' in body) {
    const dir = str(body.word_save_dir, 400, 'word_save_dir');
    if (dir) checkSaveDir(dir);
    upd.run('word_save_dir', dir);
    changed.push('word_save_dir');
  }
  if ('print_mode' in body) {
    if (!['word', 'browser'].includes(body.print_mode)) throw new HttpError(400, 'invalid', { field: 'print_mode' });
    upd.run('print_mode', body.print_mode);
    changed.push('print_mode');
  }
  if ('clinic_logo' in body) {
    const logo = typeof body.clinic_logo === 'string' ? body.clinic_logo : '';
    if (logo && (!/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(logo) || logo.length > 700000)) {
      throw new HttpError(400, 'invalid', { field: 'clinic_logo' });
    }
    upd.run('clinic_logo', logo);
    changed.push('clinic_logo');
  }
  sec.audit(ctx.user, 'settings.update', 'settings', null, { changed }, ctx.ip);
  return getSettings();
});

/* ================= Word fayllarni server papkasiga saqlash ================= */
// Papka server kompyuterda bo'ladi (masalan, D:\NURMED\Hujjatlar). Fayllar oy bo'yicha ichki papkalarga yoziladi.
function checkSaveDir(dir) {
  if (!path.isAbsolute(dir)) throw new HttpError(400, 'dir_not_absolute');
  try {
    fs.mkdirSync(dir, { recursive: true });
    const probe = path.join(dir, `.nurmed-${process.pid}.tmp`);
    fs.writeFileSync(probe, '');
    fs.unlinkSync(probe);
  } catch { throw new HttpError(400, 'dir_not_writable'); }
}

const safeFileName = (s) => String(s || '').normalize('NFC').replace(/[\\/:*?"<>|\u0000-\u001F]/g, '').replace(/^\.+/, '')
  .trim().replace(/\s+/g, '_').slice(0, 150);

router.post('/api/files', async (ctx) => {
  need(ctx, 'patient.read');
  const dir = (db.prepare("SELECT value FROM settings WHERE key = 'word_save_dir'").get() || {}).value || '';
  if (!dir) throw new HttpError(400, 'save_dir_not_set');
  const base = safeFileName(ctx.query.get('name')).replace(/\.docx$/i, '');
  if (!base) throw new HttpError(400, 'invalid', { field: 'name' });
  const data = await readRaw(ctx.req, 5 * 1024 * 1024);
  if (data.length < 4 || data[0] !== 0x50 || data[1] !== 0x4B) throw new HttpError(400, 'invalid', { field: 'file' }); // .docx = ZIP
  const sub = path.join(dir, todayLocal().slice(0, 7));
  try { fs.mkdirSync(sub, { recursive: true }); } catch { throw new HttpError(500, 'dir_not_writable'); }
  let file = path.join(sub, base + '.docx');
  for (let n = 2; fs.existsSync(file) && n < 1000; n++) file = path.join(sub, `${base}_(${n}).docx`);
  if (path.dirname(file) !== sub) throw new HttpError(400, 'invalid', { field: 'name' });
  try { fs.writeFileSync(file, data, { flag: 'wx' }); } catch { throw new HttpError(500, 'dir_not_writable'); }
  sec.audit(ctx.user, 'file.save', 'file', null, { file, size: data.length }, ctx.ip);
  return { path: file };
});

/* ================= Shifokorlar ro'yxati ================= */
router.get('/api/doctors', async (ctx) => {
  need(ctx);
  const rows = db.prepare(`SELECT id, full_name, phone, roles FROM users WHERE active = 1 ORDER BY full_name`).all();
  return rows.filter((r) => sec.isClinician(JSON.parse(r.roles))).map(({ id, full_name, phone }) => ({ id, full_name, phone }));
});

/* ================= Bosh oyna ================= */
router.get('/api/dashboard', async (ctx) => {
  need(ctx);
  const date = dateParam(ctx.query.get('date'), 'date', todayLocal());
  const visits = db.prepare(`
    SELECT v.id, v.visit_at, v.status, v.doctor_id, p.id AS patient_id, p.full_name AS patient_name, p.code AS patient_code,
           u.full_name AS doctor_name
    FROM visits v JOIN patients p ON p.id = v.patient_id LEFT JOIN users u ON u.id = v.doctor_id
    WHERE substr(v.visit_at, 1, 10) = ? AND v.status != 'cancelled' ORDER BY v.visit_at`).all(date);
  const out = {
    date,
    visits_count: visits.length,
    visits: sec.can(ctx.user, 'visit.list') ? visits : [],
  };
  if (sec.can(ctx.user, 'billing.read')) {
    const r = db.prepare(`
      SELECT COALESCE(SUM(CASE WHEN kind = 'payment' THEN amount ELSE -amount END), 0) AS net
      FROM payments WHERE voided = 0 AND substr(paid_at, 1, 10) = ?`).get(date);
    out.revenue = r.net;
  }
  return out;
});

/* ================= Bemorlar ================= */
function patientInput(body) {
  return {
    full_name: str(body.full_name, 200, 'full_name', true).replace(/\s+/g, ' '),
    birth_date: birthDate(body.birth_date),
    gender: ['m', 'f', ''].includes(body.gender ?? '') ? (body.gender ?? '') : (() => { throw new HttpError(400, 'invalid', { field: 'gender' }); })(),
    phone: phone(body.phone),
    address: str(body.address, 300, 'address'),
  };
}

router.get('/api/patients', async (ctx) => {
  need(ctx, 'patient.read');
  const q = str(ctx.query.get('q') || '', 100, 'q');
  const { page: p, offset } = page(ctx.query);
  const where = ['archived = 0'];
  const params = [];
  if (q) {
    const digits = q.replace(/\D/g, '');
    const cond = ["ulower(full_name) LIKE ulower(?) ESCAPE '\\'", "ulower(code) LIKE ulower(?) ESCAPE '\\'"];
    params.push(likeEsc(q), likeEsc(q));
    if (digits.length >= 3) { cond.push("phone LIKE ? ESCAPE '\\'"); params.push(likeEsc(digits)); }
    where.push('(' + cond.join(' OR ') + ')');
  }
  const w = where.join(' AND ');
  const total = db.prepare(`SELECT COUNT(*) AS c FROM patients WHERE ${w}`).get(...params).c;
  const rows = db.prepare(`
    SELECT p.*, (SELECT MAX(visit_at) FROM visits v WHERE v.patient_id = p.id AND v.status != 'cancelled') AS last_visit,
           (SELECT COUNT(*) FROM visits v WHERE v.patient_id = p.id AND v.status != 'cancelled') AS visits_count
    FROM patients p WHERE ${w} ORDER BY p.full_name COLLATE NOCASE LIMIT ? OFFSET ?`).all(...params, PAGE_SIZE, offset);
  return { total, page: p, page_size: PAGE_SIZE, rows };
});

router.post('/api/patients', async (ctx) => {
  need(ctx, 'patient.write');
  const body = await readJson(ctx.req);
  const d = patientInput(body);
  if (!body.force) {
    const dup = db.prepare(`SELECT id, code, full_name, birth_date, phone FROM patients
      WHERE archived = 0 AND (ulower(full_name) = ulower(?) AND (birth_date = ? OR ? = '') OR (phone != '' AND phone = ?))
      LIMIT 5`).all(d.full_name, d.birth_date, d.birth_date, d.phone);
    if (dup.length) throw new HttpError(409, 'possible_duplicate', { matches: dup });
  }
  const now = nowLocal();
  const id = tx(() => {
    const r = db.prepare(`INSERT INTO patients(full_name, birth_date, gender, phone, address, created_at, created_by)
      VALUES (?, ?, ?, ?, ?, ?, ?)`).run(d.full_name, d.birth_date, d.gender, d.phone, d.address, now, ctx.user.id);
    const nid = Number(r.lastInsertRowid);
    db.prepare('UPDATE patients SET code = ? WHERE id = ?').run('NM-' + pad(nid), nid);
    return nid;
  });
  sec.audit(ctx.user, 'patient.create', 'patient', id, {}, ctx.ip);
  return db.prepare('SELECT * FROM patients WHERE id = ?').get(id);
});

router.get('/api/patients/:id', async (ctx) => {
  need(ctx, 'patient.read');
  const p = patientExists(int(ctx.params.id, 'id', 1));
  const clinical = sec.can(ctx.user, 'visit.clinical.read');
  const visits = db.prepare(`
    SELECT v.id, v.visit_at, v.status, v.diagnosis_main, v.diagnosis_extra, v.followup_date, u.full_name AS doctor_name
    FROM visits v LEFT JOIN users u ON u.id = v.doctor_id WHERE v.patient_id = ? ORDER BY v.visit_at DESC`).all(p.id)
    .map((v) => (clinical ? v : { id: v.id, visit_at: v.visit_at, status: v.status, doctor_name: v.doctor_name }));
  const out = { patient: p, visits };
  if (sec.can(ctx.user, 'billing.read')) out.invoices = invoiceRows('i.patient_id = ?', [p.id], 200, 0);
  sec.audit(ctx.user, 'patient.view', 'patient', p.id, {}, ctx.ip);
  return out;
});

router.put('/api/patients/:id', async (ctx) => {
  need(ctx, 'patient.write');
  const id = int(ctx.params.id, 'id', 1);
  const old = patientExists(id);
  const body = await readJson(ctx.req);
  const d = patientInput(body);
  const changed = {};
  for (const k of Object.keys(d)) if (old[k] !== d[k]) changed[k] = { from: old[k], to: d[k] };
  let archived = old.archived;
  if ('archived' in body && sec.can(ctx.user, 'admin')) archived = body.archived ? 1 : 0;
  if (archived !== old.archived) changed.archived = { from: old.archived, to: archived };
  db.prepare(`UPDATE patients SET full_name = ?, birth_date = ?, gender = ?, phone = ?, address = ?, archived = ?,
    updated_at = ?, updated_by = ? WHERE id = ?`).run(d.full_name, d.birth_date, d.gender, d.phone, d.address, archived,
    nowLocal(), ctx.user.id, id);
  sec.audit(ctx.user, 'patient.update', 'patient', id, { changed }, ctx.ip);
  return db.prepare('SELECT * FROM patients WHERE id = ?').get(id);
});

/* ================= Qabullar ================= */
const CLINICAL_FIELDS = ['complaints', 'complaints_from', 'complaints_text', 'anamnesis', 'lor_status', 'diagnosis_main', 'diagnosis_extra',
  'treatment', 'recommendation', 'prescriptions', 'exams', 'followup_date', 'followup_note'];

function clinicalInput(body) {
  const pres = Array.isArray(body.prescriptions) ? body.prescriptions.slice(0, 30) : [];
  return {
    complaints: JSON.stringify(LOR.sanitizeComplaints(body.complaints)),
    complaints_from: LOR.relative(body.complaints_from) ? body.complaints_from : '',
    complaints_text: str(body.complaints_text, 4000, 'complaints_text'),
    anamnesis: str(body.anamnesis, 4000, 'anamnesis'),
    lor_status: JSON.stringify(LOR.sanitizeLor(body.lor_status)),
    diagnosis_main: str(body.diagnosis_main, 500, 'diagnosis_main'),
    diagnosis_extra: str(body.diagnosis_extra, 1000, 'diagnosis_extra'),
    treatment: str(body.treatment, 4000, 'treatment'),
    recommendation: str(body.recommendation, 4000, 'recommendation'),
    prescriptions: JSON.stringify(pres.map((x) => ({
      name: str(x && x.name, 200, 'prescriptions'),
      dose: str(x && x.dose, 100, 'prescriptions'),
      usage: str(x && x.usage, 200, 'prescriptions'),
      duration: str(x && x.duration, 100, 'prescriptions'),
    })).filter((x) => x.name)),
    exams: str(body.exams, 2000, 'exams'),
    followup_date: dateParam(body.followup_date, 'followup_date', ''),
    followup_note: str(body.followup_note, 1000, 'followup_note'),
  };
}

function doctorId(v) {
  const id = int(v, 'doctor_id', 1);
  const u = db.prepare('SELECT roles, active FROM users WHERE id = ?').get(id);
  if (!u || !u.active || !sec.isClinician(JSON.parse(u.roles))) throw new HttpError(400, 'invalid', { field: 'doctor_id' });
  return id;
}

function visitRow(id) {
  const v = db.prepare(`
    SELECT v.*, p.full_name AS patient_name, p.code AS patient_code, p.birth_date, p.gender, p.phone AS patient_phone,
           p.address AS patient_address, u.full_name AS doctor_name, u.phone AS doctor_phone,
           cu.full_name AS created_by_name, uu.full_name AS updated_by_name
    FROM visits v JOIN patients p ON p.id = v.patient_id
    LEFT JOIN users u ON u.id = v.doctor_id
    LEFT JOIN users cu ON cu.id = v.created_by
    LEFT JOIN users uu ON uu.id = v.updated_by
    WHERE v.id = ?`).get(id);
  if (!v) throw new HttpError(404, 'visit_not_found');
  return v;
}

function presentVisit(v, user) {
  const base = {
    id: v.id, patient_id: v.patient_id, patient_name: v.patient_name, patient_code: v.patient_code,
    birth_date: v.birth_date, gender: v.gender, patient_phone: v.patient_phone, patient_address: v.patient_address,
    doctor_id: v.doctor_id, doctor_name: v.doctor_name, doctor_phone: v.doctor_phone,
    visit_at: v.visit_at, status: v.status, cancel_reason: v.cancel_reason,
    created_at: v.created_at, created_by_name: v.created_by_name, updated_at: v.updated_at, updated_by_name: v.updated_by_name,
  };
  if (!sec.can(user, 'visit.clinical.read')) return base;
  return {
    ...base, ...Object.fromEntries(CLINICAL_FIELDS.map((k) => [k, v[k]])),
    complaints: JSON.parse(v.complaints), lor_status: JSON.parse(v.lor_status), prescriptions: JSON.parse(v.prescriptions),
  };
}

router.post('/api/visits', async (ctx) => {
  need(ctx, 'visit.create');
  const body = await readJson(ctx.req);
  const patient = patientExists(int(body.patient_id, 'patient_id', 1));
  if (patient.archived) throw new HttpError(400, 'patient_archived');
  const isDoctor = sec.can(ctx.user, 'visit.clinical.write');
  let did;
  if (body.doctor_id !== undefined && body.doctor_id !== null && body.doctor_id !== '') did = doctorId(body.doctor_id);
  else if (sec.isClinician(ctx.user.roles)) did = ctx.user.id;
  else throw new HttpError(400, 'required', { field: 'doctor_id' });

  const c = isDoctor ? clinicalInput(body) : clinicalInput({});
  const status = isDoctor && body.status === 'done' ? 'done' : 'open';
  const now = nowLocal();
  const r = db.prepare(`INSERT INTO visits(patient_id, doctor_id, visit_at, status, ${CLINICAL_FIELDS.join(', ')}, created_at, created_by)
    VALUES (?, ?, ?, ?, ${CLINICAL_FIELDS.map(() => '?').join(', ')}, ?, ?)`)
    .run(patient.id, did, now, status, ...CLINICAL_FIELDS.map((k) => c[k]), now, ctx.user.id);
  const id = Number(r.lastInsertRowid);
  sec.audit(ctx.user, 'visit.create', 'visit', id, { patient_id: patient.id }, ctx.ip);
  return presentVisit(visitRow(id), ctx.user);
});

function visitFilters(ctx) {
  const q = str(ctx.query.get('q') || '', 100, 'q');
  const from = dateParam(ctx.query.get('from'), 'from', '');
  const to = dateParam(ctx.query.get('to'), 'to', '');
  const status = ctx.query.get('status') || '';
  const doctor = ctx.query.get('doctor') || '';
  const patient = ctx.query.get('patient') || '';
  const where = [];
  const params = [];
  if (from) { where.push('substr(v.visit_at, 1, 10) >= ?'); params.push(from); }
  if (to) { where.push('substr(v.visit_at, 1, 10) <= ?'); params.push(to); }
  if (['open', 'done', 'cancelled'].includes(status)) { where.push('v.status = ?'); params.push(status); }
  else if (status !== 'all') where.push("v.status != 'cancelled'");
  if (doctor) { where.push('v.doctor_id = ?'); params.push(int(doctor, 'doctor', 1)); }
  if (patient) { where.push('v.patient_id = ?'); params.push(int(patient, 'patient', 1)); }
  if (q) {
    const cond = ["ulower(p.full_name) LIKE ulower(?) ESCAPE '\\'", "ulower(p.code) LIKE ulower(?) ESCAPE '\\'"];
    params.push(likeEsc(q), likeEsc(q));
    const digits = q.replace(/\D/g, '');
    if (digits.length >= 3) { cond.push("p.phone LIKE ? ESCAPE '\\'"); params.push(likeEsc(digits)); }
    if (sec.can(ctx.user, 'visit.clinical.read')) {
      cond.push("ulower(v.diagnosis_main) LIKE ulower(?) ESCAPE '\\'", "ulower(v.diagnosis_extra) LIKE ulower(?) ESCAPE '\\'");
      params.push(likeEsc(q), likeEsc(q));
    }
    where.push('(' + cond.join(' OR ') + ')');
  }
  return { where: where.length ? 'WHERE ' + where.join(' AND ') : '', params };
}

const VISIT_LIST_SQL = `
  SELECT v.id, v.visit_at, v.status, v.diagnosis_main, v.diagnosis_extra, v.patient_id, v.doctor_id,
         p.full_name AS patient_name, p.code AS patient_code, p.phone AS patient_phone, p.birth_date, p.address AS patient_address,
         u.full_name AS doctor_name
  FROM visits v JOIN patients p ON p.id = v.patient_id LEFT JOIN users u ON u.id = v.doctor_id`;

router.get('/api/visits', async (ctx) => {
  need(ctx, 'visit.list');
  const { where, params } = visitFilters(ctx);
  const { page: p, offset } = page(ctx.query);
  const total = db.prepare(`SELECT COUNT(*) AS c FROM visits v JOIN patients p ON p.id = v.patient_id ${where}`).get(...params).c;
  const clinical = sec.can(ctx.user, 'visit.clinical.read');
  // all=1 — Word jadvali uchun barcha qatorlar (eksport huquqi kerak, ko'pi bilan 5000)
  const all = ctx.query.get('all') === '1';
  if (all) need(ctx, 'export');
  const lim = all ? EXPORT_LIMIT : PAGE_SIZE;
  const off = all ? 0 : offset;
  if (all) sec.audit(ctx.user, 'visits.export_word', 'visit', null, { rows: Math.min(total, lim), query: ctx.url.search }, ctx.ip);
  const rows = db.prepare(`${VISIT_LIST_SQL} ${where} ORDER BY v.visit_at DESC LIMIT ? OFFSET ?`).all(...params, lim, off)
    .map((r) => { if (!clinical) { delete r.diagnosis_main; delete r.diagnosis_extra; } return r; });
  return { total, page: p, page_size: PAGE_SIZE, rows };
});

const csvCell = (v) => {
  let s = v === null || v === undefined ? '' : String(v);
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s; // Excel formula injection himoyasi
  return '"' + s.replace(/"/g, '""') + '"';
};

router.get('/api/visits/export.csv', async (ctx) => {
  need(ctx, 'export');
  const { where, params } = visitFilters(ctx);
  const rows = db.prepare(`${VISIT_LIST_SQL} ${where} ORDER BY v.visit_at DESC LIMIT 50000`).all(...params);
  const lang = ctx.query.get('lang') === 'ru' ? 'ru' : 'uz';
  const head = lang === 'ru'
    ? ['Дата', 'ID пациента', 'Ф.И.О.', 'Дата рождения', 'Телефон', 'Адрес', 'Врач', 'Статус', 'Диагноз', 'Сопутствующий диагноз']
    : ['Сана', 'Бемор ID', 'Ф.И.Ш.', 'Туғилган сана', 'Телефон', 'Манзил', 'Шифокор', 'Ҳолат', 'Ташхис', 'Қўшимча ташхис'];
  const lines = [head.map(csvCell).join(';')];
  for (const r of rows) {
    lines.push([r.visit_at, r.patient_code, r.patient_name, r.birth_date, r.patient_phone, r.patient_address, r.doctor_name,
      r.status, r.diagnosis_main, r.diagnosis_extra].map(csvCell).join(';'));
  }
  sec.audit(ctx.user, 'visits.export', 'visit', null, { rows: rows.length, query: ctx.url.search }, ctx.ip);
  send(ctx.res, 200, '\uFEFF' + lines.join('\r\n'), {
    'Content-Type': 'text/csv; charset=utf-8',
    'Content-Disposition': `attachment; filename="nurmed-qabullar-${todayLocal()}.csv"`,
    'Cache-Control': 'no-store',
  });
  return undefined;
});

router.get('/api/visits/:id', async (ctx) => {
  need(ctx, 'visit.list');
  const v = visitRow(int(ctx.params.id, 'id', 1));
  if (sec.can(ctx.user, 'visit.clinical.read')) {
    sec.audit(ctx.user, ctx.query.get('print') ? 'visit.print' : 'visit.view', 'visit', v.id, {}, ctx.ip);
  }
  return presentVisit(v, ctx.user);
});

router.put('/api/visits/:id', async (ctx) => {
  need(ctx);
  const id = int(ctx.params.id, 'id', 1);
  const old = visitRow(id);
  if (old.status === 'cancelled') throw new HttpError(400, 'visit_cancelled');
  const body = await readJson(ctx.req);
  const isDoctor = sec.can(ctx.user, 'visit.clinical.write');
  const canReassign = sec.can(ctx.user, 'visit.create');
  if (!isDoctor && !canReassign) throw new HttpError(403, 'forbidden');

  const sets = {};
  if (body.doctor_id !== undefined && canReassign) {
    if (!isDoctor && old.status !== 'open') throw new HttpError(403, 'forbidden');
    sets.doctor_id = doctorId(body.doctor_id);
  }
  if (isDoctor) {
    Object.assign(sets, clinicalInput(body));
    if (body.status === 'done' || body.status === 'open') sets.status = body.status;
  }
  const changed = {};
  for (const [k, v] of Object.entries(sets)) if (old[k] !== v) changed[k] = { from: old[k], to: v };
  if (!Object.keys(changed).length) return presentVisit(old, ctx.user);

  const keys = Object.keys(changed);
  db.prepare(`UPDATE visits SET ${keys.map((k) => `${k} = ?`).join(', ')}, updated_at = ?, updated_by = ? WHERE id = ?`)
    .run(...keys.map((k) => sets[k]), nowLocal(), ctx.user.id, id);
  sec.audit(ctx.user, 'visit.update', 'visit', id, { changed }, ctx.ip);
  return presentVisit(visitRow(id), ctx.user);
});

router.post('/api/visits/:id/cancel', async (ctx) => {
  need(ctx, 'visit.cancel');
  const id = int(ctx.params.id, 'id', 1);
  const v = visitRow(id);
  if (v.status === 'cancelled') throw new HttpError(400, 'visit_cancelled');
  const body = await readJson(ctx.req);
  const reason = str(body.reason, 500, 'reason', true);
  db.prepare("UPDATE visits SET status = 'cancelled', cancel_reason = ?, updated_at = ?, updated_by = ? WHERE id = ?")
    .run(reason, nowLocal(), ctx.user.id, id);
  sec.audit(ctx.user, 'visit.cancel', 'visit', id, { reason, previous_status: v.status }, ctx.ip);
  return presentVisit(visitRow(id), ctx.user);
});

/* ================= Xizmatlar katalogi ================= */
router.get('/api/services', async (ctx) => {
  need(ctx);
  if (!sec.can(ctx.user, 'billing.read') && !sec.can(ctx.user, 'admin')) throw new HttpError(403, 'forbidden');
  const all = ctx.query.get('all') === '1' && sec.can(ctx.user, 'admin');
  return db.prepare(`SELECT * FROM services WHERE deleted = 0 ${all ? '' : 'AND active = 1'} ORDER BY sort_order, name COLLATE NOCASE`).all();
});

function serviceInput(body) {
  return {
    name: str(body.name, 200, 'name', true),
    price: int(body.price, 'price', 0, 1e12),
    active: body.active === false || body.active === 0 ? 0 : 1,
    price_group: body.price_group === undefined || body.price_group === '' ? ''
      : PRICING.GROUPS.includes(body.price_group) ? body.price_group
        : (() => { throw new HttpError(400, 'invalid', { field: 'price_group' }); })(),
  };
}

router.post('/api/services', async (ctx) => {
  need(ctx, 'admin');
  const d = serviceInput(await readJson(ctx.req));
  const next = db.prepare('SELECT COALESCE(MAX(sort_order), 0) + 1 AS n FROM services').get().n;
  const r = db.prepare('INSERT INTO services(name, price, active, sort_order, price_group, created_at) VALUES (?, ?, ?, ?, ?, ?)').run(d.name, d.price, d.active, next, d.price_group, nowLocal());
  const id = Number(r.lastInsertRowid);
  sec.audit(ctx.user, 'service.create', 'service', id, d, ctx.ip);
  return db.prepare('SELECT * FROM services WHERE id = ?').get(id);
});

router.put('/api/services/:id', async (ctx) => {
  need(ctx, 'admin');
  const id = int(ctx.params.id, 'id', 1);
  const old = db.prepare('SELECT * FROM services WHERE id = ? AND deleted = 0').get(id);
  if (!old) throw new HttpError(404, 'not_found');
  const d = serviceInput(await readJson(ctx.req));
  db.prepare('UPDATE services SET name = ?, price = ?, active = ?, price_group = ? WHERE id = ?').run(d.name, d.price, d.active, d.price_group, id);
  sec.audit(ctx.user, 'service.update', 'service', id, { from: { name: old.name, price: old.price, active: old.active }, to: d }, ctx.ip);
  return db.prepare('SELECT * FROM services WHERE id = ?').get(id);
});

// Xizmatni o'chirish. Hisoblarda ishlatilmagan bo'lsa bazadan o'chiriladi; ishlatilgan bo'lsa,
// eski hisoblar buzilmasligi uchun yozuv saqlanadi, lekin katalogdan butunlay yashiriladi.
router.post('/api/services/:id/delete', async (ctx) => {
  need(ctx, 'admin');
  const id = int(ctx.params.id, 'id', 1);
  const s = db.prepare('SELECT * FROM services WHERE id = ? AND deleted = 0').get(id);
  if (!s) throw new HttpError(404, 'not_found');
  const used = db.prepare('SELECT 1 FROM invoice_items WHERE service_id = ? LIMIT 1').get(id);
  if (used) db.prepare('UPDATE services SET deleted = 1, active = 0 WHERE id = ?').run(id);
  else db.prepare('DELETE FROM services WHERE id = ?').run(id);
  sec.audit(ctx.user, 'service.delete', 'service', id, { name: s.name, price: s.price, kept_for_history: !!used }, ctx.ip);
  return { ok: true };
});

/* ================= Hisoblar va to'lovlar ================= */
const PAID_SQL = `COALESCE((SELECT SUM(CASE WHEN kind = 'payment' THEN amount ELSE -amount END)
  FROM payments pm WHERE pm.invoice_id = i.id AND pm.voided = 0), 0)`;

function payStatus(inv) {
  if (inv.status === 'cancelled') return 'cancelled';
  if (inv.paid >= inv.total) return 'paid';
  if (inv.paid > 0) return 'partial';
  return 'unpaid';
}

function invoiceRows(whereSql, params, limit, offset) {
  return db.prepare(`
    SELECT i.*, ${PAID_SQL} AS paid, p.full_name AS patient_name, p.code AS patient_code, u.full_name AS created_by_name
    FROM invoices i JOIN patients p ON p.id = i.patient_id LEFT JOIN users u ON u.id = i.created_by
    WHERE ${whereSql} ORDER BY i.created_at DESC LIMIT ? OFFSET ?`).all(...params, limit, offset)
    .map((r) => ({ ...r, debt: r.status === 'cancelled' ? 0 : Math.max(0, r.total - r.paid), pay_status: payStatus(r) }));
}

function invoiceFull(id) {
  const [inv] = invoiceRows('i.id = ?', [id], 1, 0);
  if (!inv) throw new HttpError(404, 'invoice_not_found');
  inv.items = db.prepare('SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY id').all(id);
  try { inv.discount_lines = JSON.parse(inv.discount_note || '[]'); } catch { inv.discount_lines = []; }
  inv.payments = db.prepare(`SELECT pm.*, u.full_name AS created_by_name, vu.full_name AS voided_by_name
    FROM payments pm LEFT JOIN users u ON u.id = pm.created_by LEFT JOIN users vu ON vu.id = pm.voided_by
    WHERE pm.invoice_id = ? ORDER BY pm.id`).all(id);
  if (inv.visit_id) {
    const v = db.prepare('SELECT visit_at FROM visits WHERE id = ?').get(inv.visit_id);
    inv.visit_at = v ? v.visit_at : null;
  }
  return inv;
}

function paymentInput(body, field = 'payment') {
  const amount = int(body.amount, field + '.amount', 1, 1e12);
  const method = String(body.method || '');
  if (!PAY_METHODS.includes(method)) throw new HttpError(400, 'invalid', { field: field + '.method' });
  return { amount, method, note: str(body.note, 300, field + '.note') };
}

router.get('/api/invoices', async (ctx) => {
  need(ctx, 'billing.read');
  const where = ["i.status = 'active'"];
  const params = [];
  const date = dateParam(ctx.query.get('date'), 'date', '');
  if (date) { where.push('substr(i.created_at, 1, 10) = ?'); params.push(date); }
  const q = str(ctx.query.get('q') || '', 100, 'q');
  if (q) {
    where.push("(ulower(p.full_name) LIKE ulower(?) ESCAPE '\\' OR ulower(p.code) LIKE ulower(?) ESCAPE '\\' OR ulower(i.number) LIKE ulower(?) ESCAPE '\\')");
    params.push(likeEsc(q), likeEsc(q), likeEsc(q));
  }
  const st = ctx.query.get('status') || '';
  if (st === 'debt') where.push(`i.status = 'active' AND ${PAID_SQL} < i.total`);
  const { page: p, offset } = page(ctx.query);
  const w = where.join(' AND ');
  const total = db.prepare(`SELECT COUNT(*) AS c FROM invoices i JOIN patients p ON p.id = i.patient_id WHERE ${w}`).get(...params).c;
  if (ctx.query.get('all') === '1') {
    // Word jadvali uchun: barcha qatorlar, xizmatlar ro'yxati bilan
    const rows = invoiceRows(w, params, EXPORT_LIMIT, 0);
    const itemsStmt = db.prepare('SELECT name, qty FROM invoice_items WHERE invoice_id = ? ORDER BY id');
    for (const r of rows) r.services = itemsStmt.all(r.id).map((x) => (x.qty > 1 ? `${x.name} ×${x.qty}` : x.name)).join('; ');
    sec.audit(ctx.user, 'invoices.export_word', 'invoice', null, { rows: rows.length, query: ctx.url.search }, ctx.ip);
    return { total, rows };
  }
  return { total, page: p, page_size: PAGE_SIZE, rows: invoiceRows(w, params, PAGE_SIZE, offset) };
});

router.post('/api/invoices', async (ctx) => {
  need(ctx, 'billing.write');
  const body = await readJson(ctx.req);
  const patient = patientExists(int(body.patient_id, 'patient_id', 1));
  let visitId = null;
  if (body.visit_id) {
    visitId = int(body.visit_id, 'visit_id', 1);
    const v = db.prepare('SELECT patient_id, status FROM visits WHERE id = ?').get(visitId);
    if (!v || v.patient_id !== patient.id) throw new HttpError(400, 'invalid', { field: 'visit_id' });
    if (v.status === 'cancelled') throw new HttpError(400, 'visit_cancelled');
  }
  if (!Array.isArray(body.items) || !body.items.length || body.items.length > 50) throw new HttpError(400, 'required', { field: 'items' });
  const svcStmt = db.prepare('SELECT * FROM services WHERE id = ? AND active = 1');
  const items = body.items.map((it, i) => {
    const s = svcStmt.get(int(it && it.service_id, `items.${i}.service_id`, 1));
    if (!s) throw new HttpError(400, 'invalid', { field: `items.${i}.service_id` });
    const qty = int(it.qty, `items.${i}.qty`, 1, 1000);
    const unit = it.unit_price === undefined ? s.price : int(it.unit_price, `items.${i}.unit_price`, 0, 1e12);
    return { service_id: s.id, name: s.name, unit_price: unit, qty, amount: unit * qty, price_group: s.price_group };
  });
  // Jami = Σ (narx × miqdor) − avtomatik paket chegirmasi − qo'lda chegirma. Server qayta hisoblaydi.
  const calc = PRICING.calculate(items);
  const subtotal = calc.subtotal;
  const manual = body.discount ? int(body.discount, 'discount', 0, calc.total) : 0;
  const discount = calc.discount + manual;
  const total = subtotal - discount;
  const discountNote = JSON.stringify([...calc.lines, ...(manual ? [{ uz: 'Қўлда чегирма', ru: 'Ручная скидка', amount: manual }] : [])]);
  const pay = body.payment && body.payment.amount ? paymentInput(body.payment) : null;
  if (pay && pay.amount > total) throw new HttpError(400, 'overpayment');

  const now = nowLocal();
  const id = tx(() => {
    const r = db.prepare(`INSERT INTO invoices(patient_id, visit_id, subtotal, discount, discount_note, total, created_at, created_by)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)`).run(patient.id, visitId, subtotal, discount, discountNote, total, now, ctx.user.id);
    const iid = Number(r.lastInsertRowid);
    db.prepare('UPDATE invoices SET number = ? WHERE id = ?').run('H-' + pad(iid), iid);
    const insItem = db.prepare('INSERT INTO invoice_items(invoice_id, service_id, name, unit_price, qty, amount) VALUES (?, ?, ?, ?, ?, ?)');
    for (const x of items) insItem.run(iid, x.service_id, x.name, x.unit_price, x.qty, x.amount);
    if (pay) {
      db.prepare(`INSERT INTO payments(invoice_id, kind, amount, method, note, paid_at, created_by) VALUES (?, 'payment', ?, ?, ?, ?, ?)`)
        .run(iid, pay.amount, pay.method, pay.note, now, ctx.user.id);
    }
    return iid;
  });
  sec.audit(ctx.user, 'invoice.create', 'invoice', id, { patient_id: patient.id, visit_id: visitId, total, discount, payment: pay }, ctx.ip);
  return invoiceFull(id);
});

router.get('/api/invoices/:id', async (ctx) => {
  need(ctx, 'billing.read');
  return invoiceFull(int(ctx.params.id, 'id', 1));
});

router.post('/api/invoices/:id/payments', async (ctx) => {
  need(ctx, 'billing.write');
  const id = int(ctx.params.id, 'id', 1);
  const inv = invoiceFull(id);
  if (inv.status === 'cancelled') throw new HttpError(400, 'invoice_cancelled');
  const body = await readJson(ctx.req);
  const kind = body.kind === 'refund' ? 'refund' : 'payment';
  const pay = paymentInput(body, 'payment');
  if (kind === 'payment' && pay.amount > inv.total - inv.paid) throw new HttpError(400, 'overpayment');
  if (kind === 'refund') {
    if (pay.amount > inv.paid) throw new HttpError(400, 'refund_too_large');
    if (!pay.note) throw new HttpError(400, 'required', { field: 'payment.note' });
  }
  const r = db.prepare(`INSERT INTO payments(invoice_id, kind, amount, method, note, paid_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)`)
    .run(id, kind, pay.amount, pay.method, pay.note, nowLocal(), ctx.user.id);
  sec.audit(ctx.user, kind === 'refund' ? 'payment.refund' : 'payment.create', 'payment', Number(r.lastInsertRowid),
    { invoice_id: id, ...pay }, ctx.ip);
  return invoiceFull(id);
});

router.post('/api/payments/:id/void', async (ctx) => {
  need(ctx, 'billing.write');
  const id = int(ctx.params.id, 'id', 1);
  const pm = db.prepare('SELECT * FROM payments WHERE id = ?').get(id);
  if (!pm) throw new HttpError(404, 'not_found');
  if (pm.voided) throw new HttpError(400, 'already_voided');
  const body = await readJson(ctx.req);
  const reason = str(body.reason, 300, 'reason', true);
  // To'lovni bekor qilish natijasida qaytarilgan summa to'langandan oshib ketmasligi kerak
  if (pm.kind === 'payment') {
    const inv = invoiceFull(pm.invoice_id);
    if (inv.paid - pm.amount < 0) throw new HttpError(400, 'void_breaks_balance');
  }
  db.prepare('UPDATE payments SET voided = 1, void_reason = ?, voided_at = ?, voided_by = ? WHERE id = ?')
    .run(reason, nowLocal(), ctx.user.id, id);
  sec.audit(ctx.user, 'payment.void', 'payment', id, { invoice_id: pm.invoice_id, amount: pm.amount, kind: pm.kind, reason }, ctx.ip);
  return invoiceFull(pm.invoice_id);
});

router.post('/api/invoices/:id/cancel', async (ctx) => {
  need(ctx, 'billing.write');
  const id = int(ctx.params.id, 'id', 1);
  const inv = invoiceFull(id);
  if (inv.status === 'cancelled') throw new HttpError(400, 'invoice_cancelled');
  if (inv.paid !== 0) throw new HttpError(400, 'invoice_has_payments');
  const body = await readJson(ctx.req);
  const reason = str(body.reason, 300, 'reason', true);
  db.prepare("UPDATE invoices SET status = 'cancelled', cancel_reason = ?, cancelled_at = ?, cancelled_by = ? WHERE id = ?")
    .run(reason, nowLocal(), ctx.user.id, id);
  sec.audit(ctx.user, 'invoice.cancel', 'invoice', id, { reason }, ctx.ip);
  return invoiceFull(id);
});

// Hisobni o'chirish (xato ochilgan hisob uchun). Hisob bazadan yo'qolmaydi: uning faol to'lovlari bekor qilinadi,
// hisob "bekor qilingan" bo'ladi va ro'yxatdan yashiriladi. Kunlik tushum shunga mos kamayadi. Hammasi audit jurnaliga yoziladi.
router.post('/api/invoices/:id/delete', async (ctx) => {
  need(ctx, 'billing.write');
  const id = int(ctx.params.id, 'id', 1);
  const inv = invoiceFull(id);
  if (inv.status === 'cancelled') throw new HttpError(400, 'invoice_cancelled');
  const body = await readJson(ctx.req);
  const reason = str(body.reason, 300, 'reason', true);
  const now = nowLocal();
  const voided = inv.payments.filter((p) => !p.voided).map((p) => ({ id: p.id, kind: p.kind, amount: p.amount, method: p.method }));
  tx(() => {
    db.prepare('UPDATE payments SET voided = 1, void_reason = ?, voided_at = ?, voided_by = ? WHERE invoice_id = ? AND voided = 0')
      .run(reason, now, ctx.user.id, id);
    db.prepare("UPDATE invoices SET status = 'cancelled', cancel_reason = ?, cancelled_at = ?, cancelled_by = ? WHERE id = ?")
      .run(reason, now, ctx.user.id, id);
  });
  sec.audit(ctx.user, 'invoice.delete', 'invoice', id, { number: inv.number, total: inv.total, reason, voided_payments: voided }, ctx.ip);
  return { ok: true };
});

router.get('/api/cash/daily', async (ctx) => {
  need(ctx, 'billing.read');
  const date = dateParam(ctx.query.get('date'), 'date', todayLocal());
  const payments = db.prepare(`
    SELECT pm.*, i.number AS invoice_number, p.full_name AS patient_name, u.full_name AS created_by_name
    FROM payments pm JOIN invoices i ON i.id = pm.invoice_id JOIN patients p ON p.id = i.patient_id
    LEFT JOIN users u ON u.id = pm.created_by
    WHERE substr(pm.paid_at, 1, 10) = ? ORDER BY pm.paid_at`).all(date);
  const by_method = {};
  let income = 0; let refunds = 0;
  for (const p of payments) {
    if (p.voided) continue;
    const m = by_method[p.method] || (by_method[p.method] = { income: 0, refunds: 0, net: 0 });
    if (p.kind === 'payment') { m.income += p.amount; income += p.amount; } else { m.refunds += p.amount; refunds += p.amount; }
    m.net = m.income - m.refunds;
  }
  const inv = db.prepare(`SELECT COUNT(*) AS c, COALESCE(SUM(total), 0) AS total, COALESCE(SUM(discount), 0) AS discount
    FROM invoices WHERE status = 'active' AND substr(created_at, 1, 10) = ?`).get(date);
  return { date, payments, by_method, income, refunds, net: income - refunds,
    invoices_count: inv.c, invoices_total: inv.total, discounts: inv.discount };
});

/* ================= Hisobotlar ================= */
router.get('/api/reports', async (ctx) => {
  need(ctx);
  const canV = sec.can(ctx.user, 'report.visits');
  const canF = sec.can(ctx.user, 'report.finance');
  if (!canV && !canF) throw new HttpError(403, 'forbidden');
  const to = dateParam(ctx.query.get('to'), 'to', todayLocal());
  const from = dateParam(ctx.query.get('from'), 'from', to.slice(0, 8) + '01');
  if (from > to) throw new HttpError(400, 'invalid', { field: 'from' });
  const days = (Date.parse(to) - Date.parse(from)) / 86400000;
  const groupLen = days > 62 ? 7 : 10; // uzun davr — oylar bo'yicha
  const out = { from, to, group: groupLen === 7 ? 'month' : 'day' };

  if (canV) {
    const P = [from, to];
    const inRange = "substr(v.visit_at, 1, 10) BETWEEN ? AND ? AND v.status != 'cancelled'";
    out.visits = {
      total: db.prepare(`SELECT COUNT(*) AS c FROM visits v WHERE ${inRange}`).get(...P).c,
      cancelled: db.prepare("SELECT COUNT(*) AS c FROM visits v WHERE substr(v.visit_at, 1, 10) BETWEEN ? AND ? AND v.status = 'cancelled'").get(...P).c,
      by_period: db.prepare(`SELECT substr(v.visit_at, 1, ${groupLen}) AS period, COUNT(*) AS count FROM visits v
        WHERE ${inRange} GROUP BY period ORDER BY period`).all(...P),
      by_doctor: db.prepare(`SELECT COALESCE(u.full_name, '—') AS doctor, COUNT(*) AS count FROM visits v
        LEFT JOIN users u ON u.id = v.doctor_id WHERE ${inRange} GROUP BY v.doctor_id ORDER BY count DESC`).all(...P),
      by_diagnosis: db.prepare(`SELECT v.diagnosis_main AS diagnosis, COUNT(*) AS count, COUNT(DISTINCT v.patient_id) AS patients
        FROM visits v WHERE ${inRange} AND v.diagnosis_main != '' GROUP BY v.diagnosis_main COLLATE NOCASE
        ORDER BY count DESC LIMIT 30`).all(...P),
    };
    const pt = db.prepare(`
      WITH firsts AS (SELECT patient_id, MIN(substr(visit_at, 1, 10)) AS first_day FROM visits WHERE status != 'cancelled' GROUP BY patient_id),
           period AS (SELECT DISTINCT v.patient_id FROM visits v WHERE ${inRange})
      SELECT COUNT(*) AS patients, SUM(CASE WHEN f.first_day >= ? THEN 1 ELSE 0 END) AS new_patients
      FROM period pr JOIN firsts f ON f.patient_id = pr.patient_id`).get(...P, from);
    out.visits.patients = pt.patients;
    out.visits.new_patients = pt.new_patients || 0;
    out.visits.returning_patients = pt.patients - (pt.new_patients || 0);
  }

  if (canF) {
    const P = [from, to];
    const pays = db.prepare(`SELECT method, kind, SUM(amount) AS sum, COUNT(*) AS count FROM payments
      WHERE voided = 0 AND substr(paid_at, 1, 10) BETWEEN ? AND ? GROUP BY method, kind`).all(...P);
    const by_method = {};
    let income = 0; let refunds = 0;
    for (const r of pays) {
      const m = by_method[r.method] || (by_method[r.method] = { income: 0, refunds: 0, net: 0 });
      if (r.kind === 'payment') { m.income += r.sum; income += r.sum; } else { m.refunds += r.sum; refunds += r.sum; }
      m.net = m.income - m.refunds;
    }
    const inv = db.prepare(`SELECT COUNT(*) AS c, COALESCE(SUM(total), 0) AS total, COALESCE(SUM(discount), 0) AS discount
      FROM invoices WHERE status = 'active' AND substr(created_at, 1, 10) BETWEEN ? AND ?`).get(...P);
    const debt = db.prepare(`SELECT COUNT(*) AS c, COALESCE(SUM(i.total - ${PAID_SQL}), 0) AS sum,
        SUM(CASE WHEN ${PAID_SQL} > 0 THEN 1 ELSE 0 END) AS partial
      FROM invoices i WHERE i.status = 'active' AND substr(i.created_at, 1, 10) BETWEEN ? AND ? AND ${PAID_SQL} < i.total`).get(...P);
    out.finance = {
      income, refunds, net: income - refunds, by_method,
      invoices_count: inv.c, invoices_total: inv.total, discounts: inv.discount,
      debt_count: debt.c, debt_partial: debt.partial || 0, debt_sum: debt.sum,
      by_period: db.prepare(`SELECT substr(paid_at, 1, ${groupLen}) AS period,
          SUM(CASE WHEN kind = 'payment' THEN amount ELSE -amount END) AS net
        FROM payments WHERE voided = 0 AND substr(paid_at, 1, 10) BETWEEN ? AND ? GROUP BY period ORDER BY period`).all(...P),
      services: db.prepare(`SELECT it.name, SUM(it.qty) AS qty, SUM(it.amount) AS amount FROM invoice_items it
        JOIN invoices i ON i.id = it.invoice_id WHERE i.status = 'active' AND substr(i.created_at, 1, 10) BETWEEN ? AND ?
        GROUP BY it.name ORDER BY qty DESC`).all(...P),
    };
  }
  return out;
});

/* ================= Foydalanuvchilar (admin) ================= */
function rolesInput(v) {
  if (!Array.isArray(v)) throw new HttpError(400, 'invalid', { field: 'roles' });
  const roles = [...new Set(v.filter((r) => sec.ROLES.includes(r)))];
  if (!roles.length) throw new HttpError(400, 'required', { field: 'roles' });
  return roles;
}

router.get('/api/users', async (ctx) => {
  need(ctx, 'admin');
  return db.prepare('SELECT id, username, full_name, roles, phone, active, must_change_password, created_at FROM users WHERE deleted = 0 ORDER BY full_name')
    .all().map((u) => ({ ...u, roles: JSON.parse(u.roles) }));
});

router.post('/api/users', async (ctx) => {
  need(ctx, 'admin');
  const b = await readJson(ctx.req);
  const username = str(b.username, 60, 'username', true).toLowerCase();
  if (!/^[a-z0-9._-]{3,60}$/.test(username)) throw new HttpError(400, 'invalid', { field: 'username' });
  if (!sec.validatePasswordStrength(b.password)) throw new HttpError(400, 'weak_password');
  const roles = rolesInput(b.roles);
  if (db.prepare('SELECT 1 FROM users WHERE username = ?').get(username)) throw new HttpError(409, 'username_taken');
  const r = db.prepare(`INSERT INTO users(username, password_hash, full_name, roles, phone, active, must_change_password, created_at)
    VALUES (?, ?, ?, ?, ?, 1, 1, ?)`).run(username, sec.hashPassword(b.password), str(b.full_name, 200, 'full_name', true),
    JSON.stringify(roles), phone(b.phone), nowLocal());
  const id = Number(r.lastInsertRowid);
  sec.audit(ctx.user, 'user.create', 'user', id, { username, roles }, ctx.ip);
  return { id };
});

router.put('/api/users/:id', async (ctx) => {
  need(ctx, 'admin');
  const id = int(ctx.params.id, 'id', 1);
  const old = db.prepare('SELECT * FROM users WHERE id = ? AND deleted = 0').get(id);
  if (!old) throw new HttpError(404, 'not_found');
  const b = await readJson(ctx.req);
  const roles = rolesInput(b.roles);
  const active = b.active === false ? 0 : 1;
  if (id === ctx.user.id && (!roles.includes('admin') || !active)) throw new HttpError(400, 'cannot_lock_self');
  const full = str(b.full_name, 200, 'full_name', true);
  const ph = phone(b.phone);
  db.prepare('UPDATE users SET full_name = ?, roles = ?, phone = ?, active = ? WHERE id = ?').run(full, JSON.stringify(roles), ph, active, id);
  const details = { roles, active };
  if (b.password) {
    if (!sec.validatePasswordStrength(b.password)) throw new HttpError(400, 'weak_password');
    db.prepare('UPDATE users SET password_hash = ?, must_change_password = 1 WHERE id = ?').run(sec.hashPassword(b.password), id);
    details.password_reset = true;
  }
  if (!active || b.password || old.roles !== JSON.stringify(roles)) sec.destroyUserSessions(id);
  sec.audit(ctx.user, 'user.update', 'user', id, details, ctx.ip);
  return { ok: true };
});

// Xodimni o'chirish. Xodim nomi uning qabullari, hisoblari va audit yozuvlarida qolishi uchun yozuv saqlanadi:
// akkaunt o'chiriladi (kirib bo'lmaydi), ro'yxatdan yashiriladi va login bo'shatiladi.
router.post('/api/users/:id/delete', async (ctx) => {
  need(ctx, 'admin');
  const id = int(ctx.params.id, 'id', 1);
  if (id === ctx.user.id) throw new HttpError(400, 'cannot_delete_self');
  const u = db.prepare('SELECT * FROM users WHERE id = ? AND deleted = 0').get(id);
  if (!u) throw new HttpError(404, 'not_found');
  if (JSON.parse(u.roles).includes('admin')) {
    const admins = db.prepare('SELECT roles FROM users WHERE deleted = 0 AND active = 1 AND id != ?').all(id)
      .filter((r) => JSON.parse(r.roles).includes('admin')).length;
    if (!admins) throw new HttpError(400, 'last_admin');
  }
  db.prepare('UPDATE users SET deleted = 1, active = 0, username = ? WHERE id = ?').run(`${u.username}~deleted~${id}`, id);
  sec.destroyUserSessions(id);
  sec.audit(ctx.user, 'user.delete', 'user', id, { username: u.username, full_name: u.full_name }, ctx.ip);
  return { ok: true };
});

/* ================= Audit jurnali (admin) ================= */
router.get('/api/audit', async (ctx) => {
  need(ctx, 'admin');
  const { page: p, offset } = page(ctx.query);
  const where = [];
  const params = [];
  const action = ctx.query.get('action');
  if (action) { where.push("a.action LIKE ? ESCAPE '\\'"); params.push(likeEsc(str(action, 60, 'action'))); }
  const date = dateParam(ctx.query.get('date'), 'date', '');
  if (date) { where.push('substr(a.at, 1, 10) = ?'); params.push(date); }
  const w = where.length ? 'WHERE ' + where.join(' AND ') : '';
  const total = db.prepare(`SELECT COUNT(*) AS c FROM audit_logs a ${w}`).get(...params).c;
  const rows = db.prepare(`SELECT a.*, u.full_name AS user_name, u.username FROM audit_logs a LEFT JOIN users u ON u.id = a.user_id
    ${w} ORDER BY a.id DESC LIMIT ? OFFSET ?`).all(...params, PAGE_SIZE, offset);
  return { total, page: p, page_size: PAGE_SIZE, rows };
});

/* ================= Zaxira nusxalari (admin) ================= */
router.get('/api/backups', async (ctx) => {
  need(ctx, 'admin');
  return backup.list();
});

router.post('/api/backups', async (ctx) => {
  need(ctx, 'admin');
  const info = await backup.create('manual');
  sec.audit(ctx.user, 'backup.create', 'backup', null, { file: info.name }, ctx.ip);
  return info;
});

router.get('/api/backups/:name', async (ctx) => {
  need(ctx, 'admin');
  const file = backup.resolve(ctx.params.name);
  sec.audit(ctx.user, 'backup.download', 'backup', null, { file: ctx.params.name }, ctx.ip);
  backup.stream(file, ctx.res, ctx.params.name);
  return undefined;
});

router.post('/api/backups/:name/delete', async (ctx) => {
  need(ctx, 'admin');
  backup.remove(ctx.params.name);
  sec.audit(ctx.user, 'backup.delete', 'backup', null, { file: ctx.params.name }, ctx.ip);
  return { ok: true };
});

module.exports = { router, json };
