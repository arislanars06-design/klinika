// Qabul bo'limi: yangi qabul, elektron tibbiy karta (shikoyat, LOR STATUS, tashxis), chop etish.
import {
  html, raw, render, $, $$, t, L, state, GET, POST, PUT, qs, can, go, toast, errorText, busy,
  confirmDialog, fmtDate, fmtDateTime, age, genderText, statusBadge, patientPicker, patientSummary,
  printDoc, docHeader, localDate, ApiError, refresh,
} from '../core.js';

const LOR = window.LOR;

/* ================= Yangi qabul ================= */
export async function newVisitView(el, query) {
  const presetId = Number(query.get('patient')) || null;
  let patient = null;
  if (presetId) {
    try { patient = (await GET(`/api/patients/${presetId}`)).patient; } catch (e) { toast(errorText(e), 'err'); }
  }

  render(el, html`
    <div class="page-head"><h1>${t('visit.new')}</h1><div class="muted">${t('visit.date')}: ${fmtDateTime(localDate() + ' ' + new Date().toTimeString().slice(0, 5))}</div></div>
    <section class="card">
      <h2 class="step"><span>02</span>${t('visit.step_patient')}</h2>
      <div id="patient-area"></div>
    </section>
    <div id="after-patient"></div>`);

  const area = $('#patient-area', el);
  const after = $('#after-patient', el);

  const choose = (p) => { patient = p; showChosen(); };

  function showChosen() {
    render(area, html`${patientSummary(patient)}
      <button class="btn btn--ghost btn--sm" id="change-patient">${t('visit.change_patient')}</button>`);
    $('#change-patient', area).onclick = () => { patient = null; showSearch(); };
    if (can('visit.clinical.write')) {
      renderClinicalForm(after, { patient_id: patient.id, status: 'open' }, patient, { isNew: true });
    } else {
      renderRegistrarForm(after, patient);
    }
  }

  function showSearch() {
    render(after, '');
    render(area, html`
      <div class="grid2">
        <div><h3>${t('visit.find_patient')}</h3><div id="picker"></div></div>
        <div>
          <h3>${t('visit.new_patient')}</h3>
          ${can('patient.write') ? patientForm({}) : html`<p class="muted">${t('err.forbidden')}</p>`}
        </div>
      </div>`);
    patientPicker($('#picker', area), choose);
    const f = $('form.patient-form', area);
    if (f) bindPatientForm(f, null, choose);
  }

  if (patient) showChosen(); else showSearch();
}

/* ---------- Bemor kartasi formasi (yangi / tahrir) ---------- */
export function patientForm(p) {
  return html`
    <form class="form patient-form" autocomplete="off">
      <label class="field"><span>${t('f.full_name')} *</span><input name="full_name" required maxlength="200" value="${p.full_name || ''}"></label>
      <div class="row">
        <label class="field"><span>${t('f.birth_date')}</span>
          <input name="birth_date" maxlength="10" placeholder="${t('patient.birth_ph')}" pattern="\\d{4}(-\\d{2}-\\d{2})?" value="${p.birth_date || ''}"></label>
        <label class="field"><span>${t('f.gender')}</span>
          <select name="gender">
            <option value="">—</option>
            <option value="m" ${p.gender === 'm' ? raw('selected') : ''}>${t('gender.m')}</option>
            <option value="f" ${p.gender === 'f' ? raw('selected') : ''}>${t('gender.f')}</option>
          </select></label>
      </div>
      <label class="field"><span>${t('f.phone')}</span><input name="phone" type="tel" maxlength="30" placeholder="+998 90 123 45 67" value="${p.phone || ''}"></label>
      <label class="field"><span>${t('f.address')}</span><input name="address" maxlength="300" value="${p.address || ''}"></label>
      <div class="form__dup"></div>
      <button class="btn" type="submit">${p.id ? t('save') : t('patient.create')}</button>
    </form>`;
}

export function bindPatientForm(f, id, onSaved) {
  const read = () => Object.fromEntries(['full_name', 'birth_date', 'gender', 'phone', 'address'].map((k) => [k, f.elements[k].value.trim()]));
  const save = async (force) => {
    const btn = f.querySelector('button[type=submit]');
    btn.disabled = true;
    try {
      const body = { ...read(), force };
      const p = id ? await PUT(`/api/patients/${id}`, body) : await POST('/api/patients', body);
      toast(t('saved'));
      onSaved(p);
    } catch (e) {
      if (e instanceof ApiError && e.code === 'possible_duplicate') {
        const box = $('.form__dup', f);
        render(box, html`
          <div class="alert alert--warn">
            <b>${t('patient.dup_title')}</b>
            ${e.data.matches.map((m) => html`<div class="dup-row"><span>${m.full_name} · ${m.code} · ${fmtDate(m.birth_date)} · ${m.phone}</span>
              <button type="button" class="btn btn--sm" data-use="${m.id}">${t('patient.use_existing')}</button></div>`)}
            <button type="button" class="btn btn--ghost btn--sm" data-force>${t('patient.create_anyway')}</button>
          </div>`);
        box.querySelectorAll('[data-use]').forEach((b) => {
          b.onclick = async () => onSaved((await GET(`/api/patients/${b.dataset.use}`)).patient);
        });
        $('[data-force]', box).onclick = () => save(true);
      } else toast(errorText(e), 'err');
    } finally { btn.disabled = false; }
  };
  f.onsubmit = (e) => { e.preventDefault(); if (f.reportValidity()) save(false); };
}

