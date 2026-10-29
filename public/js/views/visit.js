// Qabul bo'limi: yangi qabul (pasport ma'lumotlari shu oynaning o'zida), elektron tibbiy karta
// (shikoyat, LOR STATUS, tashxis), chop etish va kassaga o'tish.
import {
  html, raw, render, $, $$, t, L, state, GET, POST, PUT, qs, can, go, toast, errorText, busy,
  confirmDialog, fmtDate, fmtDateTime, age, genderText, statusBadge, patientSummary,
  printDoc, docHeader, localDate, ApiError, refresh,
} from '../core.js';

const LOR = window.LOR;
const PATIENT_FIELDS = ['full_name', 'birth_date', 'gender', 'phone', 'address'];

/* ================= Yangi qabul ================= */
export async function newVisitView(el, query) {
  const presetId = Number(query.get('patient')) || null;
  let patient = null;
  if (presetId) {
    try { patient = (await GET(`/api/patients/${presetId}`)).patient; } catch (e) { toast(errorText(e), 'err'); }
  }
  if (can('visit.clinical.write')) return renderVisitForm(el, { status: 'open' }, patient, { isNew: true });
  return renderRegistrarForm(el, patient);
}

/* ---------- Pasport ma'lumotlari (bemor kartasi shu yerda ochiladi yoki tanlanadi) ---------- */
function pasportFields(p, locked) {
  const dis = locked ? raw('disabled') : '';
  return html`
    <div class="grid-fields">
      <label class="field field--wide"><span>${t('f.full_name')} *</span>
        <input name="full_name" required maxlength="200" autocomplete="off" value="${p.full_name || ''}" ${dis}></label>
      <label class="field"><span>${t('f.birth_date')}</span>
        <input name="birth_date" maxlength="10" placeholder="${t('patient.birth_ph')}" pattern="\\d{4}(-\\d{2}-\\d{2})?" value="${p.birth_date || ''}" ${dis}></label>
      <label class="field"><span>${t('f.gender')}</span>
        <select name="gender" ${dis}>
          <option value="">—</option>
          <option value="m" ${p.gender === 'm' ? raw('selected') : ''}>${t('gender.m')}</option>
          <option value="f" ${p.gender === 'f' ? raw('selected') : ''}>${t('gender.f')}</option>
        </select></label>
      <label class="field"><span>${t('f.phone')}</span>
        <input name="phone" type="tel" maxlength="30" placeholder="+998 90 123 45 67" autocomplete="off" value="${p.phone || ''}" ${dis}></label>
      <label class="field field--wide"><span>${t('f.address')}</span>
        <input name="address" maxlength="300" value="${p.address || ''}" ${dis}></label>
    </div>`;
}

/**
 * Pasport bo'limini boshqaradi. Yangi qabulda F.I.Sh. yoki telefon yozilganda bazadan mos bemorlar taklif qilinadi
 * (bir bemorga ikkinchi karta ochilmasligi uchun). Saqlashda bemor kartasi avtomatik yaratiladi.
 */
