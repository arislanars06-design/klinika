// NURMED — umumiy yordamchilar: API, xavfsiz HTML, tarjima, formatlash, dialoglar, router.
import { DICT } from './i18n.js';
import { docToDocx, downloadBlob, safeName } from './docx.js';

export const state = {
  user: null,
  settings: {},
  lang: localStorage.getItem('nurmed_lang') === 'ru' ? 'ru' : 'uz',
  leaveGuard: null, // { dirty: () => boolean } — saqlanmagan tibbiy yozuv bo'lsa, sahifadan chiqishda so'raladi
};

/* ---------- Tarjima ---------- */
export function t(key, vars) {
  const d = DICT[state.lang] || DICT.uz;
  let s = d[key] ?? DICT.uz[key];
  if (s === undefined) { console.warn('i18n missing:', key); s = key; }
  if (vars) s = s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? ''));
  return s;
}
export const L = (obj) => (obj ? obj[state.lang] || obj.uz : '');

/* ---------- Xavfsiz HTML (barcha qiymatlar avtomatik escape qilinadi) ---------- */
class Raw { constructor(s) { this.s = s; } toString() { return this.s; } }
export const raw = (s) => new Raw(String(s));
const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ESC[c]);
function val(v) {
  if (v instanceof Raw) return v.s;
  if (Array.isArray(v)) return v.map(val).join('');
  if (v === null || v === undefined || v === false) return '';
  return esc(v);
}
export function html(strings, ...vals) {
  let out = '';
  strings.forEach((s, i) => { out += s; if (i < vals.length) out += val(vals[i]); });
  return new Raw(out);
}
export function render(el, content) {
  el.innerHTML = content instanceof Raw ? content.s : esc(content);
  // CSP inline style ruxsat bermaydi: kenglik kabi qiymatlar data-atributdan o'rnatiladi
  el.querySelectorAll('[data-w]').forEach((n) => { n.style.width = n.dataset.w + '%'; });
  return el;
}
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

/* ---------- API ---------- */
export class ApiError extends Error {
  constructor(status, data) { super(data && data.error); this.status = status; this.data = data || {}; this.code = this.data.error; }
}
let onUnauthorized = () => {};
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };

export async function api(method, path, body) {
  const r = await fetch(path, {
    method,
    headers: { 'X-Nurmed': '1', ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}) },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'same-origin',
  });
  let data = null;
  try { data = await r.json(); } catch { /* bo'sh javob */ }
  if (!r.ok) {
    const err = new ApiError(r.status, data);
    if (r.status === 401 && path !== '/api/login') onUnauthorized();
    throw err;
  }
  return data;
}
export const GET = (p) => api('GET', p);
export const POST = (p, b = {}) => api('POST', p, b);
export const PUT = (p, b = {}) => api('PUT', p, b);

export function qs(obj) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(obj)) if (v !== undefined && v !== null && v !== '') p.set(k, v);
  const s = p.toString();
  return s ? '?' + s : '';
}

export function errorText(e) {
  if (!(e instanceof ApiError)) return t('err.network');
  const key = 'err.' + e.code;
  const d = DICT[state.lang] || DICT.uz;
  let msg = d[key] ?? DICT.uz[key] ?? t('err.server_error');
  if (e.data.field) msg += ` (${fieldName(e.data.field)})`;
  return msg;
}
function fieldName(f) {
  const base = String(f).split('.')[0];
  const k = 'f.' + base;
  return (DICT[state.lang] || DICT.uz)[k] ?? DICT.uz[k] ?? f;
}

export const can = (perm) => !!state.user && state.user.perms.includes(perm);
export const hasRole = (r) => !!state.user && state.user.roles.includes(r);

