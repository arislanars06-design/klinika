// Qabul bo'limi: yangi qabul (pasport ma'lumotlari shu oynaning o'zida), elektron tibbiy karta
// (shikoyat, LOR STATUS, tashxis), chop etish va kassaga o'tish.
import {
  html, raw, render, $, $$, t, L, state, GET, POST, PUT, qs, can, go, toast, errorText, busy,
  confirmDialog, fmtDate, fmtDateTime, age, genderText, statusBadge, patientSummary,
  printDoc, docHeader, localDate, ApiError, refresh, showWordButton, modal,
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
  // «Даволаш режаси» yangi qabulda shablon bilan to'ladi (Созламалар → Клиника), shifokor tahrirlaydi
  if (can('visit.clinical.write')) return renderVisitForm(el, { status: 'open', treatment: state.settings.treatment_template || '' }, patient, { isNew: true });
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
      ${addressFields(p.address || '', locked)}
    </div>`;
}

/* ---------- Manzil: hudud → tuman → ko'cha/uy (O'zbekiston bo'yicha) ---------- */
const REGIONS = window.ADDRESS_UZ || [];
/** Saqlangan manzil matnidan hudud, tuman va qolgan qismni ajratish */
function parseAddress(a) {
  const s = String(a || '').trim();
  for (const [ri, r] of REGIONS.entries()) {
    if (!s.startsWith(r[0])) continue;
    let rest = s.slice(r[0].length).replace(/^[,\s]+/, '');
    for (const [di, dname] of r[2].entries()) {
      if (rest.startsWith(dname[0])) return { ri, di, rest: rest.slice(dname[0].length).replace(/^[,\s]+/, '') };
    }
    return { ri, di: -1, rest };
  }
  return { ri: -1, di: -1, rest: s };
}
function addressFields(addr, locked) {
  const a = parseAddress(addr);
  const dis = locked ? raw('disabled') : '';
  const districts = a.ri >= 0 ? REGIONS[a.ri][2] : [];
  return html`
    <label class="field"><span>${t('addr.region')}</span>
      <select name="addr_region" ${dis}><option value="">—</option>
        ${REGIONS.map((r, i) => html`<option value="${i}" ${i === a.ri ? raw('selected') : ''}>${L({ uz: r[0], ru: r[1] })}</option>`)}</select></label>
    <label class="field"><span>${t('addr.district')}</span>
      <select name="addr_district" ${dis} ${a.ri < 0 ? raw('disabled') : ''}><option value="">—</option>
        ${districts.map((d, i) => html`<option value="${i}" ${i === a.di ? raw('selected') : ''}>${L({ uz: d[0], ru: d[1] })}</option>`)}</select></label>
    <label class="field field--wide"><span>${t('addr.street')}</span>
      <input name="addr_rest" maxlength="200" placeholder="${t('addr.street_ph')}" value="${a.rest}" ${dis}></label>
    <input type="hidden" name="address" value="${addr}">`;
}
/** Manzil maydonlarini bog'lash: hudud tanlanganda tumanlar to'ladi, yashirin "address" yangilanadi */
export function bindAddress(root) {
  const reg = $('[name=addr_region]', root);
  if (!reg) return;
  const dist = $('[name=addr_district]', root);
  const rest = $('[name=addr_rest]', root);
  const out = $('input[name=address]', root);
  const compose = () => {
    const r = REGIONS[Number(reg.value)];
    const d = r && dist.value !== '' ? r[2][Number(dist.value)] : null;
    out.value = [r ? r[0] : '', d ? d[0] : '', rest.value.trim()].filter(Boolean).join(', ');
  };
  reg.addEventListener('change', () => {
    const r = REGIONS[Number(reg.value)];
    render(dist, html`<option value="">—</option>${(r ? r[2] : []).map((d, i) => html`<option value="${i}">${L({ uz: d[0], ru: d[1] })}</option>`)}`);
    dist.disabled = !r;
    compose();
  });
  dist.addEventListener('change', compose);
  rest.addEventListener('input', compose);
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
    bindAddress(body);
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
      ${showWordButton() ? html`<button class="btn btn--ghost" id="word">${t('word')}</button>` : ''}
      ${can('billing.write') && v.status !== 'cancelled' ? html`<a class="btn btn--ghost" href="#/cash/new?patient=${v.patient_id}&visit=${v.id}">${t('visit.cash')}</a>` : ''}
      ${can('visit.cancel') && v.status !== 'cancelled' ? html`<button class="btn btn--danger" id="cancel">${t('visit.cancel')}</button>` : ''}
    </div>`);
  $('#print', el).onclick = () => printVisit(v.id);
  if ($('#word', el)) $('#word', el).onclick = () => printVisit(v.id, 'word');
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
  (v.complaints || []).forEach((c) => { const x = typeof c === 'string' ? { code: c } : c; sel[LOR.complaintCode(x.code)] = { ...x, code: LOR.complaintCode(x.code) }; });
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
      <div class="complaints-from"><span class="complaints-from__label">${t('visit.complaints_from')}:</span>
        <div class="chips chips--sm">${LOR.RELATIVES.map((r) => chip('complaints_from', r.code, L(r), v.complaints_from === r.code))}</div></div>
      ${Object.keys(sel).filter(LOR.isRetiredComplaint).map((c) => html`<input type="hidden" name="complaint" value="${c}">`)}
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

