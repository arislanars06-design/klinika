// Bosh oyna, Bemorlar tarixi (qidiruv, filtr, eksport) va bemor kartasi.
import {
  html, raw, render, $, $$, t, state, GET, POST, PUT, can, qs, toast, confirmDialog, modal, printDoc, docHeader, errorText, money, fmtDate, fmtDateTime, age,
  genderText, statusBadge, payBadge, pager, setQuery, localDate, addDays, go,
} from '../core.js';
import { patientForm, bindPatientForm, printVisit } from './visit.js';

/* ================= Bosh oyna ================= */
export async function dashboardView(el, query) {
  const date = query.get('date') || localDate();
  const d = await GET('/api/dashboard' + qs({ date }));
  const isToday = date === localDate();
  const mine = can('visit.clinical.write') ? d.visits.filter((v) => v.doctor_id === state.user.id && v.status === 'open') : [];

  const visitLink = (v) => {
    if (can('visit.clinical.read') || can('visit.create')) return `#/visit/${v.id}`;
    if (can('billing.write')) return `#/cash/new?patient=${v.patient_id}&visit=${v.id}`;
    return `#/patient/${v.patient_id}`;
  };

  render(el, html`
    <div class="page-head">
      <h1>${t('nav.dashboard')}</h1>
      <label class="inline">${t('date')}: <input type="date" id="dash-date" value="${date}"></label>
    </div>
    <div class="stats">
      <div class="stat"><div class="stat__label">${isToday ? t('dash.today_patients') : t('dash.patients_on')}</div>
        <div class="stat__value">${d.visits_count}</div><div class="muted small">${t('dash.patients_note')}</div></div>
      ${d.revenue !== undefined ? html`<div class="stat"><div class="stat__label">${isToday ? t('dash.today_revenue') : t('dash.revenue_on')}</div>
        <div class="stat__value">${money(d.revenue)}</div><div class="muted small">${t('dash.revenue_note')}</div></div>` : ''}
      ${can('visit.clinical.write') ? html`<div class="stat"><div class="stat__label">${t('dash.my_queue')}</div><div class="stat__value">${mine.length}</div></div>` : ''}
    </div>
    <section class="card">
      <h2>${t('dash.visits_list')}</h2>
      ${d.visits.length ? html`
        <table class="table">
          <thead><tr><th>${t('time')}</th><th>${t('f.full_name')}</th><th>${t('f.doctor_id')}</th><th>${t('status')}</th></tr></thead>
          <tbody>${d.visits.map((v) => html`
            <tr class="${v.doctor_id === state.user.id && v.status === 'open' ? 'row--mine' : ''}">
              <td>${v.visit_at.slice(11, 16)}</td>
              <td><a href="${visitLink(v)}">${v.patient_name}</a> <span class="muted small">${v.patient_code}</span></td>
              <td>${v.doctor_name || '—'}</td>
              <td>${statusBadge(v.status)}</td>
            </tr>`)}</tbody>
        </table>` : html`<p class="muted">${t('empty')}</p>`}
    </section>`);
  $('#dash-date', el).onchange = (e) => go('/' + qs({ date: e.target.value }));
}

/* ================= Bemorlar tarixi ================= */
const PERIODS = ['today', '7', '30', '365', 'all', 'custom'];

function periodRange(period, from, to) {
  const today = localDate();
  if (period === 'today') return { from: today, to: today };
  if (['7', '30', '365'].includes(period)) return { from: addDays(today, -(Number(period) - 1)), to: today };
  if (period === 'custom') return { from, to };
  return { from: '', to: '' };
}

