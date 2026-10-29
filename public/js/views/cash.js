// Kassa: hisoblar, yangi hisob (xizmatlar × miqdor), to'lov, qaytarish, bekor qilish, chek va kunlik hisobot.
import {
  html, raw, render, $, $$, t, GET, POST, qs, can, go, toast, errorText, busy, confirmDialog, money, fmtDate,
  fmtDateTime, payBadge, pager, setQuery, localDate, patientPicker, printDoc, docHeader, METHODS, refresh, modal,
} from '../core.js';
import { invoiceTable } from './main-views.js';

function cashTabs(active) {
  return html`<div class="tabs">
    <a class="tab ${active === 'list' ? 'tab--active' : ''}" href="#/cash">${t('cash.invoices')}</a>
    <a class="tab ${active === 'daily' ? 'tab--active' : ''}" href="#/cash/daily">${t('cash.daily')}</a>
  </div>`;
}

const methodOptions = (sel) => METHODS.map((m) => html`<option value="${m}" ${m === sel ? raw('selected') : ''}>${t('method.' + m)}</option>`);
const toInt = (v) => { const n = Number(String(v).replace(/\s/g, '')); return Number.isFinite(n) ? Math.round(n) : NaN; };

/* ================= Hisoblar ro'yxati ================= */
export async function cashListView(el, query) {
  const f = { date: query.get('date') ?? localDate(), q: query.get('q') || '', debt: query.get('debt') === '1', page: Number(query.get('page')) || 1 };
  render(el, html`
    <div class="page-head"><h1>${t('nav.cash')}</h1>
      ${can('billing.write') ? html`<button type="button" class="btn" id="create-inv">+ ${t('cash.create')}</button>` : ''}</div>
    ${cashTabs('list')}
    <form class="filters card" id="f">
      <label class="inline">${t('date')}: <input type="date" name="date" value="${f.date}"></label>
      <input type="search" name="q" value="${f.q}" placeholder="${t('cash.search_ph')}" class="field--grow">
      <label class="inline"><input type="checkbox" name="debt" ${f.debt ? raw('checked') : ''}> ${t('cash.only_debt')}</label>
      <button class="btn">${t('search')}</button>
    </form>
    <section class="card" id="res"></section>`);
  const form = $('#f', el);
  const load = async (o) => {
    setQuery('/cash', { date: o.date === localDate() ? '' : o.date || 'all', q: o.q, debt: o.debt ? 1 : '', page: o.page > 1 ? o.page : '' });
    const d = await GET('/api/invoices' + qs({ date: o.date, q: o.q, status: o.debt ? 'debt' : '', page: o.page }));
    const box = $('#res', el);
    render(box, d.rows.length ? invoiceTable(d.rows) : html`<p class="muted">${t('empty')}</p>`);
    box.appendChild(pager(d, (pg) => load({ ...o, page: pg })));
  };
  form.onsubmit = (e) => {
    e.preventDefault();
    load({ date: form.elements.date.value, q: form.elements.q.value.trim(), debt: form.elements.debt.checked, page: 1 });
  };
  if (f.date === 'all') f.date = '';
  form.elements.date.value = f.date;
  const cb = $('#create-inv', el);
  if (cb) cb.onclick = () => invoiceDialog({});
  load(f).catch((e) => toast(errorText(e), 'err'));
}

/* ================= Hisob yaratish (oyna) ================= */
// "#/cash/new?patient=..&visit=.." manzili ham shu oynani ochadi (qabul oynasidagi "Касса" tugmasi).
export async function newInvoiceView(el, query) {
  await cashListView(el, new URLSearchParams());
  if (!can('billing.write')) return;
  setQuery('/cash', {});
  invoiceDialog({ patientId: Number(query.get('patient')) || null, visitId: Number(query.get('visit')) || null });
}

/**
 * Ixcham hisob oynasi: bemor F.I.Sh. va tug'ilgan yili, xizmat turi (bir nechta bo'lishi mumkin), jami summa va to'lov.
 * Hisob qabulga bog'lanadi: berilgan qabul yoki bemorning bugungi qabuli.
 */