/* Input nomi: lor|<metod>|<tomon yoki ->|<qism>|<maydon>. Radio, tomon va daraja ham checkbox
   ko‘rinishida chiziladi (data-single): bittasi tanlanadi, qayta bosilsa tanlov olib tashlanadi. */
const lorName = (m, ear, p, f) => `lor|${m}|${ear || '-'}|${p}|${f}`;
const methodBox = (form, code) => $(`.lor[data-method="${code}"]`, form);
const fieldLabel = (f) => (f.uz ? L(f) : LOR.FIELD_LABELS[f.code] ? L(LOR.FIELD_LABELS[f.code]) : '');

function lorParts(m, ear, parts, list) {
  return html`${list.map((p) => {
    const pv = parts[p.code] || {};
    return html`<div class="lor-part ${LOR.partVisible(p, parts) ? '' : 'hidden'}" data-part="${p.code}" data-ear="${ear || ''}">
      <div class="lor-part__title">${L(p)}</div>
      <div class="lor-part__fields">
        ${p.fields.map((f) => {
          const n = lorName(m.code, ear, p.code, f.code);
          const cur = pv[f.code];
          const has = (c) => (Array.isArray(cur) ? cur.includes(c) : cur === c);
          const single = ['radio', 'side', 'degree'].includes(f.type);
          let body;
          if (f.type === 'checkbox') {
            body = html`<label class="chip"><input type="checkbox" name="${n}" value="1" ${cur ? raw('checked') : ''}><span>${L(f)}</span></label>`;
          } else if (f.type === 'text') {
            body = html`<input class="lor__field-text" name="${n}" maxlength="300" placeholder="${f.ph ? L(f.ph) : ''}" value="${cur || ''}">`;
          } else {
            body = LOR.choicesOf(f).map((c) => html`<label class="chip"><input type="checkbox" name="${n}" value="${c.code}"
                ${single ? raw('data-single') : ''} ${c.is_norm ? raw('data-norm') : ''} ${has(c.code) ? raw('checked') : ''}><span>${L(c)}</span></label>`);
          }
          const label = f.type !== 'checkbox' && p.fields.length > 1 ? fieldLabel(f) : '';
          return html`<div class="lor-field ${LOR.fieldVisible(f, pv) ? '' : 'hidden'}" data-field="${f.code}">
            ${label ? html`<span class="lor-field__label">${label}:</span>` : ''}
            ${f.type === 'text' ? body : html`<div class="chips chips--sm">${body}</div>`}</div>`;
        })}
        <input class="lor__text" name="${lorName(m.code, ear, p.code, '_text')}" maxlength="500" placeholder="${t('lor.note')}" value="${pv._text || ''}">
      </div>
    </div>`;
  })}`;
}