export async function historyView(el, query) {
  const tab = query.get('tab') === 'patients' ? 'patients' : 'visits';
  const f = {
    tab, q: query.get('q') || '', period: PERIODS.includes(query.get('period')) ? query.get('period') : '30',
    from: query.get('from') || '', to: query.get('to') || '', status: query.get('status') || '',
    doctor: query.get('doctor') || '', page: Number(query.get('page')) || 1,
  };
  const doctors = await GET('/api/doctors');

  render(el, html`
    <div class="page-head"><h1>${t('nav.history')}</h1></div>
    <div class="tabs">
      <a class="tab ${tab === 'visits' ? 'tab--active' : ''}" href="#/history">${t('hist.visits')}</a>
      <a class="tab ${tab === 'patients' ? 'tab--active' : ''}" href="#/history?tab=patients">${t('hist.patients')}</a>
    </div>
    <form class="filters card" id="filters">
      <input type="search" name="q" value="${f.q}" placeholder="${tab === 'visits' && can('visit.clinical.read') ? t('hist.search_ph_dx') : t('hist.search_ph')}" class="field--grow">
      ${tab === 'visits' ? html`
        <select name="period">${PERIODS.map((p) => html`<option value="${p}" ${f.period === p ? raw('selected') : ''}>${t('period.' + p)}</option>`)}</select>
        <span class="custom-range ${f.period === 'custom' ? '' : 'hidden'}">
          <input type="date" name="from" value="${f.from}"> — <input type="date" name="to" value="${f.to}"></span>
        <select name="status">
          ${['', 'open', 'done', 'cancelled', 'all'].map((s) => html`<option value="${s}" ${f.status === s ? raw('selected') : ''}>${t('hist.status_' + (s || 'active'))}</option>`)}
        </select>
        <select name="doctor"><option value="">${t('hist.all_doctors')}</option>
          ${doctors.map((d) => html`<option value="${d.id}" ${String(d.id) === f.doctor ? raw('selected') : ''}>${d.full_name}</option>`)}</select>` : ''}
      <button class="btn">${t('search')}</button>
      ${tab === 'visits' && can('export') ? html`<a class="btn btn--ghost" id="csv" href="#">CSV</a>` : ''}
    </form>
    <section class="card" id="results"><p class="muted">${t('loading')}</p></section>`);

  const form = $('#filters', el);
  const readForm = () => {
    const o = { ...f, q: form.elements.q.value.trim(), page: 1 };
    if (tab === 'visits') {
      Object.assign(o, { period: form.elements.period.value, from: form.elements.from.value, to: form.elements.to.value,
        status: form.elements.status.value, doctor: form.elements.doctor.value });
    }
    return o;
  };
  if (tab === 'visits') {
    form.elements.period.onchange = () => $('.custom-range', form).classList.toggle('hidden', form.elements.period.value !== 'custom');
  }
  const urlParams = (o) => (tab === 'visits'
    ? { q: o.q, period: o.period, from: o.period === 'custom' ? o.from : '', to: o.period === 'custom' ? o.to : '', status: o.status, doctor: o.doctor, page: o.page > 1 ? o.page : '' }
    : { tab: 'patients', q: o.q, page: o.page > 1 ? o.page : '' });

  const load = async (o) => {
    setQuery('/history', urlParams(o));
    const box = $('#results', el);
    try {
      if (tab === 'patients') {
        const d = await GET('/api/patients' + qs({ q: o.q, page: o.page }));
        render(box, d.rows.length ? html`
          <table class="table"><thead><tr><th>ID</th><th>${t('f.full_name')}</th><th>${t('f.birth_date')}</th><th>${t('f.phone')}</th>
            <th>${t('hist.visits_count')}</th><th>${t('patient.last_visit')}</th><th></th></tr></thead>
          <tbody>${d.rows.map((p) => html`<tr><td>${p.code}</td><td><a href="#/patient/${p.id}">${p.full_name}</a></td>
            <td>${fmtDate(p.birth_date)}</td><td>${p.phone}</td><td>${p.visits_count}</td><td>${fmtDate(p.last_visit)}</td>
            <td class="row-actions">
              ${can('patient.write') ? html`<button type="button" class="btn btn--ghost btn--sm" data-p-edit="${p.id}">${t('edit')}</button>` : ''}
              <button type="button" class="btn btn--ghost btn--sm" data-p-print="${p.id}">${t('print')}</button>
              ${can('admin') ? html`<button type="button" class="btn btn--danger btn--sm" data-p-del="${p.id}">${t('delete')}</button>` : ''}
            </td></tr>`)}</tbody></table>`
          : html`<p class="muted">${t('empty')}</p>`);
        box.appendChild(pager(d, (pg) => load({ ...o, page: pg })));
        bindPatientActions(box, d.rows, () => load(o));
        return;
      }
      const r = periodRange(o.period, o.from, o.to);
      const params = { q: o.q, from: r.from, to: r.to, status: o.status, doctor: o.doctor };
      const csv = $('#csv', el);
      if (csv) csv.href = '/api/visits/export.csv' + qs({ ...params, lang: state.lang });
      const d = await GET('/api/visits' + qs({ ...params, page: o.page }));
      const clinical = can('visit.clinical.read');
      render(box, d.rows.length ? html`
        <table class="table"><thead><tr><th>${t('date')}</th><th>ID</th><th>${t('f.full_name')}</th><th>${t('f.phone')}</th>
          <th>${t('f.doctor_id')}</th>${clinical ? html`<th>${t('f.diagnosis_main')}</th>` : ''}<th>${t('status')}</th><th></th></tr></thead>
        <tbody>${d.rows.map((v) => html`<tr>
          <td><a href="#/visit/${v.id}">${fmtDateTime(v.visit_at)}</a></td><td>${v.patient_code}</td>
          <td><a href="#/patient/${v.patient_id}">${v.patient_name}</a></td><td>${v.patient_phone}</td><td>${v.doctor_name || '—'}</td>
          ${clinical ? html`<td>${v.diagnosis_main}</td>` : ''}<td>${statusBadge(v.status)}</td>
          <td class="row-actions">
            <a class="btn btn--ghost btn--sm" href="#/visit/${v.id}">${t('edit')}</a>
            ${clinical ? html`<button type="button" class="btn btn--ghost btn--sm" data-v-print="${v.id}">${t('print')}</button>` : ''}
            ${can('visit.cancel') && v.status !== 'cancelled' ? html`<button type="button" class="btn btn--danger btn--sm" data-v-del="${v.id}">${t('delete')}</button>` : ''}
          </td></tr>`)}</tbody></table>`
        : html`<p class="muted">${t('empty')}</p>`);
      box.appendChild(pager(d, (pg) => load({ ...o, page: pg })));
      $$('[data-v-print]', box).forEach((b) => { b.onclick = () => printVisit(Number(b.dataset.vPrint)); });
      $$('[data-v-del]', box).forEach((b) => {
        b.onclick = async () => {
          const reason = await confirmDialog(t('hist.delete_visit_confirm'), { input: true, danger: true, okText: t('delete') });
          if (!reason) return;
          try { await POST(`/api/visits/${b.dataset.vDel}/cancel`, { reason }); toast(t('hist.deleted')); load(o); } catch (e) { toast(errorText(e), 'err'); }
        };
      });
    } catch (e) { render(box, html`<p class="alert alert--err">${errorText(e)}</p>`); }
  };
  form.onsubmit = (e) => { e.preventDefault(); load(readForm()); };
  load(f);
}