function pasportController(box, initial, { canChange, onPatient }) {
  let patient = initial;
  const body = $('[data-pasport-body]', box);
  const draw = (p) => {
    render(body, html`
      ${patient ? html`<div class="card-head"><span class="locked">${patient.code}${patient.birth_date ? ` · ${age(patient.birth_date)} ${t('years')}` : ''}</span>
        <span>${canChange ? html`<button type="button" class="btn btn--ghost btn--sm" data-change>${t('visit.change_patient')}</button>`
          : html`<a class="btn btn--ghost btn--sm" href="#/patient/${patient.id}">${t('patient.card')}</a>`}</span></div>` : ''}
      ${pasportFields(p || {}, !!patient)}
      <div class="suggest" data-suggest></div>`);
    const ch = $('[data-change]', body);
    if (ch) ch.onclick = () => { patient = null; draw({}); onPatient(null); $('input[name=full_name]', body).focus(); };
    if (!patient) bindSuggest();
  };
  const read = () => Object.fromEntries(PATIENT_FIELDS.map((k) => [k, $(`[name=${k}]`, body).value.trim()]));
  const lock = (p) => { patient = p; draw(p); onPatient(p); };

  function showMatches(rows, title, withForce) {
    const sb = $('[data-suggest]', body);
    render(sb, rows.length || withForce ? html`
      <div class="suggest__title">${title}</div>
      ${rows.map((m) => html`<button type="button" class="picker__item" data-use="${m.id}">
        <span><b>${m.full_name}</b> <span class="muted">${m.code} · ${fmtDate(m.birth_date)} · ${m.phone}</span></span></button>`)}
      ${withForce ? html`<div><button type="button" class="btn btn--ghost btn--sm" data-force>${t('patient.create_anyway')}</button></div>` : ''}` : '');
    $$('[data-use]', sb).forEach((b) => {
      b.onclick = async () => {
        try { lock((await GET(`/api/patients/${b.dataset.use}`)).patient); toast(t('visit.patient_selected')); } catch (e) { toast(errorText(e), 'err'); }
      };
    });
    const f = $('[data-force]', sb);
    if (f) f.onclick = () => create(true).then((p) => { if (p) toast(t('visit.patient_created')); });
  }

  let timer; let seq = 0;
  function bindSuggest() {
    const run = async () => {
      const v = read();
      const digits = v.phone.replace(/\D/g, '');
      const q = v.full_name.length >= 3 ? v.full_name : digits.length >= 5 ? digits : '';
      if (!q) { render($('[data-suggest]', body), ''); return; }
      const my = ++seq;
      try {
        const d = await GET('/api/patients' + qs({ q }));
        if (my === seq && !patient) showMatches(d.rows.slice(0, 5), t('visit.suggest'), false);
      } catch { /* taklif ixtiyoriy */ }
    };
    ['full_name', 'phone'].forEach((n) => $(`[name=${n}]`, body).addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(run, 300); }));
  }

  async function create(force) {
    const data = read();
    if (!data.full_name) { toast(t('visit.need_name'), 'err'); $('[name=full_name]', body).focus(); return null; }
    try {
      const p = await POST('/api/patients', { ...data, force });
      lock(p);
      return p;
    } catch (e) {
      if (e instanceof ApiError && e.code === 'possible_duplicate') {
        showMatches(e.data.matches, t('patient.dup_title'), true);
        toast(t('err.possible_duplicate'), 'err');
      } else toast(errorText(e), 'err');
      return null;
    }
  }

  draw(initial);
  return {
    get: () => patient,
    /** Tanlangan bemor yoki yangi yaratilgan bemor; muammo bo'lsa null */
    ensure: () => (patient ? Promise.resolve(patient) : create(false)),
  };
}

const pasportCard = (extra = '') => html`
  <section class="card" data-pasport>
    <div class="card-head"><h2>${t('visit.pasport')}</h2>${extra}</div>
    <div data-pasport-body></div>
  </section>`;

/* ---------- Registrator: pasport va shifokor navbatiga yozish ---------- */
async function renderRegistrarForm(el, patient) {
  const doctors = await GET('/api/doctors');
  render(el, html`
    <div class="page-head"><h1>${t('visit.new')}</h1><div class="muted">${t('visit.date')}: ${fmtDateTime(localDate() + ' ' + new Date().toTimeString().slice(0, 5))}</div></div>
    <form id="reg-form" autocomplete="off">
      ${pasportCard()}
      <section class="card">
        <div class="row">
          <label class="field"><span>${t('f.doctor_id')} *</span>
            <select name="doctor_id" required>
              <option value="">—</option>
              ${doctors.map((d) => html`<option value="${d.id}">${d.full_name}</option>`)}
            </select></label>
          <button class="btn" type="submit">${t('visit.register_btn')}</button>
        </div>
        ${doctors.length ? '' : html`<p class="alert alert--warn">${t('visit.no_doctors')}</p>`}
      </section>
    </form>`);
  const f = $('#reg-form', el);
  const pas = pasportController($('[data-pasport]', el), patient, { canChange: true, onPatient: () => {} });
  f.onsubmit = async (e) => {
    e.preventDefault();
    if (!f.reportValidity()) return;
    await busy(e.submitter, async () => {
      const p = await pas.ensure();
      if (!p) return;
      await POST('/api/visits', { patient_id: p.id, doctor_id: Number(f.elements.doctor_id.value) });
      toast(t('visit.registered'));
      go('/');
    });
  };
}

/* ================= Mavjud qabul ================= */
export async function visitView(el, id) {
  const v = await GET(`/api/visits/${id}`);
  const patient = {
    id: v.patient_id, full_name: v.patient_name, code: v.patient_code, birth_date: v.birth_date,
    gender: v.gender, phone: v.patient_phone, address: v.patient_address,
  };
  if (v.lor_status === undefined) return renderBasicVisit(el, v, patient);
  if (can('visit.clinical.write') && v.status !== 'cancelled') return renderVisitForm(el, v, patient, { isNew: false });
  return renderReadOnlyVisit(el, v, patient);
}

function visitHead(v, patient, withSummary = true) {
  return html`
    <div class="page-head">
      <h1>${t('visit.title')} #${v.id}</h1>
      <div class="page-head__meta">${statusBadge(v.status)}
        <span class="muted">${fmtDateTime(v.visit_at)} · ${t('f.doctor_id')}: ${v.doctor_name || '—'}</span></div>
    </div>
    ${v.status === 'cancelled' ? html`<div class="alert alert--err">${t('visit.cancelled_reason')}: ${v.cancel_reason}</div>` : ''}
    ${withSummary ? html`<section class="card">${patientSummary(patient)}</section>` : ''}`;
}

