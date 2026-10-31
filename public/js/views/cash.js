// Kassa: hisoblar, hisob yaratish sahifasi (xizmatlar × miqdor), to'lov, qaytarish, bekor qilish, chek va kunlik hisobot.
import {
  html, raw, render, $, $$, t, L, GET, POST, qs, can, go, toast, errorText, busy, confirmDialog, money, fmtDate,
  fmtDateTime, payBadge, pager, setQuery, localDate, printDoc, docHeader, METHODS, refresh, showWordButton, ApiError,
} from '../core.js';
import { invoiceTable, bindInvoiceDelete } from './main-views.js';

function cashTabs(active) {
  return html`<div class="tabs">
    <a class="tab ${active === 'list' ? 'tab--active' : ''}" href="#/cash">${t('cash.invoices')}</a>
    ${can('report.finance') ? html`<a class="tab" href="#/cash/stats">${t('stats')}</a>` : ''}
  </div>`;
}

const methodOptions = (sel) => METHODS.map((m) => html`<option value="${m}" ${m === sel ? raw('selected') : ''}>${t('method.' + m)}</option>`);
const toInt = (v) => { const n = Number(String(v).replace(/\s/g, '')); return Number.isFinite(n) ? Math.round(n) : NaN; };

/** Chegirma qatorlari (hisob sahifasi va chek) */
function discountRows(inv) {
  if (!inv.discount) return '';
  const lines = inv.discount_lines && inv.discount_lines.length ? inv.discount_lines : [{ uz: t('cash.discount'), ru: t('cash.discount'), amount: inv.discount }];
  return html`${lines.map((l) => html`<dt>${t('cash.discount')}: ${L(l)}</dt><dd>− ${money(l.amount)}</dd>`)}`;
}
/** Hisob yaratish sahifasidagi jami blok */
function discountTotals(subtotal, lines, total) {
  return html`${lines.length ? html`<dt>${t('cash.subtotal')}</dt><dd>${money(subtotal)}</dd>
    ${lines.map((l) => html`<dt class="text-ok">${t('cash.discount')}: ${L(l)}</dt><dd class="text-ok">− ${money(l.amount)}</dd>`)}` : ''}
    <dt class="totals__big">${t('cash.total')}</dt><dd class="totals__big" id="total">${money(total)}</dd>`;
}

/* ================= Hisoblar ro'yxati ================= */
export async function cashListView(el, query) {
  const f = { date: query.get('date') ?? localDate(), q: query.get('q') || '', debt: query.get('debt') === '1', page: Number(query.get('page')) || 1 };
  render(el, html`
    <div class="page-head"><h1>${t('nav.cash')}</h1>
      ${can('billing.write') ? html`<a class="btn" href="#/cash/new">+ ${t('cash.create')}</a>` : ''}</div>
    ${cashTabs('list')}
    <form class="filters card" id="f">
      <label class="inline">${t('date')}: <input type="date" name="date" value="${f.date}"></label>
      <input type="search" name="q" value="${f.q}" placeholder="${t('cash.search_ph')}" class="field--grow">
      <label class="inline"><input type="checkbox" name="debt" ${f.debt ? raw('checked') : ''}> ${t('cash.only_debt')}</label>
      <button class="btn">${t('search')}</button>
      <button type="button" class="btn btn--ghost" id="inv-word">${t('word')}</button>
    </form>
    <section class="card" id="res"></section>`);
  const form = $('#f', el);
  let cur = f;
  $('#inv-word', el).onclick = (e) => busy(e.target, () => invoicesWord(cur));
  const load = async (o) => {
    cur = o;
    setQuery('/cash', { date: o.date === localDate() ? '' : o.date || 'all', q: o.q, debt: o.debt ? 1 : '', page: o.page > 1 ? o.page : '' });
    const d = await GET('/api/invoices' + qs({ date: o.date, q: o.q, status: o.debt ? 'debt' : '', page: o.page }));
    const box = $('#res', el);
    render(box, d.rows.length ? invoiceTable(d.rows, { actions: true }) : html`<p class="muted">${t('empty')}</p>`);
    box.appendChild(pager(d, (pg) => load({ ...o, page: pg })));
    bindInvoiceDelete(box, d.rows, () => load(o));
  };
  form.onsubmit = (e) => {
    e.preventDefault();
    load({ date: form.elements.date.value, q: form.elements.q.value.trim(), debt: form.elements.debt.checked, page: 1 });
  };
  if (f.date === 'all') f.date = '';
  form.elements.date.value = f.date;
  load(f).catch((e) => toast(errorText(e), 'err'));
}

