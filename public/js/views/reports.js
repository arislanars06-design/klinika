// Statistika: qabullar — «Беморлар тарихи → Статистика», moliya — «Касса → Статистика».
import { html, raw, render, $, t, state, GET, qs, money, fmtDate, fmtDateTime, localDate, addDays, go, setQuery, can, busy, printDoc, docHeader } from '../core.js';

const KINDS = {
  visits: {
    path: '/history/stats', title: 'nav.history', perm: 'report.visits', doc: 'rep.visits', folder: 'history',
    tabs: () => [['#/history', 'hist.visits'], ['#/history?tab=patients', 'hist.patients'], ['#/history/stats', 'stats']],
  },
  finance: {
    path: '/cash/stats', title: 'nav.cash', perm: 'report.finance', doc: 'rep.finance', folder: 'cash',
    tabs: () => [['#/cash', 'cash.invoices'], ['#/cash/stats', 'stats']],
  },
};

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

/** kind: 'visits' | 'finance' */
export async function statsView(el, query, kind) {
  const K = KINDS[kind];
  const preset = PRESETS.includes(query.get('p')) ? query.get('p') : 'month';
  const [from, to] = range(preset, query.get('from'), query.get('to'));
  const d = await GET('/api/reports' + qs({ from, to, part: kind }));
  const periodLabel = (r) => (d.group === 'month' ? r.period.split('-').reverse().join('.') : fmtDate(r.period));
  const V = d.visits;
  const F = d.finance;

  render(el, html`
    <div class="page-head"><h1>${t(K.title)}</h1><span class="muted">${fmtDate(from)} — ${fmtDate(to)}</span></div>
    <div class="tabs">${K.tabs().map(([href, key]) => html`<a class="tab ${key === 'stats' ? 'tab--active' : ''}" href="${href}">${t(key)}</a>`)}</div>
    <form class="filters card" id="f">
      <select name="p">${PRESETS.map((p) => html`<option value="${p}" ${p === preset ? raw('selected') : ''}>${t('rep.' + p)}</option>`)}</select>
      <span class="custom-range ${preset === 'custom' ? '' : 'hidden'}"><input type="date" name="from" value="${from}"> — <input type="date" name="to" value="${to}"></span>
      <button class="btn">${t('show')}</button>
      <button type="button" class="btn btn--ghost" id="stats-word">${t('rep.download_word')}</button>
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
    go(K.path + qs(p === 'custom' ? { p, from: f.elements.from.value, to: f.elements.to.value } : { p }));
  };
  setQuery(K.path, preset === 'custom' ? { p: preset, from, to } : { p: preset });
  $('#stats-word', el).onclick = (e) => busy(e.target, () => statsWord(K, d, from, to, periodLabel));
}

/** Ro'yxat jadvali; cols: [{ h, w (%), num }] — w Word'da ustun kengligi */
function listTable(title, cols, rows, foot) {
  const cls = (c) => (c.num ? 'num' : '');
  return html`<div class="doc__block"><h3>${title}</h3>${rows.length ? html`<table class="doc__table">
    <thead><tr>${cols.map((c) => html`<th class="${cls(c)}" data-w="${c.w || ''}">${c.h}</th>`)}</tr></thead>
    <tbody>${rows.map((r) => html`<tr>${r.map((v, i) => html`<td class="${cls(cols[i])}">${v}</td>`)}</tr>`)}
      ${foot ? html`<tr>${foot.map((v, i) => html`<td class="${cls(cols[i])}"><b>${v}</b></td>`)}</tr>` : ''}</tbody></table>`
    : html`<p>${t('empty')}</p>`}</div>`;
}

/** Statistikani Word (A4) fayliga: avval bemorlar ro'yxati, keyin ko'rsatkichlar va bo'limlar bo'yicha jadvallar */
async function statsWord(K, d, from, to, periodLabel) {
  const V = d.visits;
  const F = d.finance;
  const kv = (rows) => html`<table class="doc__table"><thead><tr><th>${t('rep.indicator')}</th><th class="num">${t('rep.value')}</th></tr></thead>
    <tbody>${rows.map(([k, v]) => html`<tr><td>${k}</td><td class="num">${v}</td></tr>`)}</tbody></table>`;
  const tbl = (title, head, rows) => html`<div class="doc__block"><h3>${title}</h3>${rows.length
    ? html`<table class="doc__table"><thead><tr>${head.map((h, i) => html`<th class="${i ? 'num' : ''}">${h}</th>`)}</tr></thead>
      <tbody>${rows.map((r) => html`<tr>${r.map((c, i) => html`<td class="${i ? 'num' : ''}">${c}</td>`)}</tr>`)}</tbody></table>`
    : html`<p>${t('empty')}</p>`}</div>`;
  const byPeriod = d.group === 'month' ? t('rep.by_month') : t('rep.by_day');
  let body;
  if (V) {
    body = html`
      ${await visitsList(from, to)}
      <div class="doc__block">${kv([[t('rep.visits_total'), V.total], [t('rep.cancelled'), V.cancelled], [t('rep.patients'), V.patients],
        [t('rep.new'), V.new_patients], [t('rep.returning'), V.returning_patients]])}</div>
      ${tbl(byPeriod, [t('rep.period_col'), t('rep.visits_total')], V.by_period.map((r) => [periodLabel(r), r.count]))}
      ${tbl(t('rep.by_doctor'), [t('doc.doctor'), t('rep.visits_total')], V.by_doctor.map((r) => [r.doctor, r.count]))}
      ${tbl(t('rep.by_diagnosis'), [t('f.diagnosis_main'), t('rep.visits_total'), t('rep.patients')], V.by_diagnosis.map((r) => [r.diagnosis, r.count, r.patients]))}`;
  } else {
    body = html`
      ${await invoicesList(from, to)}
      <div class="doc__block">${kv([[t('cash.net'), money(F.net)], [t('cash.income'), money(F.income)], [t('cash.refunds'), money(F.refunds)],
        [t('rep.invoiced'), money(F.invoices_total)], [t('cash.invoices'), F.invoices_count], [t('cash.discount'), money(F.discounts)],
        [t('rep.debts'), money(F.debt_sum)], [t('rep.debt_invoices'), F.debt_count]])}</div>
      ${tbl(t('cash.by_method'), [t('cash.method'), t('cash.net')], Object.entries(F.by_method).map(([m, v]) => [t('method.' + m), money(v.net)]))}
      ${tbl(byPeriod, [t('rep.period_col'), t('cash.net')], F.by_period.map((r) => [periodLabel(r), money(r.net)]))}
      ${tbl(t('rep.services'), [t('cash.service'), t('cash.qty'), t('cash.amount')], F.services.map((s) => [s.name, s.qty, money(s.amount)]))}`;
  }
  const period = `${fmtDate(from)} — ${fmtDate(to)}`;
  return printDoc(html`<article class="doc">${docHeader()}
    <h2 class="doc__title">${t(K.doc)}</h2>
    <div class="doc__subtitle">${t('rep.period')}: ${period}</div>
    ${body}
    <footer class="doc__foot"><div class="doc__foot-row">
      <div><b>${t('rep.prepared')}:</b> ${state.user.full_name}</div>
      <div class="doc__sign">${t('doc.signature')}: ______________</div></div></footer>
  </article>`, { word: true, page: 'a4', folder: K.folder, name: `${t(K.doc)} ${fmtDate(from)}-${fmtDate(to)}` });
}

/** Беморлар рўйхати (қабуллар бўйича): № | Сана | Ф.И.Ш. | Туғилган сана | Ташхис | Шифокор */
async function visitsList(from, to) {
  const d = await GET('/api/visits' + qs({ all: 1, from, to }));
  const rows = [...d.rows].sort((a, b) => a.visit_at.localeCompare(b.visit_at) || a.id - b.id)
    .map((v, i) => [i + 1, fmtDateTime(v.visit_at), v.patient_name, fmtDate(v.birth_date) || '—', v.diagnosis_main || '—', v.doctor_name || '']);
  return listTable(t('rep.patient_list'), [
    { h: '№', w: 5 }, { h: t('date'), w: 14 }, { h: t('f.full_name'), w: 25 }, { h: t('f.birth_date'), w: 12 },
    { h: t('f.diagnosis_main') }, { h: t('doc.doctor'), w: 16 },
  ], rows);
}

/** Беморлар рўйхати хизматлар билан (ҳисоблар бўйича): № | Сана | Ф.И.Ш. | Хизматлар | Жами | Тўланган | Қарз */
async function invoicesList(from, to) {
  const d = await GET('/api/invoices' + qs({ all: 1, from, to }));
  const list = [...d.rows].sort((a, b) => a.created_at.localeCompare(b.created_at) || a.id - b.id);
  const sum = (k) => list.reduce((a, r) => a + (r[k] || 0), 0);
  const rows = list.map((r, i) => [i + 1, fmtDateTime(r.created_at), r.patient_name, r.services || '—', money(r.total), money(r.paid), r.debt ? money(r.debt) : '—']);
  return listTable(t('rep.patient_services'), [
    { h: '№', w: 5 }, { h: t('date'), w: 13 }, { h: t('f.full_name'), w: 20 }, { h: t('rep.services_col') },
    { h: t('cash.total'), w: 11, num: true }, { h: t('cash.paid'), w: 11, num: true }, { h: t('cash.debt'), w: 10, num: true },
  ], rows, list.length ? ['', '', t('total'), '', money(sum('total')), money(sum('paid')), money(sum('debt'))] : null);
}

/** Eski «Ҳисоботлар» havolasi: mos statistika sahifasiga o'tkazadi */
export function reportsRedirect() {
  go(can('report.visits') ? '/history/stats' : '/cash/stats');
}