async function renderBasicVisit(el, v, patient) {
  const canReassign = can('visit.create') && v.status === 'open';
  const doctors = canReassign ? await GET('/api/doctors') : [];
  render(el, html`${visitHead(v, patient)}
    <section class="card">
      <p class="muted">${t('visit.no_clinical_access')}</p>
      ${canReassign ? html`
        <form class="form row" id="reassign">
          <label class="field"><span>${t('f.doctor_id')}</span>
            <select name="doctor_id">${doctors.map((d) => html`<option value="${d.id}" ${d.id === v.doctor_id ? raw('selected') : ''}>${d.full_name}</option>`)}</select></label>
          <button class="btn btn--ghost">${t('save')}</button>
        </form>` : ''}
      <div class="actions">
        ${can('billing.write') && v.status !== 'cancelled' ? html`<a class="btn" href="#/cash/new?patient=${v.patient_id}&visit=${v.id}">${t('visit.to_cash')}</a>` : ''}
      </div>
    </section>`);
  const f = $('#reassign', el);
  if (f) f.onsubmit = async (e) => {
    e.preventDefault();
    await busy(f.querySelector('button'), async () => {
      await PUT(`/api/visits/${v.id}`, { doctor_id: Number(f.elements.doctor_id.value) });
      toast(t('saved'));
    });
  };
}

function renderReadOnlyVisit(el, v, patient) {
  render(el, html`${visitHead(v, patient)}
    <section class="card doc-preview">${visitDocBody(v)}</section>
    <div class="actions">
      <button class="btn" id="print">${t('print')}</button>
      ${can('billing.write') && v.status !== 'cancelled' ? html`<a class="btn btn--ghost" href="#/cash/new?patient=${v.patient_id}&visit=${v.id}">${t('visit.cash')}</a>` : ''}
      ${can('visit.cancel') && v.status !== 'cancelled' ? html`<button class="btn btn--danger" id="cancel">${t('visit.cancel')}</button>` : ''}
    </div>`);
  $('#print', el).onclick = () => printVisit(v.id);
  const c = $('#cancel', el);
  if (c) c.onclick = () => cancelVisit(v.id, () => visitView(el, v.id));
}

async function cancelVisit(id, after) {
  const reason = await confirmDialog(t('visit.cancel_confirm'), { input: true, danger: true, okText: t('visit.cancel') });
  if (!reason) return;
  try { await POST(`/api/visits/${id}/cancel`, { reason }); toast(t('visit.cancelled')); after(); } catch (e) { toast(errorText(e), 'err'); }
}

/* ================= Elektron tibbiy karta (shifokor) ================= */
function chip(name, value, label, checked) {
  return html`<label class="chip"><input type="checkbox" name="${name}" value="${value}" ${checked ? raw('checked') : ''}><span>${label}</span></label>`;
}

function complaintsBlock(v) {
  const sel = {};
  (v.complaints || []).forEach((c) => { const x = typeof c === 'string' ? { code: c } : c; sel[x.code] = x; });
  const dischargeBox = (i) => {
    const cur = sel[i.code] || {};
    return html`<span class="discharge ${cur.code ? '' : 'hidden'}" data-discharge-for="${i.code}">
      <select name="cdis|${i.code}"><option value="">${t('visit.discharge_type')}</option>
        ${LOR.DISCHARGE.map((d) => html`<option value="${d.code}" ${cur.discharge === d.code ? raw('selected') : ''}>${L(d)}</option>`)}</select>
      <input name="cdtx|${i.code}" maxlength="200" placeholder="${t('visit.discharge_other')}" value="${cur.discharge_text || ''}"
        class="${cur.discharge === 'other' ? '' : 'hidden'}"></span>`;
  };
  return html`
    <section class="card">
      <h2>${t('visit.step_complaints')}</h2>
      <div class="complaints">
        ${LOR.COMPLAINTS.map((g) => html`
          <div class="complaints__group"><div class="complaints__title">${L(g)}</div>
            <div class="chips chips--sm">${g.items.map((i) => html`<span class="complaint-item">
              ${chip('complaint', i.code, L(i), !!sel[i.code])}${i.has_discharge_type ? dischargeBox(i) : ''}</span>`)}</div>
          </div>`)}
      </div>
      <div class="grid-fields">
        <label class="field field--wide"><span>${t('f.complaints_text')}</span>
          <textarea name="complaints_text" rows="2" maxlength="4000" placeholder="${t('visit.complaints_ph')}">${v.complaints_text || ''}</textarea></label>
        <label class="field field--wide"><span>${t('f.anamnesis')}</span>
          <textarea name="anamnesis" rows="2" maxlength="4000" placeholder="${t('visit.anamnesis_ph')}">${v.anamnesis || ''}</textarea></label>
      </div>
    </section>`;
}