/** Hisoblar ro'yxati (joriy filtr bo'yicha) — Word jadvali, A4 yotiq varaq */
async function invoicesWord(o) {
  const d = await GET('/api/invoices' + qs({ date: o.date, q: o.q, status: o.debt ? 'debt' : '', all: 1 }));
  const sum = (k) => d.rows.reduce((a, r) => a + (r[k] || 0), 0);
  const title = `${t('nav.cash')}: ${o.date ? fmtDate(o.date) : t('period.all')}${o.debt ? ' · ' + t('cash.only_debt') : ''}`;
  await printDoc(html`<article class="doc">${docHeader()}
    <h2 class="doc__title">${title}</h2>
    ${o.q ? html`<p>${t('search')}: ${o.q}</p>` : ''}
    <table class="doc__table"><thead><tr><th>№</th><th>${t('cash.invoice')}</th><th>${t('date')}</th><th>${t('f.full_name')}</th><th>${t('f.services')}</th>
      <th class="num">${t('cash.subtotal')}</th><th class="num">${t('cash.discount')}</th><th class="num">${t('cash.total')}</th>
      <th class="num">${t('cash.paid')}</th><th class="num">${t('cash.debt')}</th><th>${t('status')}</th></tr></thead>
    <tbody>${d.rows.map((r, i) => html`<tr><td>${i + 1}</td><td>${r.number}</td><td>${fmtDateTime(r.created_at)}</td><td>${r.patient_name}</td><td>${r.services}</td>
      <td class="num">${money(r.subtotal)}</td><td class="num">${r.discount ? money(r.discount) : '—'}</td><td class="num">${money(r.total)}</td>
      <td class="num">${money(r.paid)}</td><td class="num">${r.debt ? money(r.debt) : '—'}</td><td>${t('pay.' + r.pay_status)}</td></tr>`)}
      <tr><th></th><th>${t('total')}</th><th></th><th>${d.rows.length}</th><th></th><th class="num">${money(sum('subtotal'))}</th><th class="num">${money(sum('discount'))}</th>
        <th class="num">${money(sum('total'))}</th><th class="num">${money(sum('paid'))}</th><th class="num">${money(sum('debt'))}</th><th></th></tr></tbody></table>
    ${d.total > d.rows.length ? html`<p>${t('word.limited', { n: d.rows.length })}</p>` : ''}
    <div class="doc__sign">${t('cash.cashier')}: ____________________</div>
  </article>`, { word: true, page: 'a4l', folder: 'cash', name: title });
}

/* ================= Hisob yaratish (kassa sahifasi) ================= */
/**
 * "+ Ҳисоб яратиш" tugmasi va qabul oynasidagi "Касса" tugmasi shu sahifani ochadi (#/cash/new?patient=..&visit=..).
 * Sahifada: bemor F.I.Sh. va tug'ilgan yili, xizmat turi (bir nechta bo'lishi mumkin), jami summa va to'lov.
 * Hisob qabulga bog'lanadi: berilgan qabul yoki bemorning bugungi qabuli.
 */