/* ---------- Bemorlar ro'yxatidagi amallar: tahrirlash, chop etish, o'chirish (arxivlash) ---------- */
function bindPatientActions(box, rows, reload) {
  $$('[data-p-edit]', box).forEach((b) => {
    b.onclick = () => {
      const p = rows.find((x) => x.id === Number(b.dataset.pEdit));
      modal(html`<div class="dialog__body"><div class="card-head"><h2>${p.full_name}</h2>
        <button type="button" class="btn btn--ghost btn--sm" data-close>×</button></div>${patientForm(p)}</div>`, (dlg, close) => {
        bindPatientForm($('form.patient-form', dlg), p.id, () => { close(); reload(); });
      });
    };
  });
  $$('[data-p-print]', box).forEach((b) => { b.onclick = () => printPatientCard(Number(b.dataset.pPrint)); });
  $$('[data-p-del]', box).forEach((b) => {
    b.onclick = async () => {
      const p = rows.find((x) => x.id === Number(b.dataset.pDel));
      if (!(await confirmDialog(t('hist.delete_patient_confirm', { name: p.full_name }), { danger: true, okText: t('delete') }))) return;
      try {
        await PUT(`/api/patients/${p.id}`, { full_name: p.full_name, birth_date: p.birth_date, gender: p.gender, phone: p.phone, address: p.address, archived: true });
        toast(t('hist.deleted'));
        reload();
      } catch (e) { toast(errorText(e), 'err'); }
    };
  });
}

/** Bemor kartasi va qabullar ro'yxatini chop etish */
export async function printPatientCard(id) {
  try {
    const d = await GET(`/api/patients/${id}`);
    const p = d.patient;
    const clinical = can('visit.clinical.read');
    printDoc(html`<article class="doc">${docHeader()}
      <h2 class="doc__title">${t('patient.card')}</h2>
      <div class="doc__block doc__patient">
        <div><b>${t('f.full_name')}:</b> ${p.full_name} <span class="muted">(${p.code})</span></div>
        <div><b>${t('f.birth_date')}:</b> ${fmtDate(p.birth_date) || '—'}${p.birth_date ? ` (${age(p.birth_date)} ${t('years')})` : ''}
          ${p.gender ? html` &nbsp; <b>${t('f.gender')}:</b> ${genderText(p.gender)}` : ''}</div>
        ${p.phone ? html`<div><b>${t('f.phone')}:</b> ${p.phone}</div>` : ''}
        ${p.address ? html`<div><b>${t('f.address')}:</b> ${p.address}</div>` : ''}
      </div>
      <div class="doc__block"><h3>${t('hist.visits')} (${d.visits.length})</h3>
        ${d.visits.length ? html`<table class="doc__table"><thead><tr><th>${t('date')}</th><th>${t('f.doctor_id')}</th>
          ${clinical ? html`<th>${t('f.diagnosis_main')}</th>` : ''}<th>${t('status')}</th></tr></thead>
          <tbody>${d.visits.map((v) => html`<tr><td>${fmtDateTime(v.visit_at)}</td><td>${v.doctor_name || ''}</td>
          ${clinical ? html`<td>${v.diagnosis_main}</td>` : ''}<td>${t('status.' + v.status)}</td></tr>`)}</tbody></table>` : html`<p>—</p>`}
      </div>
      <div class="muted small">${t('doc.printed')}: ${fmtDate(localDate())} ${new Date().toTimeString().slice(0, 5)}</div>
    </article>`);
  } catch (e) { toast(errorText(e), 'err'); }
}