/* Input nomi: lor|<metod>|<quloq yoki ->|<qism>|<maydon>. Radio, tomon va daraja ham checkbox
   ko‘rinishida chiziladi (data-single): bittasi tanlanadi, qayta bosilsa tanlov olib tashlanadi. */
const lorName = (m, ear, p, f) => `lor|${m}|${ear || '-'}|${p}|${f}`;
const methodBox = (form, code) => $(`.lor[data-method="${code}"]`, form);

function lorParts(m, ear, parts) {
  return html`${m.parts.map((p) => {
    const pv = parts[p.code] || {};
    return html`<div class="lor-part ${LOR.partVisible(p, parts) ? '' : 'hidden'}" data-part="${p.code}" data-ear="${ear || ''}">
      <div class="lor-part__title">${L(p)}</div>
      <div class="lor-part__fields">
        ${p.fields.map((f) => {
          const n = lorName(m.code, ear, p.code, f.code);
          const cur = pv[f.code];
          const has = (c) => (Array.isArray(cur) ? cur.includes(c) : cur === c);
          const single = ['radio', 'side', 'degree'].includes(f.type);
          const body = f.type === 'checkbox'
            ? html`<label class="chip"><input type="checkbox" name="${n}" value="1" ${cur ? raw('checked') : ''}><span>${L(f)}</span></label>`
            : LOR.choicesOf(f).map((c) => html`<label class="chip"><input type="checkbox" name="${n}" value="${c.code}"
                ${single ? raw('data-single') : ''} ${c.is_norm ? raw('data-norm') : ''} ${has(c.code) ? raw('checked') : ''}><span>${L(c)}</span></label>`);
          return html`<div class="lor-field ${LOR.fieldVisible(f, pv) ? '' : 'hidden'}" data-field="${f.code}">
            ${f.type !== 'checkbox' && LOR.FIELD_LABELS[f.code] && p.fields.length > 1 ? html`<span class="lor-field__label">${L(LOR.FIELD_LABELS[f.code])}:</span>` : ''}
            <div class="chips chips--sm">${body}</div></div>`;
        })}
        <input class="lor__text" name="${lorName(m.code, ear, p.code, '_text')}" maxlength="500" placeholder="${t('lor.note')}" value="${pv._text || ''}">
      </div>
    </div>`;
  })}`;
}

function lorBlock(v) {
  const data = v.lor_status || {};
  return html`
    <section class="card">
      <div class="card-head"><h2>${t('visit.step_lor')}</h2></div>
      <div class="tabs lor-tabs" role="tablist">
        ${LOR.METHODS.map((m, i) => html`<button type="button" class="tab ${i === 0 ? 'tab--active' : ''}" data-lor-tab="${m.code}">
          ${L(m)}<span class="tab__count hidden" data-count-for="${m.code}"></span></button>`)}
      </div>
      ${LOR.METHODS.map((m, i) => {
        const mv = data[m.code] || {};
        return html`
        <div class="lor ${i === 0 ? '' : 'hidden'}" data-method="${m.code}">
          ${m.ears
            ? html`<div class="lor-ears">${m.ears.map((e) => html`<div class="lor-ear" data-ear-box="${e.code}">
                <h4 class="lor-ear__title">${L(e)}</h4>${lorParts(m, e.code, (mv.ears || {})[e.code] || {})}</div>`)}</div>`
            : lorParts(m, '', mv.parts || {})}
          <div class="lor__foot">
            <label class="field"><span>${t('lor.section_note')}</span>
              <textarea name="lornote|${m.code}" rows="1" maxlength="2000">${mv.note || ''}</textarea></label>
            <button type="button" class="btn btn--ghost btn--sm" data-norm-method="${m.code}">${t('lor.norm')}</button>
            <button type="button" class="btn btn--ghost btn--sm" data-clear="${m.code}">${t('lor.clear')}</button>
          </div>
        </div>`;
      })}
      <p class="hint">${t('visit.lor_hint')}</p>
    </section>`;
}

/** Formadagi tanlovlardan qism qiymatlarini o‘qish */
function readParts(form, m, ear) {
  const parts = {};
  for (const p of m.parts) {
    const pv = {};
    for (const f of p.fields) {
      const n = lorName(m.code, ear, p.code, f.code);
      const vals = $$(`input[name="${CSS.escape(n)}"]:checked`, form).map((i) => i.value);
      if (!vals.length) continue;
      if (f.type === 'checkbox') pv[f.code] = true;
      else if (f.type === 'checkbox_multi') pv[f.code] = vals;
      else pv[f.code] = vals[0];
    }
    const txt = form.elements[lorName(m.code, ear, p.code, '_text')];
    if (txt && txt.value.trim()) pv._text = txt.value.trim();
    if (Object.keys(pv).length) parts[p.code] = pv;
  }
  return parts;
}