export async function newInvoiceView(el, query) {
  if (!can('billing.write')) { render(el, html`<p class="alert alert--err">${t('err.forbidden')}</p>`); return; }
  const patientId = Number(query.get('patient')) || null;
  const visitId = Number(query.get('visit')) || null;
  const services = await GET('/api/services');
  let patient = null;
  let linkVisit = null;

  render(el, html`
    <div class="page-head"><h1>${t('cash.create')}</h1>
      <a class="btn btn--ghost" href="#/cash">${t('cancel')}</a></div>
    ${cashTabs('')}
    <form class="card form invoice-page" id="invf" autocomplete="off">
      <div id="inv-pat"></div>
      <div id="inv-body">
        <table class="table items">
          <thead><tr><th>${t('cash.service_type')}</th><th class="num">${t('cash.qty')}</th><th class="num">${t('cash.amount')}</th><th></th></tr></thead>
          <tbody id="items"></tbody>
        </table>
        <button type="button" class="btn btn--ghost btn--sm" id="add">+ ${t('cash.add_service')}</button>
        ${services.length ? '' : html`<p class="alert alert--warn">${t('cash.no_services')}</p>`}
        <dl class="totals" id="totals"></dl>
        <div class="row">
          <label class="field"><span>${t('cash.pay_amount')}</span><input name="pay_amount" inputmode="numeric" class="num-input"></label>
          <label class="field"><span>${t('cash.method')}</span><select name="method">${methodOptions('cash')}</select></label>
        </div>
        <div class="dialog__actions"><a class="btn btn--ghost" href="#/cash">${t('cancel')}</a>
          <button type="submit" class="btn">${t('cash.save_invoice')}</button></div>
      </div>
    </form>`);
  {
    const dlg = el;
    const form = $('#invf', dlg);
    const tbody = $('#items', dlg);
    const patBox = $('#inv-pat', dlg);
    let payTouched = false;

    // Jami summa va avtomatik paket chegirmasi (server ham xuddi shu qoidalar bilan qayta hisoblaydi)
    const recalc = () => {
      const lines = [];
      $$('tr.item', tbody).forEach((tr) => {
        const s = services.find((x) => x.id === Number($('select', tr).value));
        const qty = toInt($('[data-k=qty]', tr).value);
        const amount = s && qty >= 1 ? s.price * qty : 0;
        $('[data-k=amount]', tr).textContent = money(amount);
        if (s && qty >= 1) lines.push({ price_group: s.price_group, unit_price: s.price, qty, name: s.name });
      });
      const c = window.PRICING.calculate(lines);
      render($('#totals', dlg), discountTotals(c.subtotal, c.lines, c.total));
      if (!payTouched) form.elements.pay_amount.value = c.total;
      return c.total;
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

    /* Bemor: Ф.И.Ш. va tug'ilgan yili darhol yoziladi. Bazada mos bemor bo'lsa, taklif qilinadi;
       tanlanmasa, saqlashda yangi bemor kartasi ochiladi. */
    const drawPatient = (p) => {
      render(patBox, html`
        <div class="grid-fields inv-patient">
          <label class="field field--wide"><span>${t('f.full_name')} *</span>
            <input name="pat_name" maxlength="200" required value="${p ? p.full_name : ''}" ${p ? raw('disabled') : ''}></label>
          <label class="field"><span>${t('f.birth_year')}</span>
            <input name="pat_year" inputmode="numeric" maxlength="4" pattern="\\d{4}" placeholder="1985"
              value="${p && p.birth_date ? p.birth_date.slice(0, 4) : ''}" ${p ? raw('disabled') : ''}></label>
          ${p ? html`<div class="field"><span>${p.code}</span><button type="button" class="btn btn--ghost btn--sm" id="chg">${t('visit.change_patient')}</button></div>` : ''}
        </div>
        ${linkVisit ? html`<div class="muted small">${t('cash.visit_link')}: ${fmtDateTime(linkVisit.visit_at)}</div>` : ''}
        <div class="suggest" id="suggest"></div>`);
      const chg = $('#chg', patBox);
      if (chg) chg.onclick = () => { patient = null; linkVisit = null; drawPatient(null); $('[name=pat_name]', patBox).focus(); };
      if (!p) bindSuggest();
    };
    const choose = async (p) => {
      patient = p;
      let visits = [];
      try { visits = (await GET(`/api/patients/${p.id}`)).visits.filter((v) => v.status !== 'cancelled'); } catch { /* ixtiyoriy */ }
      linkVisit = (visitId && visits.find((v) => v.id === visitId)) || visits.find((v) => v.visit_at.slice(0, 10) === localDate()) || null;
      drawPatient(p);
    };
    const showMatches = (rows, title) => {
      const sb = $('#suggest', patBox);
      render(sb, rows.length ? html`<div class="suggest__title">${title}</div>
        ${rows.map((m) => html`<button type="button" class="picker__item" data-use="${m.id}">
          <span><b>${m.full_name}</b> <span class="muted">${m.code} · ${m.birth_date ? m.birth_date.slice(0, 4) : '—'} · ${m.phone}</span></span></button>`)}` : '');
      $$('[data-use]', sb).forEach((b) => { b.onclick = () => choose(rows.find((r) => r.id === Number(b.dataset.use))); });
    };
    let timer; let seq = 0;
    function bindSuggest() {
      const inp = $('[name=pat_name]', patBox);
      inp.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          const q = inp.value.trim();
          if (q.length < 3) { showMatches([], ''); return; }
          const my = ++seq;
          try { const d = await GET('/api/patients' + qs({ q })); if (my === seq && !patient) showMatches(d.rows.slice(0, 5), t('visit.suggest')); } catch { /* ixtiyoriy */ }
        }, 300);
      });
    }
    /** Tanlangan bemor yoki yangi karta (ism + tug'ilgan yil). Takroriy bo'lishi mumkin bo'lsa, tanlash uchun ko'rsatiladi. */
    async function ensurePatient(force = false) {
      if (patient) return patient;
      const name = $('[name=pat_name]', patBox).value.trim();
      const year = $('[name=pat_year]', patBox).value.trim();
      if (!name) { toast(t('visit.need_name'), 'err'); $('[name=pat_name]', patBox).focus(); return null; }
      if (year && !/^\d{4}$/.test(year)) { toast(t('err.invalid') + ` (${t('f.birth_year')})`, 'err'); return null; }
      try {
        patient = await POST('/api/patients', { full_name: name, birth_date: year, force });
        return patient;
      } catch (e) {
        if (e instanceof ApiError && e.code === 'possible_duplicate') {
          showMatches(e.data.matches, t('cash.dup_choose'));
          const sb = $('#suggest', patBox);
          const f = document.createElement('div');
          render(f, html`<button type="button" class="btn btn--ghost btn--sm">${t('patient.create_anyway')}</button>`);
          $('button', f).onclick = () => ensurePatient(true).then((p) => { if (p) { drawPatient(p); toast(t('visit.patient_created')); } });
          sb.appendChild(f);
          toast(t('err.possible_duplicate'), 'err');
        } else toast(errorText(e), 'err');
        return null;
      }
    }

    addRow();
    if (patientId) {
      GET(`/api/patients/${patientId}`).then((d) => choose(d.patient)).catch((e) => { toast(errorText(e), 'err'); drawPatient(null); });
    } else { drawPatient(null); setTimeout(() => $('[name=pat_name]', patBox)?.focus(), 0); }

    form.onsubmit = async (e) => {
      e.preventDefault();
      const total = recalc();
      const items = $$('tr.item', tbody).map((tr) => ({ service_id: Number($('select', tr).value), qty: toInt($('[data-k=qty]', tr).value) }));
      if (!items.length) { toast(t('cash.need_items'), 'err'); return; }
      if (items.some((i) => !(i.qty >= 1))) { toast(t('err.invalid'), 'err'); return; }
      const payAmount = toInt(form.elements.pay_amount.value) || 0;
      if (payAmount > total) { toast(t('err.overpayment'), 'err'); return; }
      await busy(e.submitter, async () => {
        if (!(await ensurePatient())) return;
        const inv = await POST('/api/invoices', {
          patient_id: patient.id, visit_id: linkVisit ? linkVisit.id : null, items,
          payment: payAmount > 0 ? { amount: payAmount, method: form.elements.method.value } : null,
        });
        toast(t('saved'));
        go(`/cash/invoice/${inv.id}`);
      });
    };
  }
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
          ${discountRows(inv)}
          <dt class="totals__big">${t('cash.total')}</dt><dd class="totals__big">${money(inv.total)}</dd>
          <dt>${t('cash.paid')}</dt><dd>${money(inv.paid)}</dd>
          <dt>${t('cash.debt')}</dt><dd class="${inv.debt ? 'text-err' : ''}">${money(inv.debt)}</dd>
        </dl>
        <div class="actions">
          <button class="btn btn--ghost" id="print">${t('cash.print_receipt')}</button>
          ${showWordButton() ? html`<button class="btn btn--ghost" id="word">${t('word')}</button>` : ''}
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
  if ($('#word', el)) $('#word', el).onclick = () => printReceipt(inv, 'word');
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