export async function invoiceDialog({ patientId = null, visitId = null }) {
  let services;
  try { services = await GET('/api/services'); } catch (e) { toast(errorText(e), 'err'); return; }
  let patient = null;
  let linkVisit = null;

  modal(html`
    <form class="dialog__body form" id="invf" autocomplete="off">
      <div class="card-head"><h2>${t('cash.create')}</h2><button type="button" class="btn btn--ghost btn--sm" data-close>×</button></div>
      <div id="inv-pat"></div>
      <div id="inv-body" class="hidden">
        <table class="table items">
          <thead><tr><th>${t('cash.service_type')}</th><th class="num">${t('cash.qty')}</th><th class="num">${t('cash.amount')}</th><th></th></tr></thead>
          <tbody id="items"></tbody>
        </table>
        <button type="button" class="btn btn--ghost btn--sm" id="add">+ ${t('cash.add_service')}</button>
        ${services.length ? '' : html`<p class="alert alert--warn">${t('cash.no_services')}</p>`}
        <dl class="totals"><dt class="totals__big">${t('cash.total')}</dt><dd class="totals__big" id="total"></dd></dl>
        <div class="row">
          <label class="field"><span>${t('cash.pay_amount')}</span><input name="pay_amount" inputmode="numeric" class="num-input"></label>
          <label class="field"><span>${t('cash.method')}</span><select name="method">${methodOptions('cash')}</select></label>
        </div>
        <div class="dialog__actions"><button type="button" class="btn btn--ghost" data-close>${t('cancel')}</button>
          <button type="submit" class="btn">${t('cash.save_invoice')}</button></div>
      </div>
    </form>`, (dlg, close) => {
    const form = $('#invf', dlg);
    const tbody = $('#items', dlg);
    const patBox = $('#inv-pat', dlg);
    let payTouched = false;

    const recalc = () => {
      let total = 0;
      $$('tr.item', tbody).forEach((tr) => {
        const s = services.find((x) => x.id === Number($('select', tr).value));
        const qty = toInt($('[data-k=qty]', tr).value);
        const amount = s && qty >= 1 ? s.price * qty : 0;
        $('[data-k=amount]', tr).textContent = money(amount);
        total += amount;
      });
      $('#total', dlg).textContent = money(total);
      if (!payTouched) form.elements.pay_amount.value = total;
      return total;
    };
    const addRow = () => {
      if (!services.length) return;
      const tr = document.createElement('tr');
      tr.className = 'item';
      render(tr, html`<td><select>${services.map((s) => html`<option value="${s.id}">${s.name} — ${money(s.price)}</option>`)}</select></td>
        <td class="num"><input data-k="qty" class="num-input num-input--sm" type="number" min="1" max="1000" value="1"></td>
        <td class="num" data-k="amount"></td>
        <td><button type="button" class="btn btn--ghost btn--sm" data-del>×</button></td>`);
      tbody.appendChild(tr);
      recalc();
    };
    tbody.addEventListener('input', recalc);
    tbody.addEventListener('change', recalc);
    tbody.addEventListener('click', (e) => { if (e.target.closest('[data-del]')) { e.target.closest('tr').remove(); recalc(); } });
    $('#add', dlg).onclick = addRow;
    form.elements.pay_amount.oninput = () => { payTouched = true; };

    const choose = async (p) => {
      patient = p;
      let visits = [];
      try { visits = (await GET(`/api/patients/${p.id}`)).visits.filter((v) => v.status !== 'cancelled'); } catch { /* ixtiyoriy */ }
      linkVisit = (visitId && visits.find((v) => v.id === visitId)) || visits.find((v) => v.visit_at.slice(0, 10) === localDate()) || null;
      render(patBox, html`
        <div class="grid-fields inv-patient">
          <div class="field field--wide"><span>${t('f.full_name')}</span><b>${p.full_name}</b> <span class="muted small">${p.code}</span></div>
          <div class="field"><span>${t('f.birth_year')}</span><b>${p.birth_date ? p.birth_date.slice(0, 4) : '—'}</b></div>
          <div class="field"><span></span><button type="button" class="btn btn--ghost btn--sm" id="chg">${t('visit.change_patient')}</button></div>
        </div>
        ${linkVisit ? html`<div class="muted small">${t('cash.visit_link')}: ${fmtDateTime(linkVisit.visit_at)}</div>` : ''}`);
      $('#chg', patBox).onclick = () => { patient = null; $('#inv-body', dlg).classList.add('hidden'); showPicker(); };
      $('#inv-body', dlg).classList.remove('hidden');
      if (!tbody.children.length) addRow();
    };
    const showPicker = () => patientPicker(patBox, choose);

    if (patientId) {
      GET(`/api/patients/${patientId}`).then((d) => choose(d.patient)).catch((e) => { toast(errorText(e), 'err'); showPicker(); });
    } else showPicker();

    form.onsubmit = async (e) => {
      e.preventDefault();
      if (!patient) return;
      const total = recalc();
      const items = $$('tr.item', tbody).map((tr) => ({ service_id: Number($('select', tr).value), qty: toInt($('[data-k=qty]', tr).value) }));
      if (!items.length) { toast(t('cash.need_items'), 'err'); return; }
      if (items.some((i) => !(i.qty >= 1))) { toast(t('err.invalid'), 'err'); return; }
      const payAmount = toInt(form.elements.pay_amount.value) || 0;
      if (payAmount > total) { toast(t('err.overpayment'), 'err'); return; }
      await busy(e.submitter, async () => {
        const inv = await POST('/api/invoices', {
          patient_id: patient.id, visit_id: linkVisit ? linkVisit.id : null, items,
          payment: payAmount > 0 ? { amount: payAmount, method: form.elements.method.value } : null,
        });
        toast(t('saved'));
        close();
        go(`/cash/invoice/${inv.id}`);
      });
    };
  });
}