/**
 * "Norma" tugmasi: shifokor o‘zi bosganda, shu metoddagi faqat BO‘SH maydonlarga norma variantini qo‘yadi.
 * Shifokor allaqachon tanlagan qiymatlar o‘zgarmaydi. Shartli maydonlar (masalan, gipertrofiya darajasi)
 * to‘ldirilmaydi, chunki ular faqat patologiya tanlanganda ma’noga ega. Natija: to‘ldirilgan maydonlar soni.
 */
function fillNorm(form, m) {
  let n = 0;
  for (const ear of m.ears ? m.ears.map((e) => e.code) : ['']) {
    for (const p of m.parts) {
      const box = $(`.lor-part[data-part="${p.code}"][data-ear="${ear}"]`, methodBox(form, m.code));
      if (!box || box.classList.contains('hidden')) continue;
      for (const f of p.fields) {
        if (f.when) continue;
        const norm = LOR.choicesOf(f).find((c) => c.is_norm);
        if (!norm) continue;
        const inputs = $$(`input[name="${CSS.escape(lorName(m.code, ear, p.code, f.code))}"]`, box);
        if (inputs.some((i) => i.checked)) continue;
        const target = inputs.find((i) => i.value === norm.code);
        if (target) { target.checked = true; n += 1; }
      }
    }
  }
  return n;
}

/** Shartli maydon va qismlarni ko‘rsatish/yashirish. Yashiringan maydon tanlovlari tozalanadi. */
function applyLorVisibility(form) {
  for (const m of LOR.METHODS) {
    for (const ear of m.ears ? m.ears.map((e) => e.code) : ['']) {
      const parts = readParts(form, m, ear);
      for (const p of m.parts) {
        const box = $(`.lor-part[data-part="${p.code}"][data-ear="${ear}"]`, methodBox(form, m.code));
        if (!box) continue;
        const pvis = LOR.partVisible(p, parts);
        box.classList.toggle('hidden', !pvis);
        for (const f of p.fields) {
          const fbox = $(`.lor-field[data-field="${f.code}"]`, box);
          const vis = pvis && LOR.fieldVisible(f, parts[p.code] || {});
          fbox.classList.toggle('hidden', !vis);
          if (!vis) $$('input:checked', fbox).forEach((i) => { i.checked = false; });
        }
        if (!pvis) $$('input:checked', box).forEach((i) => { i.checked = false; });
      }
    }
  }
}

function diagnosisBlock(v) {
  const rx = v.prescriptions && v.prescriptions.length ? v.prescriptions : [{}];
  return html`
    <section class="card">
      <h2>${t('visit.step_diagnosis')}</h2>
      <datalist id="dx-list">${LOR.DIAGNOSES.map((d) => html`<option value="${d.code} — ${L(d)}"></option>`)}</datalist>
      <div class="grid-fields">
        <label class="field field--wide"><span>${t('f.diagnosis_main')}</span>
          <input name="diagnosis_main" list="dx-list" maxlength="500" value="${v.diagnosis_main || ''}" placeholder="${t('visit.dx_ph')}"></label>
        <label class="field field--wide"><span>${t('f.diagnosis_extra')}</span>
          <input name="diagnosis_extra" maxlength="1000" value="${v.diagnosis_extra || ''}"></label>
        <label class="field field--wide"><span>${t('f.treatment')}</span>
          <textarea name="treatment" rows="2" maxlength="4000">${v.treatment || ''}</textarea></label>
        <label class="field field--wide"><span>${t('f.exams')}</span>
          <textarea name="exams" rows="2" maxlength="2000" placeholder="${t('visit.exams_ph')}">${v.exams || ''}</textarea></label>
      </div>
      <div class="field"><span>${t('f.prescriptions')}</span>
        <table class="rx">
          <thead><tr><th>${t('rx.name')}</th><th>${t('rx.dose')}</th><th>${t('rx.usage')}</th><th>${t('rx.duration')}</th><th></th></tr></thead>
          <tbody id="rx-body">${rx.map(rxRow)}</tbody>
        </table>
        <div><button type="button" class="btn btn--ghost btn--sm" id="rx-add">+ ${t('rx.add')}</button></div>
      </div>
      <div class="grid-fields">
        <label class="field"><span>${t('f.followup_date')}</span><input type="date" name="followup_date" value="${v.followup_date || ''}"></label>
        <label class="field field--wide"><span>${t('f.followup_note')}</span><input name="followup_note" maxlength="1000" value="${v.followup_note || ''}"></label>
      </div>
    </section>`;
}

function rxRow(r = {}) {
  return html`<tr class="rx__row">
    <td><input data-rx="name" maxlength="200" value="${r.name || ''}"></td>
    <td><input data-rx="dose" maxlength="100" value="${r.dose || ''}"></td>
    <td><input data-rx="usage" maxlength="200" value="${r.usage || ''}"></td>
    <td><input data-rx="duration" maxlength="100" value="${r.duration || ''}"></td>
    <td><button type="button" class="btn btn--ghost btn--sm" data-rx-del title="${t('delete')}">✕</button></td>
  </tr>`;
}