function printReceipt(inv, mode = 'print') {
  printDoc(html`
    <article class="doc doc--receipt">
      ${docHeader()}
      <h2 class="doc__title">${t('cash.receipt')} ${inv.number}</h2>
      <p>${fmtDateTime(inv.created_at)}<br><b>${t('f.full_name')}:</b> ${inv.patient_name} (${inv.patient_code})</p>
      <table class="doc__table"><thead><tr><th>${t('cash.service')}</th><th class="num">${t('cash.price')}</th><th class="num">${t('cash.qty')}</th><th class="num">${t('cash.amount')}</th></tr></thead>
        <tbody>${inv.items.map((i) => html`<tr><td>${i.name}</td><td class="num">${money(i.unit_price)}</td><td class="num">${i.qty}</td><td class="num">${money(i.amount)}</td></tr>`)}</tbody></table>
      <dl class="totals">
        ${inv.discount ? html`<dt>${t('cash.subtotal')}</dt><dd>${money(inv.subtotal)}</dd>` : ''}
        ${discountRows(inv)}
        <dt><b>${t('cash.total')}</b></dt><dd><b>${money(inv.total)}</b></dd>
        <dt>${t('cash.paid')}</dt><dd>${money(inv.paid)}</dd>
        ${inv.debt ? html`<dt>${t('cash.debt')}</dt><dd>${money(inv.debt)}</dd>` : ''}
      </dl>
      ${inv.payments.filter((p) => !p.voided).map((p) => html`<div class="small">${fmtDateTime(p.paid_at)} · ${t('kind.' + p.kind)} · ${t('method.' + p.method)} · ${money(p.amount)}</div>`)}
      <p class="small muted">${t('cash.receipt_note')}</p>
    </article>`, { name: `${t('cash.receipt')} ${inv.number} ${inv.patient_name}`, word: mode === 'word', folder: 'cash' });
}