/* ---------- Formatlash ---------- */
export function money(n) {
  const s = Math.round(Number(n) || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  return `${s} ${t('sum')}`;
}
export function fmtDate(s) {
  if (!s) return '';
  if (/^\d{4}$/.test(s)) return s;
  const [y, m, d] = s.slice(0, 10).split('-');
  return `${d}.${m}.${y}`;
}
export const fmtDateTime = (s) => (s ? `${fmtDate(s)} ${s.slice(11, 16)}` : '');
export function localDate(d = new Date()) {
  const z = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}`;
}
export function addDays(dateStr, n) {
  const d = new Date(dateStr + 'T12:00:00');
  d.setDate(d.getDate() + n);
  return localDate(d);
}
export function age(birth) {
  if (!birth) return '';
  const today = localDate();
  let a = Number(today.slice(0, 4)) - Number(birth.slice(0, 4));
  if (birth.length === 10 && today.slice(5) < birth.slice(5)) a -= 1;
  return a >= 0 ? a : '';
}
export const genderText = (g) => (g === 'm' ? t('gender.m') : g === 'f' ? t('gender.f') : '');

export function statusBadge(s) {
  return html`<span class="badge badge--${s}">${t('status.' + s)}</span>`;
}
export function payBadge(s) {
  return html`<span class="badge badge--pay-${s}">${t('pay.' + s)}</span>`;
}
// To'lov usullari: Нақд, Карта, Терминал (eski yozuvlardagi boshqa usullar faqat ko'rsatiladi)
export const METHODS = ['cash', 'card', 'terminal'];

/* ---------- Bildirishnoma va dialoglar ---------- */
export function toast(msg, type = 'ok') {
  const box = $('#toasts');
  const el = document.createElement('div');
  el.className = `toast toast--${type}`;
  el.textContent = msg;
  box.appendChild(el);
  setTimeout(() => el.classList.add('toast--hide'), 3500);
  setTimeout(() => el.remove(), 4000);
}

/** Tasdiqlash oynasi. opts.input = true bo'lsa, sabab so'raladi (majburiy). Natija: false yoki matn/true. */
export function confirmDialog(message, opts = {}) {
  return new Promise((resolve) => {
    const dlg = document.createElement('dialog');
    dlg.className = 'dialog';
    render(dlg, html`
      <form method="dialog" class="dialog__body">
        <p class="dialog__msg">${message}</p>
        ${opts.input ? html`<textarea name="reason" rows="3" required maxlength="500" placeholder="${opts.placeholder || t('reason')}"></textarea>` : ''}
        <div class="dialog__actions">
          <button type="button" class="btn btn--ghost" data-act="cancel">${t('cancel')}</button>
          <button type="submit" class="btn ${opts.danger ? 'btn--danger' : ''}">${opts.okText || t('confirm')}</button>
        </div>
      </form>`);
    document.body.appendChild(dlg);
    const finish = (v) => { dlg.close(); dlg.remove(); resolve(v); };
    dlg.querySelector('[data-act=cancel]').onclick = () => finish(false);
    dlg.addEventListener('cancel', (e) => { e.preventDefault(); finish(false); });
    dlg.querySelector('form').onsubmit = (e) => {
      e.preventDefault();
      if (opts.input) {
        const v = dlg.querySelector('textarea').value.trim();
        if (!v) return;
        finish(v);
      } else finish(true);
    };
    dlg.showModal();
  });
}

/** Ixtiyoriy kontentli modal oyna. build(dlg, close) ichida forma ulanadi. */
export function modal(content, build) {
  const dlg = document.createElement('dialog');
  dlg.className = 'dialog dialog--wide';
  render(dlg, content);
  document.body.appendChild(dlg);
  const close = () => { dlg.close(); dlg.remove(); };
  dlg.addEventListener('cancel', (e) => { e.preventDefault(); close(); });
  dlg.querySelectorAll('[data-close]').forEach((b) => { b.onclick = close; });
  build && build(dlg, close);
  dlg.showModal();
  return close;
}

/** Tugmani so'rov davomida bloklaydi va xatoni ko'rsatadi */
export async function busy(btn, fn) {
  if (btn) btn.disabled = true;
  // Xato foydalanuvchiga ko'rsatiladi; qayta otilmaydi (aks holda brauzerda "ushlanmagan xato" bo'ladi)
  try { return await fn(); } catch (e) { toast(errorText(e), 'err'); return undefined; } finally { if (btn) btn.disabled = false; }
}

/* ---------- Sahifalash ---------- */
export function pager(data, onPage) {
  const pages = Math.max(1, Math.ceil(data.total / data.page_size));
  const el = document.createElement('div');
  el.className = 'pager';
  render(el, html`
    <span>${t('total')}: ${data.total}</span>
    <button class="btn btn--ghost btn--sm" data-p="${data.page - 1}" ${data.page <= 1 ? raw('disabled') : ''}>‹</button>
    <span>${data.page} / ${pages}</span>
    <button class="btn btn--ghost btn--sm" data-p="${data.page + 1}" ${data.page >= pages ? raw('disabled') : ''}>›</button>`);
  el.querySelectorAll('[data-p]').forEach((b) => { b.onclick = () => onPage(Number(b.dataset.p)); });
  return el;
}

/* ---------- Router (#/yo'l?parametrlar) ---------- */
export function parseHash() {
  const h = location.hash.replace(/^#/, '') || '/';
  const [path, query = ''] = h.split('?');
  return { path, query: new URLSearchParams(query) };
}
export function go(path) {
  // A hashchange event does not fire for the same address, so redraw the page directly
  if (location.hash === '#' + path) refreshFn();
  else location.hash = '#' + path;
}
let refreshFn = () => {};
export const setRefresh = (fn) => { refreshFn = fn; };
/** Joriy sahifani qayta chizish */
export const refresh = () => refreshFn();
export function setQuery(path, params) {
  history.replaceState(null, '', '#' + path + qs(params));
}

/* ---------- Bemor qidirish vidjeti ---------- */
export function patientPicker(container, onPick, opts = {}) {
  render(container, html`
    <div class="picker">
      <input type="search" class="picker__input" placeholder="${t('patient.search_ph')}" autocomplete="off">
      <div class="picker__results"></div>
    </div>`);
  const input = $('.picker__input', container);
  const box = $('.picker__results', container);
  let timer; let seq = 0;
  const run = async () => {
    const q = input.value.trim();
    if (q.length < 2) { render(box, ''); return; }
    const my = ++seq;
    try {
      const d = await GET('/api/patients' + qs({ q }));
      if (my !== seq) return;
      render(box, d.rows.length ? html`${d.rows.map((p) => html`
        <button type="button" class="picker__item" data-id="${p.id}">
          <b>${p.full_name}</b> <span class="muted">${p.code} · ${fmtDate(p.birth_date)} · ${p.phone}</span>
          ${p.last_visit ? html`<span class="muted small">${t('patient.last_visit')}: ${fmtDate(p.last_visit)}</span>` : ''}
        </button>`)}` : html`<div class="muted picker__empty">${t('patient.not_found')}</div>`);
      box.querySelectorAll('[data-id]').forEach((b) => {
        b.onclick = () => onPick(d.rows.find((p) => p.id === Number(b.dataset.id)));
      });
    } catch (e) { toast(errorText(e), 'err'); }
  };
  input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(run, 250); });
  if (opts.autofocus !== false) setTimeout(() => input.focus(), 0);
  return input;
}

export function patientSummary(p) {
  return html`
    <div class="patient-summary">
      <div class="patient-summary__name"><a href="#/patient/${p.id}">${p.full_name}</a> <span class="muted">${p.code}</span></div>
      <div class="muted">
        ${p.birth_date ? html`${fmtDate(p.birth_date)} (${age(p.birth_date)} ${t('years')})` : ''}
        ${p.gender ? html` · ${genderText(p.gender)}` : ''}
        ${p.phone ? html` · ${p.phone}` : ''}
        ${p.address ? html` · ${p.address}` : ''}
      </div>
    </div>`;
}

/* ---------- Chop etish ---------- */
/* ---------- Shu kompyuterda yuklab olingan fayllar ro'yxati ---------- */
const DL_KEY = 'nurmed_downloads';
export function downloadsList() {
  try { const a = JSON.parse(localStorage.getItem(DL_KEY) || '[]'); return Array.isArray(a) ? a : []; } catch { return []; }
}
function rememberDownload(name) {
  const list = [{ name, at: Date.now() }, ...downloadsList()].slice(0, 50);
  try { localStorage.setItem(DL_KEY, JSON.stringify(list)); } catch { /* xotira to'la */ }
}
export function clearDownloads() { localStorage.removeItem(DL_KEY); }

/** Sozlamada server papkasi berilgan bo'lsa, Word faylning nusxasi o'sha papkaga yoziladi */
export async function saveCopyOnServer(blob, filename) {
  if (!state.settings.word_save_dir) return null;
  try {
    const r = await fetch('/api/files' + qs({ name: filename }), {
      method: 'POST', body: blob, credentials: 'same-origin',
      headers: { 'X-Nurmed': '1', 'Content-Type': 'application/octet-stream' },
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new ApiError(r.status, d);
    toast(t('word.saved_server', { path: d.path }));
    return d.path;
  } catch (e) { toast(t('word.save_failed') + ': ' + errorText(e), 'err'); return null; }
}

/** "Чоп этиш" tugmasi Word fayl ochadimi (Созламалар → Клиника → Чоп этиш усули) */
export const printsToWord = () => state.settings.print_mode !== 'browser';
/** Alohida "Word" tugmasi faqat chop etish brauzer orqali bo'lganda ko'rsatiladi */
export const showWordButton = () => !printsToWord();

/**
 * Hujjatni chop etish yoki Word fayli (.docx) sifatida yuklab olish.
 * opts.name — Word fayl nomi (kengaytmasiz). opts.word = true bo'lsa yoki sozlamada Word tanlangan bo'lsa, .docx yuklanadi.
 */
export function printDoc(content, opts = {}) {
  const root = $('#print-root');
  render(root, content);
  const imgs = $$('img', root);
  return Promise.all(imgs.map((i) => (i.complete ? null : new Promise((r) => { i.onload = i.onerror = r; })))).then(() => {
    if (!(opts.word || printsToWord())) { window.print(); return; }
    const doc = $('.doc', root) || root;
    const filename = safeName(opts.name || 'hujjat') + '.docx';
    const blob = docToDocx(doc, opts.page);
    downloadBlob(blob, filename);
    rememberDownload(filename);
    toast(t('word.saved_to', { name: filename }));
    return saveCopyOnServer(blob, filename);
  });
}

/**
 * Hujjat sarlavhasi (Созламалар → Клиника): vazirlik, logo + klinika nomi, tavsif, yo'nalishlar,
 * manzil, telefonlar, Telegram/Instagram, rekvizitlar. Bo'sh maydonlar chiqmaydi.
 */
/**
 * Hujjat sarlavhasi — jadval (Созламалар → Клиника):
 *   1-qator: vazirlik + klinika tavsifi
 *   2-qator: logo (yo'q bo'lsa klinika nomi) | Хизматлар (ro'yxat) | Реквизитлар (manzil, telefonlar, Telegram/Instagram)
 */
/** Sozlama qiymati joriy tilda: ruschada «<kalit>_ru» (bo'sh bo'lsa o'zbekchasi) */
export function setting(key) {
  const s = state.settings || {};
  return (state.lang === 'ru' && s[key + '_ru']) || s[key] || '';
}

export function docHeader() {
  const s = {
    ...state.settings,
    ...Object.fromEntries(['clinic_name', 'clinic_ministry', 'clinic_subtitle', 'clinic_services', 'clinic_address', 'clinic_requisites'].map((k) => [k, setting(k)])),
  };
  const services = String(s.clinic_services || '').split('\n').map((x) => x.trim()).filter(Boolean);
  const social = [s.clinic_telegram ? `Telegram: ${s.clinic_telegram}` : '', s.clinic_instagram ? `Instagram: ${s.clinic_instagram}` : ''].filter(Boolean).join(' · ');
  const hasReq = s.clinic_address || s.clinic_phone || social || s.clinic_requisites;
  const top = s.clinic_ministry || s.clinic_subtitle;
  const cols = 1 + (services.length ? 1 : 0) + (hasReq ? 1 : 0);
  return html`
    <header class="doc__head">
      <table class="doc__htable">
        <colgroup><col class="doc__col-logo">${services.length ? html`<col class="doc__col-serv">` : ''}${hasReq ? html`<col>` : ''}</colgroup>
        ${top ? html`<tr><td class="doc__htop" colspan="${cols}">
          ${s.clinic_ministry ? html`<div class="doc__ministry">${s.clinic_ministry}</div>` : ''}
          ${s.clinic_subtitle ? html`<div class="doc__sub">${s.clinic_subtitle}</div>` : ''}</td></tr>` : ''}
        <tr>
          <td class="doc__hlogo">${s.clinic_logo ? html`<img class="doc__logo" src="${s.clinic_logo}" alt="">` : html`<div class="doc__clinic">${s.clinic_name}</div>`}</td>
          ${services.length ? html`<td class="doc__hserv"><div class="doc__hcap">${t('doc.services')}</div>
            ${services.map((x) => html`<div class="doc__hli">• ${x}</div>`)}</td>` : ''}
          ${hasReq ? html`<td class="doc__hreq"><div class="doc__hcap">${t('doc.requisites')}</div>
            ${s.clinic_address ? html`<div class="doc__hline doc__hgap">${t('doc.addr')}: ${s.clinic_address}</div>` : ''}
            ${s.clinic_phone ? html`<div class="doc__hline">${t('doc.tel')}: ${s.clinic_phone}</div>` : ''}
            ${social ? html`<div class="doc__hline">${social}</div>` : ''}
            ${s.clinic_requisites ? html`<div class="doc__hline">${s.clinic_requisites}</div>` : ''}</td>` : ''}
        </tr>
      </table>
    </header>`;
}