function collect(form) {
  const fd = new FormData(form);
  const lor = {};
  for (const m of LOR.METHODS) {
    const res = {};
    if (m.ears) {
      const ears = {};
      for (const e of m.ears) {
        const p = readParts(form, m, e.code);
        if (Object.keys(p).length) ears[e.code] = p;
      }
      if (Object.keys(ears).length) res.ears = ears;
    } else {
      const p = readParts(form, m, '');
      if (Object.keys(p).length) res.parts = p;
    }
    const note = (fd.get(`lornote|${m.code}`) || '').trim();
    if (note) res.note = note;
    if (Object.keys(res).length) lor[m.code] = res;
  }
  const complaints = fd.getAll('complaint').map((code) => {
    const c = { code };
    const d = fd.get(`cdis|${code}`);
    if (d) {
      c.discharge = d;
      const tx = (fd.get(`cdtx|${code}`) || '').trim();
      if (d === 'other' && tx) c.discharge_text = tx;
    }
    return c;
  });
  const prescriptions = $$('.rx__row', form).map((tr) => Object.fromEntries($$('[data-rx]', tr).map((i) => [i.dataset.rx, i.value.trim()])))
    .filter((r) => r.name);
  const g = (k) => (fd.get(k) || '').trim();
  return {
    complaints, complaints_text: g('complaints_text'), anamnesis: g('anamnesis'), lor_status: lor,
    diagnosis_main: g('diagnosis_main'), diagnosis_extra: g('diagnosis_extra'), treatment: g('treatment'), prescriptions,
    exams: g('exams'), followup_date: g('followup_date'), followup_note: g('followup_note'),
  };
}

function historyList(history) {
  return history.length ? html`<ul class="hist">${history.map((h) => html`
    <li><a href="#/visit/${h.id}">${fmtDate(h.visit_at)}</a> ${h.status === 'cancelled' ? statusBadge('cancelled') : ''}
      <div class="small">${h.diagnosis_main || html`<span class="muted">${t('visit.no_dx')}</span>`}</div>
      <div class="muted small">${h.doctor_name || ''}</div></li>`)}</ul>`
    : html`<p class="muted small">${t('visit.first_visit')}</p>`;
}