/* ================= Hisob sahifasi ================= */
export async function invoiceView(el, id) {
  const inv = await GET(`/api/invoices/${id}`);
  const active = inv.status !== 'cancelled';
  const w = can('billing.write');
  render(el, html`
    <div class="page-head">
      <h1>${t('cash.invoice')} ${inv.number}</h1>
      <div class="page-head__meta">${payBadge(inv.pay_status)} <span class="muted">${fmtDateTime(inv.created_at)} · ${inv.created_by_name || ''}</span></div>
    </div>
    ${cashTabs('')}
    ${!active ? html`<div class="alert alert--err">${t('cash.cancelled_reason')}: ${inv.cancel_reason}</div>` : ''}
    <div class="grid2">
      <section class="card">
        <div><a href="#/patient/${inv.patient_id}"><b>${inv.patient_name}</b></a> <span class="muted">${inv.patient_code}</span></div>
        ${inv.visit_id ? html`<div class="muted">${t('cash.visit_link')}: ${fmtDateTime(inv.visit_at)}</div>` : ''}
        <table class="table">
          <thead><tr><th>${t('cash.service')}</th><th class="num">${t('cash.price')}</th><th class="num">${t('cash.qty')}</th><th class="num">${t('cash.amount')}</th></tr></thead>
          <tbody>${inv.items.map((i) => html`<tr><td>${i.name}</td><td class="num">${money(i.unit_price)}</td><td class="num">${i.qty}</td><td class="num">${money(i.amount)}</td></tr>`)}</tbody>
        </table>
        <dl class="totals">
          <dt>${t('cash.subtotal')}</dt><dd>${money(inv.subtotal)}</dd>
          ${inv.discount ? html`<dt>${t('cash.discount')}</dt><dd>− ${money(inv.discount)}</dd>` : ''}
          <dt class="totals__big">${t('cash.total')}</dt><dd class="totals__big">${money(inv.total)}</dd>
          <dt>${t('cash.paid')}</dt><dd>${money(inv.paid)}</dd>
          <dt>${t('cash.debt')}</dt><dd class="${inv.debt ? 'text-err' : ''}">${money(inv.debt)}</dd>
        </dl>
        <div class="actions">
          <button class="btn btn--ghost" id="print">${t('cash.print_receipt')}</button>
          ${w && active && inv.paid === 0 ? html`<button class="btn btn--danger" id="cancel">${t('cash.cancel_invoice')}</button>` : ''}
        </div>
      </section>
      <section class="card">
        <h2>${t('cash.payments')}</h2>
        ${inv.payments.length ? html`<table class="table"><thead><tr><th>${t('time')}</th><th>${t('cash.kind')}</th><th>${t('cash.method')}</th>
          <th class="num">${t('cash.amount')}</th><th></th></tr></thead>
          <tbody>${inv.payments.map((p) => html`<tr class="${p.voided ? 'row--voided' : ''}">
            <td>${fmtDateTime(p.paid_at)}<div class="muted small">${p.created_by_name || ''}</div></td>
            <td>${t('kind.' + p.kind)}${p.note ? html`<div class="muted small">${p.note}</div>` : ''}
              ${p.voided ? html`<div class="small text-err">${t('cash.voided')}: ${p.void_reason} (${p.voided_by_name || ''})</div>` : ''}</td>
            <td>${t('method.' + p.method)}</td>
            <td class="num">${p.kind === 'refund' ? '− ' : ''}${money(p.amount)}</td>
            <td>${w && !p.voided ? html`<button class="btn btn--ghost btn--sm" data-void="${p.id}">${t('cash.void')}</button>` : ''}</td>
          </tr>`)}</tbody></table>` : html`<p class="muted">${t('cash.no_payments')}</p>`}
        ${w && active && inv.debt > 0 ? html`
          <form class="form card card--inner" id="pay">
            <h3>${t('cash.add_payment')}</h3>
            <div class="row">
              <label class="field"><span>${t('cash.amount')}</span><input name="amount" class="num-input" inputmode="numeric" value="${inv.debt}" required></label>
              <label class="field"><span>${t('cash.method')}</span><select name="method">${methodOptions('cash')}</select></label>
            </div>
            <label class="field"><span>${t('cash.note')}</span><input name="note" maxlength="300"></label>
            <button class="btn btn--ok">${t('cash.accept_payment')}</button>
          </form>` : ''}
        ${w && active && inv.paid > 0 ? html`
          <details class="card card--inner"><summary>${t('cash.refund')}</summary>
            <form class="form" id="refund">
              <div class="row">
                <label class="field"><span>${t('cash.amount')}</span><input name="amount" class="num-input" inputmode="numeric" required></label>
                <label class="field"><span>${t('cash.method')}</span><select name="method">${methodOptions('cash')}</select></label>
              </div>
              <label class="field"><span>${t('reason')} *</span><input name="note" maxlength="300" required></label>
              <button class="btn btn--danger">${t('cash.do_refund')}</button>
            </form>
          </details>` : ''}
        <p class="hint">${t('cash.bank_hint')}</p>
      </section>
    </div>`);

  $('#print', el).onclick = () => printReceipt(inv);
  const c = $('#cancel', el);
  if (c) c.onclick = async () => {
    const reason = await confirmDialog(t('cash.cancel_confirm'), { input: true, danger: true });
    if (!reason) return;
    try { await POST(`/api/invoices/${inv.id}/cancel`, { reason }); toast(t('saved')); refresh(); } catch (e) { toast(errorText(e), 'err'); }
  };
  el.querySelectorAll('[data-void]').forEach((b) => {
    b.onclick = async () => {
      const reason = await confirmDialog(t('cash.void_confirm'), { input: true, danger: true });
      if (!reason) return;
      try { await POST(`/api/payments/${b.dataset.void}/void`, { reason }); toast(t('saved')); refresh(); } catch (e) { toast(errorText(e), 'err'); }
    };
  });
  const bindPay = (form, kind) => {
    if (!form) return;
    form.onsubmit = async (e) => {
      e.preventDefault();
      const amount = toInt(form.elements.amount.value);
      if (!(amount > 0)) { toast(t('err.invalid'), 'err'); return; }
      if (kind === 'refund' && !(await confirmDialog(t('cash.refund_confirm', { sum: money(amount) }), { danger: true }))) return;
      await busy(e.submitter, async () => {
        await POST(`/api/invoices/${inv.id}/payments`, { kind, amount, method: form.elements.method.value, note: form.elements.note.value.trim() });
        toast(t('saved'));
        refresh();
      });
    };
  };
  bindPay($('#pay', el), 'payment');
  bindPay($('#refund', el), 'refund');
}