function lorMethodBody(m, mv) {
  if (!m.ears) return lorParts(m, '', mv.parts || {}, m.parts);
  const common = LOR.commonParts(m);
  const same = !!(m.same_toggle && mv.same);
  return html`
    ${lorParts(m, '', mv.parts || {}, common.filter((p) => p.common === 'before'))}
    ${m.same_toggle ? html`<label class="inline lor-same"><input type="checkbox" name="lorsame|${m.code}" ${same ? raw('checked') : ''}> ${L(m.same_label)}</label>` : ''}
    <div class="lor-ears">${m.ears.map((e, i) => html`<div class="lor-ear ${same && i > 0 ? 'hidden' : ''}" data-ear-box="${e.code}">
      <h4 class="lor-ear__title">${L(e)}</h4>${lorParts(m, e.code, (mv.ears || {})[e.code] || {}, LOR.sideParts(m))}</div>`)}</div>
    ${lorParts(m, '', mv.parts || {}, common.filter((p) => p.common !== 'before'))}`;
}

function lorBlock(v) {
  const data = v.lor_status || {};
  const legacy = Object.keys(data).some((k) => LOR.LEGACY_CODES.has(k));
  return html`
    <section class="card">
      <div class="card-head"><h2>${t('visit.step_lor')}</h2></div>
      ${legacy ? html`<p class="alert alert--warn">${t('lor.legacy_note')}</p>` : ''}
      <div class="tabs lor-tabs" role="tablist">
        ${LOR.GROUPS.map((g, i) => html`<button type="button" class="tab ${i === 0 ? 'tab--active' : ''}" data-lor-tab="${g.code}">
          ${L(g)}<span class="tab__count hidden" data-count-for="${g.code}"></span></button>`)}
      </div>
      ${LOR.GROUPS.map((g, gi) => html`<div class="lor-group ${gi === 0 ? '' : 'hidden'}" data-group="${g.code}">
      ${g.methods.map((code) => {
        const m = LOR.METHODS.find((x) => x.code === code);
        const mv = data[m.code] || {};
        return html`
        <div class="lor" data-method="${m.code}">
          <h3 class="lor__title">${L(m)}</h3>
          ${lorMethodBody(m, mv)}
          <div class="lor__foot">
            <label class="field"><span>${t('lor.section_note')}</span>
              <textarea name="lornote|${m.code}" rows="1" maxlength="2000">${mv.note || ''}</textarea></label>
            <button type="button" class="btn btn--ghost btn--sm" data-norm-method="${m.code}">${t('lor.norm')}</button>
            <button type="button" class="btn btn--ghost btn--sm" data-clear="${m.code}">${t('lor.clear')}</button>
          </div>
        </div>`;
      })}</div>`)}
      <p class="hint">${t('visit.lor_hint')}</p>
    </section>`;
}