/** Yangi va mavjud qabul uchun bitta ixcham oyna: pasport → shikoyatlar → LOR STATUS → tashxis → amallar */
async function renderVisitForm(el, v, patient, { isNew }) {
  render(el, html`
    ${isNew ? html`<div class="page-head"><h1>${t('visit.new')}</h1>
      <div class="muted">${t('visit.date')}: ${fmtDateTime(localDate() + ' ' + new Date().toTimeString().slice(0, 5))}</div></div>`
      : visitHead(v, patient, false)}
    <div class="visit-layout">
      <form id="clinical" class="visit-main" autocomplete="off">
        ${pasportCard()}
        ${complaintsBlock(v)}
        ${lorBlock(v)}
        ${diagnosisBlock(v)}
        <div class="card sticky-actions">
          <button type="submit" class="btn" data-mode="save">${t('save')}</button>
          <button type="submit" class="btn btn--ok" data-mode="done">${t('visit.finish')}</button>
          <button type="submit" class="btn btn--ghost" data-mode="print">${t('visit.save_print')}</button>
          ${can('billing.write') ? html`<button type="submit" class="btn btn--ghost" data-mode="cash">${t('visit.cash')}</button>` : ''}
          ${!isNew && can('visit.cancel') ? html`<button type="button" class="btn btn--danger" id="cancel">${t('visit.cancel')}</button>` : ''}
          <span class="spacer"></span>
          <span class="muted small" id="dirty-flag">${!isNew && v.updated_at ? `${t('visit.updated')}: ${fmtDateTime(v.updated_at)} · ${v.updated_by_name || ''}` : ''}</span>
        </div>
      </form>
      <aside class="visit-side card card--tight">
        <h3>${t('visit.history')}</h3>
        <div id="history"><p class="muted small">—</p></div>
      </aside>
    </div>`);

  const form = $('#clinical', el);
  const loadHistory = async (p) => {
    const box = $('#history', el);
    if (!p) { render(box, html`<p class="muted small">—</p>`); return; }
    try { render(box, historyList((await GET(`/api/patients/${p.id}`)).visits.filter((x) => x.id !== v.id))); } catch { /* ixtiyoriy */ }
  };
  const pas = pasportController($('[data-pasport]', el), patient, { canChange: isNew, onPatient: loadHistory });
  loadHistory(patient);

  let dirty = false;
  const flag = $('#dirty-flag', el);
  const markDirty = () => { dirty = true; flag.textContent = t('visit.unsaved'); updateCounts(); };
  form.addEventListener('input', markDirty);
  form.addEventListener('change', (e) => {
    const i = e.target;
    if (i.type === 'checkbox' && i.name.startsWith('lor|') && i.checked) {
      const group = $$(`input[name="${CSS.escape(i.name)}"]`, form).filter((x) => x !== i);
      // Bitta tanlanadigan maydon; ko‘p tanlovda "norma" varianti (masalan, "Yo‘q", "Toza") boshqalari bilan birga bo‘lmaydi
      if (i.hasAttribute('data-single')) group.forEach((x) => { x.checked = false; });
      else if (i.hasAttribute('data-norm')) group.forEach((x) => { x.checked = false; });
      else group.filter((x) => x.hasAttribute('data-norm')).forEach((x) => { x.checked = false; });
    }
    if (i.name.startsWith('lor|')) applyLorVisibility(form);
    if (i.name === 'complaint') {
      const box = $(`[data-discharge-for="${CSS.escape(i.value)}"]`, form);
      if (box) {
        box.classList.toggle('hidden', !i.checked);
        if (!i.checked) { $('select', box).value = ''; $('input', box).value = ''; $('input', box).classList.add('hidden'); }
      }
    }
    if (i.name.startsWith('cdis|')) i.nextElementSibling.classList.toggle('hidden', i.value !== 'other');
    markDirty();
  });
  state.leaveGuard = { dirty: () => dirty };

  // LOR STATUS tablari
  $$('[data-lor-tab]', form).forEach((b) => {
    b.onclick = () => {
      $$('[data-lor-tab]', form).forEach((x) => x.classList.toggle('tab--active', x === b));
      $$('.lor[data-method]', form).forEach((p) => p.classList.toggle('hidden', p.dataset.method !== b.dataset.lorTab));
    };
  });
  function updateCounts() {
    $$('.lor[data-method]', form).forEach((d) => {
      const n = $$('.lor-part', d).filter((p) => $$('input[type=checkbox]:checked', p).length || $('.lor__text', p).value.trim()).length;
      const c = $(`[data-count-for="${d.dataset.method}"]`, form);
      c.textContent = n || '';
      c.classList.toggle('hidden', !n);
    });
  }
  updateCounts();

  $$('[data-norm-method]', form).forEach((b) => {
    b.onclick = () => {
      const m = LOR.METHODS.find((x) => x.code === b.dataset.normMethod);
      const n = fillNorm(form, m);
      applyLorVisibility(form);
      markDirty();
      toast(n ? t('lor.norm_done', { n }) : t('lor.norm_none'), n ? 'ok' : 'err');
    };
  });
  $$('[data-clear]', form).forEach((b) => {
    b.onclick = () => {
      const d = methodBox(form, b.dataset.clear);
      $$('input[type=checkbox]', d).forEach((c) => { c.checked = false; });
      $$('input.lor__text, textarea', d).forEach((i) => { i.value = ''; });
      applyLorVisibility(form);
      markDirty();
    };
  });
  const rxBody = $('#rx-body', form);
  $('#rx-add', form).onclick = () => { rxBody.insertAdjacentHTML('beforeend', rxRow().s); };
  rxBody.addEventListener('click', (e) => {
    const b = e.target.closest('[data-rx-del]');
    if (!b) return;
    b.closest('tr').remove();
    if (!rxBody.children.length) rxBody.insertAdjacentHTML('beforeend', rxRow().s);
    markDirty();
  });
  const cancelBtn = $('#cancel', el);
  if (cancelBtn) cancelBtn.onclick = () => cancelVisit(v.id, () => { dirty = false; refresh(); });

  form.onsubmit = async (e) => {
    e.preventDefault();
    const mode = e.submitter ? e.submitter.dataset.mode : 'save';
    const body = collect(form);
    if (mode === 'done') {
      if (!body.diagnosis_main) { toast(t('visit.need_dx'), 'err'); form.elements.diagnosis_main.focus(); return; }
      body.status = 'done';
    }
    await busy(e.submitter, async () => {
      const p = await pas.ensure();
      if (!p) return;
      const saved = isNew ? await POST('/api/visits', { ...body, patient_id: p.id }) : await PUT(`/api/visits/${v.id}`, body);
      dirty = false;
      toast(t('saved'));
      if (mode === 'print') printVisit(saved.id);
      if (mode === 'cash') go(`/cash/new?patient=${p.id}&visit=${saved.id}`);
      else if (isNew || mode === 'done') go(`/visit/${saved.id}`);
      else flag.textContent = '';
    });
  };
}

/* ---------- Bemor kartasini tahrirlash formasi (bemor kartasi sahifasida) ---------- */
export function patientForm(p) {
  return html`
    <form class="form patient-form" autocomplete="off">
      ${pasportFields(p, false)}
      <div class="form__dup"></div>
      <div><button class="btn" type="submit">${p.id ? t('save') : t('patient.create')}</button></div>
    </form>`;
}