function printReceipt(inv) {
  printDoc(html`
    <article class="doc doc--receipt">
      ${docHeader()}
      <h2 class="doc__title">${t('cash.receipt')} ${inv.number}</h2>
      <p>${fmtDateTime(inv.created_at)}<br><b>${t('f.full_name')}:</b> ${inv.patient_name} (${inv.patient_code})</p>
      <table class="doc__table"><thead><tr><th>${t('cash.service')}</th><th class="num">${t('cash.price')}</th><th class="num">${t('cash.qty')}</th><th class="num">${t('cash.amount')}</th></tr></thead>
        <tbody>${inv.items.map((i) => html`<tr><td>${i.name}</td><td class="num">${money(i.unit_price)}</td><td class="num">${i.qty}</td><td class="num">${money(i.amount)}</td></tr>`)}</tbody></table>
      <dl class="totals">
        ${inv.discount ? html`<dt>${t('cash.discount')}</dt><dd>− ${money(inv.discount)}</dd>` : ''}
        <dt><b>${t('cash.total')}</b></dt><dd><b>${money(inv.total)}</b></dd>
        <dt>${t('cash.paid')}</dt><dd>${money(inv.paid)}</dd>
        ${inv.debt ? html`<dt>${t('cash.debt')}</dt><dd>${money(inv.debt)}</dd>` : ''}
      </dl>
      ${inv.payments.filter((p) => !p.voided).map((p) => html`<div class="small">${fmtDateTime(p.paid_at)} · ${t('kind.' + p.kind)} · ${t('method.' + p.method)} · ${money(p.amount)}</div>`)}
      <p class="small muted">${t('cash.receipt_note')}</p>
    </article>`);
}