/** Formadagi tanlovlardan qism qiymatlarini o‘qish */
function readParts(form, m, ear, list) {
  const parts = {};
  for (const p of list) {
    const pv = {};
    for (const f of p.fields) {
      const n = lorName(m.code, ear, p.code, f.code);
      if (f.type === 'text') {
        const inp = form.elements[n];
        if (inp && inp.value.trim()) pv[f.code] = inp.value.trim();
        continue;
      }
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

const sameChecked = (form, m) => !!(m.same_toggle && form.elements[`lorsame|${m.code}`] && form.elements[`lorsame|${m.code}`].checked);

/** Bitta metodning qiymati (forma → ma'lumot) */
function readMethod(form, m) {
  const res = {};
  const common = readParts(form, m, '', LOR.commonParts(m));
  if (Object.keys(common).length) res.parts = common;
  if (m.ears) {
    const same = sameChecked(form, m);
    const ears = {};
    m.ears.forEach((e, i) => {
      if (same && i > 0) return;
      const p = readParts(form, m, e.code, LOR.sideParts(m));
      if (Object.keys(p).length) ears[e.code] = p;
    });
    if (Object.keys(ears).length) res.ears = ears;
    if (same && Object.keys(res).length) res.same = true;
  }
  return res;
}

/**
 * "Норма" tugmasi: shifokor o‘zi bosganda, shu metoddagi faqat BO‘SH maydonlarga norma variantini qo‘yadi.
 * Shifokor allaqachon tanlagan qiymatlar o‘zgarmaydi. Shartli maydonlar (masalan, gipertrofiya darajasi)
 * to‘ldirilmaydi, chunki ular faqat patologiya tanlanganda ma’noga ega. Natija: to‘ldirilgan maydonlar soni.
 */
function fillNorm(form, m) {
  let n = 0;
  for (const set of LOR.partSets(m)) {
    for (const p of set.parts) {
      const box = $(`.lor-part[data-part="${p.code}"][data-ear="${set.ear}"]`, methodBox(form, m.code));
      if (!box || box.classList.contains('hidden') || box.closest('.lor-ear.hidden')) continue;
      for (const f of p.fields) {
        if (f.when) continue;
        const norm = LOR.choicesOf(f).find((c) => c.is_norm);
        if (!norm) continue;
        const inputs = $$(`input[name="${CSS.escape(lorName(m.code, set.ear, p.code, f.code))}"]`, box);
        if (inputs.some((i) => i.checked)) continue;
        const target = inputs.find((i) => i.value === norm.code);
        if (target) { target.checked = true; n += 1; }
      }
    }
  }
  return n;
}

/** Shartli maydon va qismlarni ko‘rsatish/yashirish. Yashiringan maydon qiymatlari tozalanadi. */
function applyLorVisibility(form) {
  const clear = (root) => {
    $$('input[type=checkbox]:checked', root).forEach((i) => { i.checked = false; });
    $$('input.lor__field-text', root).forEach((i) => { i.value = ''; });
  };
  for (const m of LOR.METHODS) {
    const mb = methodBox(form, m.code);
    if (m.same_toggle) {
      const same = sameChecked(form, m);
      m.ears.forEach((e, i) => { if (i > 0) $(`[data-ear-box="${e.code}"]`, mb).classList.toggle('hidden', same); });
    }
    for (const set of LOR.partSets(m)) {
      const parts = readParts(form, m, set.ear, set.parts);
      for (const p of set.parts) {
        const box = $(`.lor-part[data-part="${p.code}"][data-ear="${set.ear}"]`, mb);
        if (!box) continue;
        const pvis = LOR.partVisible(p, parts);
        box.classList.toggle('hidden', !pvis);
        for (const f of p.fields) {
          const fbox = $(`.lor-field[data-field="${f.code}"]`, box);
          const vis = pvis && LOR.fieldVisible(f, parts[p.code] || {});
          fbox.classList.toggle('hidden', !vis);
          if (!vis) clear(fbox);
        }
        if (!pvis) clear(box);
      }
    }
  }
}

/** Eski formatdagi dorilar jadvalini (dori, doza, usul, muddat) bitta "Тавсия" matniga aylantiradi */
const legacyRx = (rx) => (Array.isArray(rx) ? rx : [])
  .map((r) => [r.name, r.dose, r.usage, r.duration].filter(Boolean).join(', ')).filter(Boolean).join('\n');
const recommendationOf = (v) => v.recommendation || legacyRx(v.prescriptions);

function diagnosisBlock(v) {
  return html`
    <section class="card">
      <h2>${t('visit.step_diagnosis')}</h2>
      <datalist id="dx-list">${(window.ICD10_LOR || LOR.DIAGNOSES).map((d) => html`<option value="${d.code} — ${L(d)}"></option>`)}</datalist>
      <div class="grid-fields">
        <label class="field field--wide"><span>${t('f.diagnosis_main')}</span>
          <input name="diagnosis_main" list="dx-list" maxlength="500" value="${v.diagnosis_main || ''}" placeholder="${t('visit.dx_ph')}"></label>
        <label class="field field--wide"><span>${t('f.diagnosis_extra')}</span>
          <input name="diagnosis_extra" list="dx-list" maxlength="1000" value="${v.diagnosis_extra || ''}" placeholder="${t('visit.dx_ph')}"></label>
        <label class="field field--wide"><span>${t('f.treatment')}</span>
          <textarea name="treatment" rows="2" maxlength="4000">${v.treatment || ''}</textarea></label>
        <label class="field field--wide"><span>${t('f.exams')}</span>
          <textarea name="exams" rows="2" maxlength="2000" placeholder="${t('visit.exams_ph')}">${v.exams || ''}</textarea></label>
      </div>
      <label class="field"><span>${t('f.recommendation')}</span>
        <textarea name="recommendation" rows="3" maxlength="4000" placeholder="${t('visit.recommendation_ph')}">${recommendationOf(v)}</textarea></label>
      <div class="grid-fields">
        <label class="field"><span>${t('f.followup_date')}</span><input type="date" name="followup_date" value="${v.followup_date || ''}"></label>
        <label class="field field--wide"><span>${t('f.followup_note')}</span><input name="followup_note" maxlength="1000" value="${v.followup_note || ''}"></label>
      </div>
    </section>`;
}

function collect(form, legacyLor = {}) {
  const fd = new FormData(form);
  // Eski shablondagi LOR STATUS (formada ko'rsatilmaydi) o'zgarmasdan saqlanadi
  const lor = { ...legacyLor };
  for (const m of LOR.METHODS) {
    const res = readMethod(form, m);
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
  const g = (k) => (fd.get(k) || '').trim();
  return {
    complaints, complaints_from: fd.get('complaints_from') || '', complaints_text: g('complaints_text'), anamnesis: g('anamnesis'), lor_status: lor,
    diagnosis_main: g('diagnosis_main'), diagnosis_extra: g('diagnosis_extra'), treatment: g('treatment'), recommendation: g('recommendation'), prescriptions: [],
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
          ${showWordButton() ? html`<button type="submit" class="btn btn--ghost" data-mode="word">${t('word')}</button>` : ''}
          ${can('billing.write') ? html`<button type="submit" class="btn btn--ghost" data-mode="cash">${t('visit.cash')}</button>` : ''}
          ${!isNew && can('visit.cancel') ? html`<button type="button" class="btn btn--danger" id="cancel">${t('visit.cancel')}</button>` : ''}
          <span class="spacer"></span>
          <span class="muted small" id="dirty-flag">${!isNew && v.updated_at ? `${t('visit.updated')}: ${fmtDateTime(v.updated_at)} · ${v.updated_by_name || ''}` : ''}</span>
        </div>
      </form>
      <aside class="visit-side">
        <section class="card card--tight">
          <h3>${t('visit.history')}</h3>
          <div id="history"><p class="muted small">—</p></div>
        </section>
        <section class="card card--tight doc-live-card">
          <div class="card-head"><h3>${t('visit.preview')}</h3>
            <button type="button" class="btn btn--ghost btn--sm" id="preview-big">${t('visit.preview_big')}</button></div>
          <div class="doc-live" id="doc-live"><div class="doc-live__page"></div></div>
        </section>
      </aside>
    </div>`);

  const form = $('#clinical', el);
  const legacyLor = Object.fromEntries(Object.entries(v.lor_status || {}).filter(([k]) => LOR.LEGACY_CODES.has(k)));
  const loadHistory = async (p) => {
    const box = $('#history', el);
    if (!p) { render(box, html`<p class="muted small">—</p>`); return; }
    try { render(box, historyList((await GET(`/api/patients/${p.id}`)).visits.filter((x) => x.id !== v.id && x.status !== 'cancelled'))); } catch { /* ixtiyoriy */ }
  };
  const pas = pasportController($('[data-pasport]', el), patient, {
    canChange: isNew, onPatient: (p) => { loadHistory(p); schedulePreview(); } });
  loadHistory(patient);

  /* Jonli ko'rinish: Word/chop etish shablonining o'zi, formadagi joriy ma'lumot bilan (saqlanmagan bo'lsa ham) */
  const live = $('#doc-live', el);
  const page = $('.doc-live__page', live);
  const previewVisit = () => {
    const p = pas.get();
    const f = (n) => { const i = $(`[data-pasport] [name=${n}]`, el); return i ? i.value.trim() : ''; };
    const now = localDate() + ' ' + new Date().toTimeString().slice(0, 5);
    const doctor = isNew ? state.user : {};
    return {
      ...v, ...collect(form, legacyLor),
      patient_name: p ? p.full_name : f('full_name') || '—', patient_code: p ? p.code : '',
      birth_date: p ? p.birth_date : f('birth_date'), gender: p ? p.gender : f('gender'),
      patient_phone: p ? p.phone : f('phone'), patient_address: p ? p.address : f('address'),
      visit_at: v.visit_at || now,
      doctor_name: v.doctor_name || doctor.full_name || '', doctor_phone: v.doctor_phone || doctor.phone || '',
    };
  };
  const drawPreview = () => { if (page.isConnected) render(page, visitDocArticle(previewVisit())); };
  let previewTimer;
  function schedulePreview() { clearTimeout(previewTimer); previewTimer = setTimeout(drawPreview, 250); }
  // A5 sahifa (148 mm) yon panel kengligiga moslab kichraytiriladi
  const fit = () => { const w = live.clientWidth - 12; if (w > 0) page.style.zoom = String(Math.min(1, w / A5_PX)); };
  new ResizeObserver(fit).observe(live);
  $('#preview-big', el).onclick = () => modal(html`
    <div class="dialog__body">
      <div class="doc-live doc-live--big"><div class="doc-live__page">${visitDocArticle(previewVisit())}</div></div>
      <div class="dialog__actions"><button type="button" class="btn" data-close>${t('close')}</button></div>
    </div>`, (dlg) => dlg.classList.add('dialog--doc'));

  let dirty = false;
  const flag = $('#dirty-flag', el);
  const markDirty = () => { dirty = true; flag.textContent = t('visit.unsaved'); updateCounts(); schedulePreview(); };
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
    if (i.name.startsWith('lor|') || i.name.startsWith('lorsame|')) applyLorVisibility(form);
    if (i.name === 'complaint') {
      const box = $(`[data-discharge-for="${CSS.escape(i.value)}"]`, form);
      if (box) {
        box.classList.toggle('hidden', !i.checked);
        if (!i.checked) { $('select', box).value = ''; $('input', box).value = ''; $('input', box).classList.add('hidden'); }
      }
    }
    if (i.name.startsWith('cdis|')) i.nextElementSibling.classList.toggle('hidden', i.value !== 'other');
    // «Яқинининг сўзидан»: bittasi tanlanadi, qayta bosilsa olib tashlanadi
    if (i.name === 'complaints_from' && i.checked) $$('input[name=complaints_from]', form).forEach((x) => { if (x !== i) x.checked = false; });
    markDirty();
  });
  state.leaveGuard = { dirty: () => dirty };

  // LOR STATUS tablari
  $$('[data-lor-tab]', form).forEach((b) => {
    b.onclick = () => {
      $$('[data-lor-tab]', form).forEach((x) => x.classList.toggle('tab--active', x === b));
      $$('.lor-group[data-group]', form).forEach((p) => p.classList.toggle('hidden', p.dataset.group !== b.dataset.lorTab));
    };
  });
  function updateCounts() {
    // Tab yonidagi son: shu bo'limda (masalan, Фарингоскопия → эпи-, мезо-, гипо-) to'ldirilgan qismlar
    $$('.lor-group[data-group]', form).forEach((d) => {
      const n = $$('.lor-part', d).filter((p) => $$('input[type=checkbox]:checked', p).length
        || $$('.lor__text, .lor__field-text', p).some((i) => i.value.trim())).length;
      const c = $(`[data-count-for="${d.dataset.group}"]`, form);
      c.textContent = n || '';
      c.classList.toggle('hidden', !n);
    });
  }
  updateCounts();
  drawPreview();

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
      $$('input.lor__text, input.lor__field-text, textarea', d).forEach((i) => { i.value = ''; });
      applyLorVisibility(form);
      markDirty();
    };
  });
  const cancelBtn = $('#cancel', el);
  if (cancelBtn) cancelBtn.onclick = () => cancelVisit(v.id, () => { dirty = false; refresh(); });

  form.onsubmit = async (e) => {
    e.preventDefault();
    const mode = e.submitter ? e.submitter.dataset.mode : 'save';
    const body = collect(form, legacyLor);
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
      if (mode === 'print' || mode === 'word') printVisit(saved.id, mode);
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
  bindAddress(f);
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
  const complaints = LOR.complaintsText(v.complaints || [], state.lang, { dative: true });
  const from = LOR.relative(v.complaints_from);
  // «ШИКОЯТИ: Онасининг сўзидан бош оғриғига, …» / «ЖАЛОБЫ: Со слов матери: головная боль, …»
  const fromPrefix = from ? upperFirst(L(from.from)) + (state.lang === 'ru' ? ': ' : ' ') : '';
  const lor = LOR.lorStatusText(v.lor_status || {}, state.lang);
  // LOR STATUS bo'limlar bo'yicha: ФАРИНГОСКОПИЯ (эпи-, мезо-, гипо-), РИНОСКОПИЯ, ОТОСКОПИЯ, …
  const lorGroups = [];
  for (const s of lor) {
    const g = s.group ? LOR.GROUPS.find((x) => x.code === s.group) : null;
    const last = lorGroups[lorGroups.length - 1];
    if (g && last && last.g === g) last.items.push(s); else lorGroups.push({ g, items: [s] });
  }
  const upper = (s) => String(s).toUpperCase();
  const lorItem = (s, title) => html`
      <div class="doc__lor"><h4>${title}</h4>
        ${s.groups.map((g) => (g.table ? html`<table class="doc__table doc__lor-table"><thead><tr><th>${g.table.head[0]}</th><th>${g.table.test}</th><th>${g.table.head[1]}</th></tr></thead>
          <tbody>${g.table.rows.map((r) => html`<tr><td>${r.vals[0]}</td><td>${r.label}</td><td>${r.vals[1]}</td></tr>`)}</tbody></table>`
          : html`<div class="doc__grp">${g.sub ? html`<span class="doc__ear">${g.sub}</span> ` : ''}${g.lines.map((l) => html`<span class="doc__ln"><b>${l.label}:</b> ${l.text}</span>`)}</div>`))}
        ${s.note ? html`<p class="pre">${s.note}</p>` : ''}
      </div>`;
  const rec = recommendationOf(v);
  const block = (title, content) => (content ? html`<div class="doc__block"><h3>${title}</h3>${content}</div>` : '');
  const p = (s) => (s ? html`<p class="pre">${s}</p>` : '');
  return html`
    <div class="doc__block doc__patient">
      <div class="doc__wide"><b>${t('f.full_name')}:</b> ${v.patient_name}</div>
      <div><b>${t('f.birth_date')}:</b> ${fmtDate(v.birth_date) || '—'}${v.birth_date ? ` (${age(v.birth_date)} ${t('years')})` : ''}
        ${v.gender ? html` &nbsp; <b>${t('f.gender')}:</b> ${genderText(v.gender)}` : ''}</div>
      ${v.patient_phone ? html`<div><b>${t('f.phone')}:</b> ${v.patient_phone}</div>` : ''}
      ${v.patient_address ? html`<div><b>${t('f.address')}:</b> ${v.patient_address}</div>` : ''}
      <div><b>${t('visit.date')}:</b> ${fmtDateTime(v.visit_at)}</div>
    </div>
    ${block(t('doc.complaints'), complaints || v.complaints_text ? html`
      ${complaints ? html`<p>${from ? fromPrefix + lowerFirst(complaints) : complaints}.</p>` : ''}
      ${v.complaints_text ? html`<p class="pre">${from && !complaints ? fromPrefix : ''}${v.complaints_text}</p>` : ''}` : '')}
    ${block(t('f.anamnesis'), p(v.anamnesis))}
    ${block(t('doc.lor_status'), lorGroups.length ? html`${lorGroups.map(({ g, items }) => {
      // Bir nechta kichik bo'limli guruh: alohida sarlavha + «Эпифарингоскопия: …»; bitta bo'limli: «РИНОСКОПИЯ: …»
      const multi = g && g.methods.length > 1;
      return html`<div class="doc__lorgrp">${multi ? html`<div class="doc__lorhead">${upper(L(g))}</div>` : ''}
        ${items.map((s) => lorItem(s, multi || !g ? s.title : upper(L(g))))}</div>`;
    })}` : '')}
    ${block(t('doc.diagnosis'), v.diagnosis_main || v.diagnosis_extra ? (v.diagnosis_main && !v.diagnosis_extra
      ? html`<p>${v.diagnosis_main}</p>`
      : html`
      ${v.diagnosis_main ? html`<p><b>${t('f.diagnosis_main')}:</b> ${v.diagnosis_main}</p>` : ''}
      ${v.diagnosis_extra ? html`<p><b>${t('f.diagnosis_extra')}:</b> ${v.diagnosis_extra}</p>` : ''}`) : '')}
    ${block(t('f.treatment'), p(v.treatment))}
    ${rec ? html`<div class="doc__block"><table class="doc__table doc__rec"><thead><tr><th>${upper(t('f.recommendation'))}</th></tr></thead>
      <tbody><tr><td><p class="pre">${rec}</p></td></tr></tbody></table></div>` : ''}
    ${block(t('f.exams'), p(v.exams))}
    ${block(t('doc.followup'), v.followup_date || v.followup_note ? html`<p>${v.followup_date ? fmtDate(v.followup_date) + '. ' : ''}${v.followup_note}</p>` : '')}`;
}

const A5_PX = (148 / 25.4) * 96; // A5 kengligi CSS pikselda
const upperFirst = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);
const lowerFirst = (s) => (/^\p{Lu}\p{Ll}/u.test(s) ? s[0].toLowerCase() + s.slice(1) : s);

/** Qabul hujjati: chop etish, Word va jonli ko'rinish uchun bitta shablon */
function visitDocArticle(v) {
  return html`
    <article class="doc">
      ${docHeader()}
      <h2 class="doc__title">${t('doc.title')}</h2>
      <div class="doc__subtitle">${t('doc.subtitle')}</div>
      ${visitDocBody(v)}
      <footer class="doc__foot">
        <div class="doc__foot-row">
          <div><b>${t('doc.doctor')}:</b> ${v.doctor_name || ''}${v.doctor_phone ? ` · ${v.doctor_phone}` : ''}</div>
          <div class="doc__sign">${t('doc.signature')}: ______________</div>
        </div>
      </footer>
    </article>`;
}

/** Word fayl nomi: Фамилия_Исм_ТуғилганЙил (масалан, Абдуллаева_Фарангиз_2022) */
export function visitFileName(v) {
  const [fam, ism] = String(v.patient_name || '').trim().split(/\s+/);
  const year = /^\d{4}/.test(v.birth_date || '') ? v.birth_date.slice(0, 4) : '';
  return [fam, ism, year].filter(Boolean).join(' ') || 'hujjat';
}

export async function printVisit(id, mode = 'print') {
  try {
    const v = await GET(`/api/visits/${id}` + qs({ print: 1 }));
    printDoc(visitDocArticle(v), { name: visitFileName(v), word: mode === 'word' });
  } catch (e) { toast(errorText(e), 'err'); }
}