export function bindPatientForm(f, id, onSaved) {
  const read = () => Object.fromEntries(PATIENT_FIELDS.map((k) => [k, f.elements[k].value.trim()]));
  f.onsubmit = async (e) => {
    e.preventDefault();
    if (!f.reportValidity()) return;
    await busy(f.querySelector('button[type=submit]'), async () => {
      const p = id ? await PUT(`/api/patients/${id}`, read()) : await POST('/api/patients', read());
      toast(t('saved'));
      onSaved(p);
    });
  };
}

/* ================= Tibbiy hujjat (chop etish) ================= */
export function visitDocBody(v) {
  const complaints = LOR.complaintsText(v.complaints || [], state.lang);
  const lor = LOR.lorStatusText(v.lor_status || {}, state.lang);
  const block = (title, content) => (content ? html`<div class="doc__block"><h3>${title}</h3>${content}</div>` : '');
  const p = (s) => (s ? html`<p class="pre">${s}</p>` : '');
  return html`
    <div class="doc__block doc__patient">
      <div><b>${t('f.full_name')}:</b> ${v.patient_name} <span class="muted">(${v.patient_code})</span></div>
      <div><b>${t('f.birth_date')}:</b> ${fmtDate(v.birth_date) || '—'}${v.birth_date ? ` (${age(v.birth_date)} ${t('years')})` : ''}
        ${v.gender ? html` &nbsp; <b>${t('f.gender')}:</b> ${genderText(v.gender)}` : ''}</div>
      ${v.patient_phone ? html`<div><b>${t('f.phone')}:</b> ${v.patient_phone}</div>` : ''}
      ${v.patient_address ? html`<div><b>${t('f.address')}:</b> ${v.patient_address}</div>` : ''}
      <div><b>${t('visit.date')}:</b> ${fmtDateTime(v.visit_at)}</div>
    </div>
    ${block(t('doc.complaints'), complaints || v.complaints_text ? html`
      ${complaints ? html`<p>${complaints}.</p>` : ''}${p(v.complaints_text)}` : '')}
    ${block(t('f.anamnesis'), p(v.anamnesis))}
    ${block(t('doc.lor_status'), lor.length ? html`${lor.map((s) => html`
      <div class="doc__lor"><h4>${s.title}</h4>
        ${s.groups.map((g) => html`${g.sub ? html`<div class="doc__ear">${g.sub}</div>` : ''}
          ${g.lines.map((l) => html`<div><b>${l.label}:</b> ${l.text}</div>`)}`)}
        ${s.note ? html`<p class="pre">${s.note}</p>` : ''}
      </div>`)}` : '')}
    ${block(t('doc.diagnosis'), v.diagnosis_main || v.diagnosis_extra ? html`
      ${v.diagnosis_main ? html`<p><b>${t('f.diagnosis_main')}:</b> ${v.diagnosis_main}</p>` : ''}
      ${v.diagnosis_extra ? html`<p><b>${t('f.diagnosis_extra')}:</b> ${v.diagnosis_extra}</p>` : ''}` : '')}
    ${block(t('f.treatment'), p(v.treatment))}
    ${block(t('f.prescriptions'), v.prescriptions && v.prescriptions.length ? html`
      <table class="doc__table"><thead><tr><th>№</th><th>${t('rx.name')}</th><th>${t('rx.dose')}</th><th>${t('rx.usage')}</th><th>${t('rx.duration')}</th></tr></thead>
      <tbody>${v.prescriptions.map((r, i) => html`<tr><td>${i + 1}</td><td>${r.name}</td><td>${r.dose}</td><td>${r.usage}</td><td>${r.duration}</td></tr>`)}</tbody></table>` : '')}
    ${block(t('f.exams'), p(v.exams))}
    ${block(t('doc.followup'), v.followup_date || v.followup_note ? html`<p>${v.followup_date ? fmtDate(v.followup_date) + '. ' : ''}${v.followup_note}</p>` : '')}`;
}

export async function printVisit(id) {
  try {
    const v = await GET(`/api/visits/${id}` + qs({ print: 1 }));
    printDoc(html`
      <article class="doc">
        ${docHeader()}
        <h2 class="doc__title">${t('doc.title')}</h2>
        ${visitDocBody(v)}
        <footer class="doc__foot">
          <div><b>${t('doc.doctor')}:</b> ${v.doctor_name || ''}${v.doctor_phone ? ` · ${v.doctor_phone}` : ''}</div>
          <div class="doc__sign">${t('doc.signature')}: ____________________</div>
          <div class="muted small">${t('doc.printed')}: ${fmtDate(localDate())} ${new Date().toTimeString().slice(0, 5)}</div>
        </footer>
      </article>`);
  } catch (e) { toast(errorText(e), 'err'); }
}