/* ================= Bemor kartasi ================= */
export async function patientView(el, id) {
  const d = await GET(`/api/patients/${id}`);
  const p = d.patient;
  const clinical = can('visit.clinical.read');

  render(el, html`
    <div class="page-head">
      <h1>${p.full_name} <span class="muted">${p.code}</span></h1>
      <div class="actions">
        ${can('visit.create') && !p.archived ? html`<a class="btn" href="#/visit/new?patient=${p.id}">+ ${t('dash.new_visit')}</a>` : ''}
        ${can('billing.write') ? html`<a class="btn btn--ghost" href="#/cash/new?patient=${p.id}">${t('cash.create')}</a>` : ''}
      </div>
    </div>
    ${p.archived ? html`<div class="alert alert--warn">${t('patient.archived')}</div>` : ''}
    <div class="grid2">
      <section class="card">
        <h2>${t('patient.card')}</h2>
        <dl class="dl">
          <dt>${t('f.birth_date')}</dt><dd>${fmtDate(p.birth_date) || '—'} ${p.birth_date ? `(${age(p.birth_date)} ${t('years')})` : ''}</dd>
          <dt>${t('f.gender')}</dt><dd>${genderText(p.gender) || '—'}</dd>
          <dt>${t('f.phone')}</dt><dd>${p.phone || '—'}</dd>
          <dt>${t('f.address')}</dt><dd>${p.address || '—'}</dd>
          <dt>${t('patient.registered')}</dt><dd>${fmtDateTime(p.created_at)}</dd>
        </dl>
        ${can('patient.write') ? html`<details class="edit"><summary class="btn btn--ghost btn--sm">${t('edit')}</summary>${patientForm(p)}
          ${can('admin') ? html`<label class="inline"><input type="checkbox" id="archive" ${p.archived ? raw('checked') : ''}> ${t('patient.archive')}</label>` : ''}
          </details>` : ''}
      </section>
      <section class="card">
        <h2>${t('hist.visits')} (${d.visits.length})</h2>
        ${d.visits.length ? html`<table class="table"><thead><tr><th>${t('date')}</th><th>${t('f.doctor_id')}</th>
          ${clinical ? html`<th>${t('f.diagnosis_main')}</th>` : ''}<th>${t('status')}</th></tr></thead>
          <tbody>${d.visits.map((v) => html`<tr><td><a href="#/visit/${v.id}">${fmtDateTime(v.visit_at)}</a></td><td>${v.doctor_name || '—'}</td>
          ${clinical ? html`<td>${v.diagnosis_main}</td>` : ''}<td>${statusBadge(v.status)}</td></tr>`)}</tbody></table>`
          : html`<p class="muted">${t('empty')}</p>`}
      </section>
    </div>
    ${d.invoices ? html`<section class="card">
      <h2>${t('cash.invoices')} (${d.invoices.length})</h2>
      ${d.invoices.length ? invoiceTable(d.invoices) : html`<p class="muted">${t('empty')}</p>`}
    </section>` : ''}`);

  const f = $('form.patient-form', el);
  if (f) {
    const arch = $('#archive', el);
    bindPatientForm(f, p.id, () => patientView(el, id));
    if (arch) {
      arch.onchange = async () => {
        try {
          await PUT(`/api/patients/${p.id}`, { ...p, archived: arch.checked });
          toast(t('saved'));
          patientView(el, id);
        } catch (e) { toast(errorText(e), 'err'); }
      };
    }
  }
}

export function invoiceTable(rows) {
  return html`<table class="table"><thead><tr><th>№</th><th>${t('date')}</th><th>${t('f.full_name')}</th><th class="num">${t('cash.total')}</th>
    <th class="num">${t('cash.paid')}</th><th class="num">${t('cash.debt')}</th><th>${t('status')}</th></tr></thead>
    <tbody>${rows.map((i) => html`<tr><td><a href="#/cash/invoice/${i.id}">${i.number}</a></td><td>${fmtDateTime(i.created_at)}</td>
      <td>${i.patient_name}</td><td class="num">${money(i.total)}</td><td class="num">${money(i.paid)}</td>
      <td class="num">${i.debt ? money(i.debt) : '—'}</td><td>${payBadge(i.pay_status)}</td></tr>`)}</tbody></table>`;
}
