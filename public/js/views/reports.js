// Hisobotlar: qabul statistikasi va moliyaviy statistika alohida.
import { html, raw, render, $, t, GET, qs, money, fmtDate, localDate, addDays, go, setQuery } from '../core.js';

const PRESETS = ['today', '7', 'month', '30', '365', 'custom'];

function range(preset, from, to) {
  const today = localDate();
  if (preset === 'today') return [today, today];
  if (preset === '7') return [addDays(today, -6), today];
  if (preset === '30') return [addDays(today, -29), today];
  if (preset === '365') return [addDays(today, -364), today];
  if (preset === 'custom' && from && to) return [from, to];
  return [today.slice(0, 8) + '01', today];
}

function bars(rows, key, fmt, labelFmt) {
  const max = Math.max(1, ...rows.map((r) => r[key]));
  return html`<div class="bars">${rows.map((r) => html`
    <div class="bars__row"><span class="bars__label">${labelFmt(r)}</span>
      <span class="bars__track"><span class="bars__fill" data-w="${Math.max(1, Math.round((r[key] / max) * 100))}"></span></span>
      <span class="bars__val">${fmt(r[key])}</span></div>`)}</div>`;
}

export async function reportsView(el, query) {
  const preset = PRESETS.includes(query.get('p')) ? query.get('p') : 'month';
  const [from, to] = range(preset, query.get('from'), query.get('to'));
  const d = await GET('/api/reports' + qs({ from, to }));
  const periodLabel = (r) => (d.group === 'month' ? r.period.split('-').reverse().join('.') : fmtDate(r.period));
  const V = d.visits;
  const F = d.finance;

  render(el, html`
    <div class="page-head"><h1>${t('nav.reports')}</h1><span class="muted">${fmtDate(from)} — ${fmtDate(to)}</span></div>
    <form class="filters card" id="f">
      <select name="p">${PRESETS.map((p) => html`<option value="${p}" ${p === preset ? raw('selected') : ''}>${t('rep.' + p)}</option>`)}</select>
      <span class="custom-range ${preset === 'custom' ? '' : 'hidden'}"><input type="date" name="from" value="${from}"> — <input type="date" name="to" value="${to}"></span>
      <button class="btn">${t('show')}</button>
    </form>

    ${V ? html`
      <h2 class="section-title">${t('rep.visits')}</h2>
      <div class="stats">
        <div class="stat"><div class="stat__label">${t('rep.visits_total')}</div><div class="stat__value">${V.total}</div>
          <div class="muted small">${t('rep.cancelled')}: ${V.cancelled}</div></div>
        <div class="stat"><div class="stat__label">${t('rep.patients')}</div><div class="stat__value">${V.patients}</div></div>
        <div class="stat"><div class="stat__label">${t('rep.new')}</div><div class="stat__value">${V.new_patients}</div></div>
        <div class="stat"><div class="stat__label">${t('rep.returning')}</div><div class="stat__value">${V.returning_patients}</div></div>
      </div>
      <div class="grid2">
        <section class="card"><h3>${d.group === 'month' ? t('rep.by_month') : t('rep.by_day')}</h3>
          ${V.by_period.length ? bars(V.by_period, 'count', String, periodLabel) : html`<p class="muted">${t('empty')}</p>`}</section>
        <section class="card"><h3>${t('rep.by_doctor')}</h3>
          ${V.by_doctor.length ? bars(V.by_doctor, 'count', String, (r) => r.doctor) : html`<p class="muted">${t('empty')}</p>`}</section>
      </div>
      <section class="card"><h3>${t('rep.by_diagnosis')}</h3>
        ${V.by_diagnosis.length ? html`<table class="table"><thead><tr><th>${t('f.diagnosis_main')}</th><th class="num">${t('rep.visits_total')}</th>
          <th class="num">${t('rep.patients')}</th></tr></thead><tbody>${V.by_diagnosis.map((r) => html`<tr><td>${r.diagnosis}</td>
          <td class="num">${r.count}</td><td class="num">${r.patients}</td></tr>`)}</tbody></table>` : html`<p class="muted">${t('empty')}</p>`}
      </section>` : ''}

    ${F ? html`
      <h2 class="section-title">${t('rep.finance')}</h2>
      <p class="hint">${t('rep.finance_note')}</p>
      <div class="stats">
        <div class="stat"><div class="stat__label">${t('cash.net')}</div><div class="stat__value">${money(F.net)}</div>
          <div class="muted small">${t('cash.income')}: ${money(F.income)} · ${t('cash.refunds')}: ${money(F.refunds)}</div></div>
        <div class="stat"><div class="stat__label">${t('rep.invoiced')}</div><div class="stat__value">${money(F.invoices_total)}</div>
          <div class="muted small">${t('cash.invoices')}: ${F.invoices_count} · ${t('cash.discount')}: ${money(F.discounts)}</div></div>
        <div class="stat"><div class="stat__label">${t('rep.debts')}</div><div class="stat__value">${money(F.debt_sum)}</div>
          <div class="muted small">${t('rep.debt_count', { n: F.debt_count, p: F.debt_partial })}</div></div>
      </div>
      <div class="grid2">
        <section class="card"><h3>${t('cash.by_method')}</h3>
          ${Object.keys(F.by_method).length ? html`<table class="table"><tbody>${Object.entries(F.by_method).map(([m, v]) => html`
            <tr><td>${t('method.' + m)}</td><td class="num">${money(v.net)}</td></tr>`)}</tbody></table>` : html`<p class="muted">${t('empty')}</p>`}</section>
        <section class="card"><h3>${d.group === 'month' ? t('rep.by_month') : t('rep.by_day')}</h3>
          ${F.by_period.length ? bars(F.by_period, 'net', money, periodLabel) : html`<p class="muted">${t('empty')}</p>`}</section>
      </div>
      <section class="card"><h3>${t('rep.services')}</h3>
        ${F.services.length ? html`<table class="table"><thead><tr><th>${t('cash.service')}</th><th class="num">${t('cash.qty')}</th>
          <th class="num">${t('cash.amount')}</th></tr></thead><tbody>${F.services.map((s) => html`<tr><td>${s.name}</td>
          <td class="num">${s.qty}</td><td class="num">${money(s.amount)}</td></tr>`)}</tbody></table>` : html`<p class="muted">${t('empty')}</p>`}
      </section>` : ''}`);

  const f = $('#f', el);
  f.elements.p.onchange = () => $('.custom-range', f).classList.toggle('hidden', f.elements.p.value !== 'custom');
  f.onsubmit = (e) => {
    e.preventDefault();
    const p = f.elements.p.value;
    go('/reports' + qs(p === 'custom' ? { p, from: f.elements.from.value, to: f.elements.to.value } : { p }));
  };
  setQuery('/reports', preset === 'custom' ? { p: preset, from, to } : { p: preset });
}