/* ---------- Registrator: qabulni ro'yxatga olish ---------- */
async function renderRegistrarForm(el, patient) {
  const doctors = await GET('/api/doctors');
  render(el, html`
    <section class="card">
      <h2 class="step"><span>→</span>${t('visit.register')}</h2>
      <form class="form row" id="reg-form">
        <label class="field"><span>${t('f.doctor_id')} *</span>
          <select name="doctor_id" required>
            <option value="">—</option>
            ${doctors.map((d) => html`<option value="${d.id}">${d.full_name}</option>`)}
          </select></label>
        <button class="btn" type="submit">${t('visit.register_btn')}</button>
      </form>
      ${doctors.length ? '' : html`<p class="alert alert--warn">${t('visit.no_doctors')}</p>`}
    </section>`);
  const f = $('#reg-form', el);
  f.onsubmit = async (e) => {
    e.preventDefault();
    if (!f.reportValidity()) return;
    await busy(f.querySelector('button'), async () => {
      await POST('/api/visits', { patient_id: patient.id, doctor_id: Number(f.elements.doctor_id.value) });
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
  if (can('visit.clinical.write') && v.status !== 'cancelled') {
    render(el, html`<div id="visit-form"></div>`);
    return renderClinicalForm($('#visit-form', el), v, patient, { isNew: false });
  }
  return renderReadOnlyVisit(el, v, patient);
}

function visitHead(v, patient) {
  return html`
    <div class="page-head">
      <h1>${t('visit.title')} #${v.id}</h1>
      <div class="page-head__meta">${statusBadge(v.status)}
        <span class="muted">${fmtDateTime(v.visit_at)} · ${t('f.doctor_id')}: ${v.doctor_name || '—'}</span></div>
    </div>
    ${v.status === 'cancelled' ? html`<div class="alert alert--err">${t('visit.cancelled_reason')}: ${v.cancel_reason}</div>` : ''}
    <section class="card">${patientSummary(patient)}</section>`;
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
  const sel = new Set(v.complaints || []);
  return html`
    <section class="card">
      <h2 class="step"><span>03</span>${t('visit.step_complaints')}</h2>
      <div class="complaints">
        ${LOR.COMPLAINTS.map((g) => html`
          <div class="complaints__group"><div class="complaints__title">${L(g)}</div>
            <div class="chips">${g.items.map((i) => chip('complaint', i.code, L(i), sel.has(i.code)))}</div>
          </div>`)}
      </div>
      <label class="field"><span>${t('f.complaints_text')}</span>
        <textarea name="complaints_text" rows="2" maxlength="4000" placeholder="${t('visit.complaints_ph')}">${v.complaints_text || ''}</textarea></label>
      <label class="field"><span>${t('f.anamnesis')}</span>
        <textarea name="anamnesis" rows="3" maxlength="4000" placeholder="${t('visit.anamnesis_ph')}">${v.anamnesis || ''}</textarea></label>
    </section>`;
}

function lorBlock(v) {
  const data = v.lor_status || {};
  return html`
    <section class="card">
      <h2 class="step"><span>04</span>${t('visit.step_lor')}</h2>
      <p class="hint">${t('visit.lor_hint')}</p>
      ${LOR.SECTIONS.map((s) => {
        const sd = data[s.key] || { fields: {}, note: '' };
        const filled = Object.keys(sd.fields || {}).length > 0 || !!sd.note;
        return html`
        <details class="lor" data-sec="${s.key}" ${filled || s.key === 'rhinoscopy' ? raw('open') : ''}>
          <summary><span>${L(s)}</span><span class="lor__count" data-count></span></summary>
          <table class="lor__table">
            <thead><tr><th></th><th>${t('side.r')}</th><th>${t('side.l')}</th><th>${t('lor.note')}</th></tr></thead>
            <tbody>
            ${s.fields.map((f) => {
              const fd = (sd.fields || {})[f.key] || {};
              const n = `lor:${s.key}:${f.key}`;
              const opts = (side) => f.options.map((o) => chip(`${n}:${side}`, o.code, L(o), (fd[side] || []).includes(o.code)));
              return html`<tr>
                <th scope="row">${L(f)}</th>
                ${f.sided
                  ? html`<td><div class="chips chips--sm">${opts('r')}</div></td><td><div class="chips chips--sm">${opts('l')}</div></td>`
                  : html`<td colspan="2"><div class="chips chips--sm">${opts('v')}</div></td>`}
                <td><input class="lor__text" name="${n}:text" maxlength="500" value="${fd.text || ''}"></td>
              </tr>`;
            })}
            </tbody>
          </table>
          <label class="field"><span>${t('lor.section_note')}</span>
            <textarea name="lor:${s.key}:note" rows="2" maxlength="2000">${sd.note || ''}</textarea></label>
          <button type="button" class="btn btn--ghost btn--sm" data-clear="${s.key}">${t('lor.clear')}</button>
        </details>`;
      })}
    </section>`;
}

function diagnosisBlock(v) {
  const rx = v.prescriptions && v.prescriptions.length ? v.prescriptions : [{}];
  return html`
    <section class="card">
      <h2 class="step"><span>05</span>${t('visit.step_diagnosis')}</h2>
      <datalist id="dx-list">${LOR.DIAGNOSES.map((d) => html`<option value="${d.code} — ${L(d)}"></option>`)}</datalist>
      <label class="field"><span>${t('f.diagnosis_main')}</span>
        <input name="diagnosis_main" list="dx-list" maxlength="500" value="${v.diagnosis_main || ''}" placeholder="${t('visit.dx_ph')}"></label>
      <label class="field"><span>${t('f.diagnosis_extra')}</span>
        <input name="diagnosis_extra" maxlength="1000" value="${v.diagnosis_extra || ''}"></label>
      <label class="field"><span>${t('f.treatment')}</span>
        <textarea name="treatment" rows="3" maxlength="4000">${v.treatment || ''}</textarea></label>
      <div class="field"><span>${t('f.prescriptions')}</span>
        <table class="rx">
          <thead><tr><th>${t('rx.name')}</th><th>${t('rx.dose')}</th><th>${t('rx.usage')}</th><th>${t('rx.duration')}</th><th></th></tr></thead>
          <tbody id="rx-body">${rx.map(rxRow)}</tbody>
        </table>
        <button type="button" class="btn btn--ghost btn--sm" id="rx-add">+ ${t('rx.add')}</button>
      </div>
      <label class="field"><span>${t('f.exams')}</span>
        <textarea name="exams" rows="2" maxlength="2000" placeholder="${t('visit.exams_ph')}">${v.exams || ''}</textarea></label>
      <div class="row">
        <label class="field"><span>${t('f.followup_date')}</span><input type="date" name="followup_date" value="${v.followup_date || ''}"></label>
        <label class="field field--grow"><span>${t('f.followup_note')}</span><input name="followup_note" maxlength="1000" value="${v.followup_note || ''}"></label>
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
  for (const s of LOR.SECTIONS) {
    const fields = {};
    for (const f of s.fields) {
      const n = `lor:${s.key}:${f.key}`;
      const item = {};
      for (const side of f.sided ? ['r', 'l'] : ['v']) {
        const vals = fd.getAll(`${n}:${side}`);
        if (vals.length) item[side] = vals;
      }
      const text = (fd.get(`${n}:text`) || '').trim();
      if (text) item.text = text;
      if (Object.keys(item).length) fields[f.key] = item;
    }
    const note = (fd.get(`lor:${s.key}:note`) || '').trim();
    if (Object.keys(fields).length || note) lor[s.key] = { fields, note };
  }
  const prescriptions = $$('.rx__row', form).map((tr) => Object.fromEntries($$('[data-rx]', tr).map((i) => [i.dataset.rx, i.value.trim()])))
    .filter((r) => r.name);
  const g = (k) => (fd.get(k) || '').trim();
  return {
    complaints: fd.getAll('complaint'), complaints_text: g('complaints_text'), anamnesis: g('anamnesis'), lor_status: lor,
    diagnosis_main: g('diagnosis_main'), diagnosis_extra: g('diagnosis_extra'), treatment: g('treatment'), prescriptions,
    exams: g('exams'), followup_date: g('followup_date'), followup_note: g('followup_note'),
  };
}

async function renderClinicalForm(el, v, patient, { isNew }) {
  let history = [];
  try { history = (await GET(`/api/patients/${patient.id}`)).visits.filter((x) => x.id !== v.id); } catch { /* ixtiyoriy */ }

  render(el, html`
    ${isNew ? '' : visitHead(v, patient)}
    <div class="visit-layout">
      <form id="clinical" class="visit-main" autocomplete="off">
        ${complaintsBlock(v)}
        ${lorBlock(v)}
        ${diagnosisBlock(v)}
        <section class="card sticky-actions">
          <h2 class="step"><span>06</span>${t('visit.step_save')}</h2>
          <div class="actions">
            <button type="submit" class="btn" data-mode="save">${t('save')}</button>
            <button type="submit" class="btn btn--ok" data-mode="done">${t('visit.finish')}</button>
            <button type="submit" class="btn btn--ghost" data-mode="print">${t('visit.save_print')}</button>
            ${!isNew && can('visit.cancel') ? html`<button type="button" class="btn btn--danger" id="cancel">${t('visit.cancel')}</button>` : ''}
            <span class="muted small" id="dirty-flag"></span>
          </div>
          ${!isNew && v.updated_at ? html`<p class="muted small">${t('visit.updated')}: ${fmtDateTime(v.updated_at)} · ${v.updated_by_name || ''}</p>` : ''}
        </section>
      </form>
      <aside class="visit-side card">
        <h3>${t('visit.history')}</h3>
        ${history.length ? html`<ul class="hist">${history.map((h) => html`
          <li><a href="#/visit/${h.id}">${fmtDate(h.visit_at)}</a> ${h.status === 'cancelled' ? statusBadge('cancelled') : ''}
            <div class="small">${h.diagnosis_main || html`<span class="muted">${t('visit.no_dx')}</span>`}</div>
            <div class="muted small">${h.doctor_name || ''}</div></li>`)}</ul>`
          : html`<p class="muted">${t('visit.first_visit')}</p>`}
      </aside>
    </div>`);

  const form = $('#clinical', el);
  let dirty = false;
  const flag = $('#dirty-flag', el);
  const markDirty = () => { dirty = true; flag.textContent = t('visit.unsaved'); updateCounts(); };
  form.addEventListener('input', markDirty);
  form.addEventListener('change', markDirty);
  state.leaveGuard = { dirty: () => dirty };

  function updateCounts() {
    $$('details.lor', form).forEach((d) => {
      const n = $$('input[type=checkbox]:checked', d).length + $$('.lor__text', d).filter((i) => i.value.trim()).length;
      $('[data-count]', d).textContent = n ? `${t('lor.recorded')}: ${n}` : t('lor.not_recorded');
    });
  }
  updateCounts();

  $$('[data-clear]', form).forEach((b) => {
    b.onclick = () => {
      const d = b.closest('details');
      $$('input[type=checkbox]', d).forEach((c) => { c.checked = false; });
      $$('input.lor__text, textarea', d).forEach((i) => { i.value = ''; });
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
      const saved = isNew ? await POST('/api/visits', { ...body, patient_id: patient.id })
        : await PUT(`/api/visits/${v.id}`, body);
      dirty = false;
      toast(t('saved'));
      if (mode === 'print') printVisit(saved.id);
      if (isNew || mode === 'done') go(`/visit/${saved.id}`);
      else { flag.textContent = ''; }
    });
  };
}

/* ================= Tibbiy hujjat (chop etish) ================= */
function labelOf(field, code) {
  const o = field.options.find((x) => x.code === code);
  return o ? L(o) : code;
}

export function lorStatusText(lor) {
  const out = [];
  for (const s of LOR.SECTIONS) {
    const sd = lor[s.key];
    if (!sd) continue;
    const lines = [];
    for (const f of s.fields) {
      const fd = sd.fields[f.key];
      if (!fd) continue;
      const parts = [];
      if (f.sided) {
        if (fd.r) parts.push(`${t('side.r')}: ${fd.r.map((c) => labelOf(f, c)).join(', ')}`);
        if (fd.l) parts.push(`${t('side.l')}: ${fd.l.map((c) => labelOf(f, c)).join(', ')}`);
      } else if (fd.v) parts.push(fd.v.map((c) => labelOf(f, c)).join(', '));
      if (fd.text) parts.push(fd.text);
      lines.push({ label: L(f), text: parts.join('; ') });
    }
    out.push({ title: L(s), lines, note: sd.note });
  }
  return out;
}

export function visitDocBody(v) {
  const complaints = (v.complaints || []).map((c) => LOR.complaintLabel(c, state.lang));
  const lor = lorStatusText(v.lor_status || {});
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
    ${block(t('doc.complaints'), complaints.length || v.complaints_text ? html`
      ${complaints.length ? html`<p>${complaints.join(', ')}.</p>` : ''}${p(v.complaints_text)}` : '')}
    ${block(t('f.anamnesis'), p(v.anamnesis))}
    ${block(t('doc.lor_status'), lor.length ? html`${lor.map((s) => html`
      <div class="doc__lor"><h4>${s.title}</h4>
        ${s.lines.map((l) => html`<div><b>${l.label}:</b> ${l.text}</div>`)}
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