/* ================= Kunlik kassa hisoboti ================= */
export async function dailyView(el, query) {
  const date = query.get('date') || localDate();
  const d = await GET('/api/cash/daily' + qs({ date }));
  const methodsTable = html`<table class="table"><thead><tr><th>${t('cash.method')}</th><th class="num">${t('cash.income')}</th>
    <th class="num">${t('cash.refunds')}</th><th class="num">${t('cash.net')}</th></tr></thead>
    <tbody>${Object.entries(d.by_method).map(([m, v]) => html`<tr><td>${t('method.' + m)}</td><td class="num">${money(v.income)}</td>
      <td class="num">${money(v.refunds)}</td><td class="num"><b>${money(v.net)}</b></td></tr>`)}
    <tr class="row--total"><td>${t('total')}</td><td class="num">${money(d.income)}</td><td class="num">${money(d.refunds)}</td><td class="num">${money(d.net)}</td></tr></tbody></table>`;
  const list = html`<table class="table"><thead><tr><th>${t('time')}</th><th>№</th><th>${t('f.full_name')}</th><th>${t('cash.kind')}</th>
    <th>${t('cash.method')}</th><th class="num">${t('cash.amount')}</th><th>${t('cash.cashier')}</th></tr></thead>
    <tbody>${d.payments.map((p) => html`<tr class="${p.voided ? 'row--voided' : ''}"><td>${p.paid_at.slice(11, 16)}</td>
      <td><a href="#/cash/invoice/${p.invoice_id}">${p.invoice_number}</a></td><td>${p.patient_name}</td>
      <td>${t('kind.' + p.kind)}${p.voided ? html` <span class="text-err small">(${t('cash.voided')})</span>` : ''}</td>
      <td>${t('method.' + p.method)}</td><td class="num">${p.kind === 'refund' ? '− ' : ''}${money(p.amount)}</td><td>${p.created_by_name || ''}</td></tr>`)}</tbody></table>`;

  render(el, html`
    <div class="page-head"><h1>${t('cash.daily')}</h1>
      <label class="inline">${t('date')}: <input type="date" id="d" value="${date}"></label></div>
    ${cashTabs('daily')}
    <div class="stats">
      <div class="stat"><div class="stat__label">${t('cash.net')}</div><div class="stat__value">${money(d.net)}</div></div>
      <div class="stat"><div class="stat__label">${t('cash.refunds')}</div><div class="stat__value">${money(d.refunds)}</div></div>
      <div class="stat"><div class="stat__label">${t('cash.invoices_today')}</div><div class="stat__value">${d.invoices_count}</div>
        <div class="muted small">${money(d.invoices_total)}${d.discounts ? html` · ${t('cash.discount')}: ${money(d.discounts)}` : ''}</div></div>
    </div>
    <section class="card"><h2>${t('cash.by_method')}</h2>${methodsTable}</section>
    <section class="card"><h2>${t('cash.payments')}</h2>${d.payments.length ? list : html`<p class="muted">${t('empty')}</p>`}</section>
    <p class="hint">${t('cash.bank_hint')}</p>
    <div class="actions"><button class="btn" id="print">${t('cash.print_daily')}</button></div>`);
  $('#d', el).onchange = (e) => go('/cash/daily' + qs({ date: e.target.value }));
  $('#print', el).onclick = () => printDoc(html`<article class="doc">${docHeader()}
    <h2 class="doc__title">${t('cash.daily')} — ${fmtDate(date)}</h2>${methodsTable}
    <p>${t('cash.invoices_today')}: ${d.invoices_count} (${money(d.invoices_total)})</p>${list}
    <div class="doc__sign">${t('cash.cashier')}: ____________________</div></article>`);
}
