// NURMED — ilovaning kirish nuqtasi: login, bosh menyu, til, soat va sahifalar marshruti.
import {
  html, raw, render, $, t, state, GET, POST, can, toast, errorText, parseHash, setUnauthorizedHandler, setRefresh,
  localDate, fmtDate, busy, modal, ApiError, downloadsList, clearDownloads, go, setting,
} from './core.js';
import { dashboardView, historyView, patientView } from './views/main-views.js';
import { newVisitView, visitView } from './views/visit.js';
import { cashListView, newInvoiceView, invoiceView } from './views/cash.js';
import { statsView, reportsRedirect } from './views/reports.js';
import { adminView } from './views/admin.js';

const app = $('#app');

const ROUTES = [
  { re: /^\/$/, view: (el, q) => dashboardView(el, q) },
  { re: /^\/visit\/new$/, perm: 'visit.create', view: (el, q) => newVisitView(el, q) },
  { re: /^\/visit\/(\d+)$/, perm: 'visit.list', view: (el, q, m) => visitView(el, Number(m[1])) },
  { re: /^\/history$/, perm: 'visit.list', view: (el, q) => historyView(el, q) },
  { re: /^\/history\/stats$/, perm: 'report.visits', view: (el, q) => statsView(el, q, 'visits') },
  { re: /^\/patient\/(\d+)$/, perm: 'patient.read', view: (el, q, m) => patientView(el, Number(m[1])) },
  { re: /^\/cash$/, perm: 'billing.read', view: (el, q) => cashListView(el, q) },
  { re: /^\/cash\/new$/, perm: 'billing.write', view: (el, q) => newInvoiceView(el, q) },
  { re: /^\/cash\/invoice\/(\d+)$/, perm: 'billing.read', view: (el, q, m) => invoiceView(el, Number(m[1])) },
  { re: /^\/cash\/daily$/, perm: 'billing.read', view: () => go('/cash') }, // eski havola
  { re: /^\/cash\/stats$/, perm: 'report.finance', view: (el, q) => statsView(el, q, 'finance') },
  { re: /^\/reports$/, any: ['report.visits', 'report.finance'], view: () => reportsRedirect() },
  { re: /^\/admin$/, perm: 'settings.clinic', view: (el, q) => adminView(el, q) },
];

const NAV = [
  { href: '#/', key: 'nav.dashboard', match: /^\/$/ },
  { href: '#/visit/new', key: 'nav.visit', perm: 'visit.create', match: /^\/visit/ },
  { href: '#/history', key: 'nav.history', perm: 'visit.list', match: /^\/(history|patient)/ },
  { href: '#/cash', key: 'nav.cash', perm: 'billing.read', match: /^\/cash/ },
  { href: '#/admin', key: 'nav.admin', perm: 'settings.clinic', match: /^\/admin/ },
];
const allowed = (r) => (r.perm ? can(r.perm) : r.any ? r.any.some(can) : true);

/* ---------- Til va rejim ---------- */
function setLang(lang) {
  state.lang = lang;
  localStorage.setItem('nurmed_lang', lang);
  document.documentElement.lang = lang === 'uz' ? 'uz-Cyrl' : 'ru';
  start();
}
const ICON_SUN = raw('<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>');
const ICON_MOON = raw('<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>');
const isDark = () => document.documentElement.dataset.theme === 'dark';
const themeButton = () => html`<button type="button" class="icon-btn" id="theme-toggle"
  title="${isDark() ? t('theme.light') : t('theme.dark')}" aria-label="${isDark() ? t('theme.light') : t('theme.dark')}">${isDark() ? ICON_SUN : ICON_MOON}</button>`;
const langSwitch = () => html`<div class="lang">
  <button type="button" class="${state.lang === 'uz' ? 'active' : ''}" data-lang="uz">Ўзб</button>
  <button type="button" class="${state.lang === 'ru' ? 'active' : ''}" data-lang="ru">Рус</button></div>`;
function bindLang(root) {
  root.querySelectorAll('[data-lang]').forEach((b) => { b.onclick = () => setLang(b.dataset.lang); });
  const tb = root.querySelector('#theme-toggle');
  if (tb) tb.onclick = () => {
    const next = isDark() ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('nurmed_theme', next);
    render(tb, isDark() ? ICON_SUN : ICON_MOON);
    tb.title = isDark() ? t('theme.light') : t('theme.dark');
  };
}

/* ---------- Kirish ---------- */
function loginScreen(msg) {
  stopClock();
  render(app, html`
    <div class="login">
      <form class="login__box card" id="login">
        <div class="login__brand"><span class="brand__mark">N</span> NURMED</div>
        <div class="muted">${t('login.subtitle')}</div>
        ${msg ? html`<div class="alert alert--warn">${msg}</div>` : ''}
        <label class="field"><span>${t('f.username')}</span><input name="username" autocomplete="username" required autofocus></label>
        <label class="field"><span>${t('f.password')}</span><input name="password" type="password" autocomplete="current-password" required></label>
        <button class="btn btn--lg">${t('login.submit')}</button>
        <div class="login__tools">${langSwitch()}${themeButton()}</div>
      </form>
    </div>`);
  bindLang(app);
  const f = $('#login');
  f.onsubmit = async (e) => {
    e.preventDefault();
    try {
      await POST('/api/login', { username: f.elements.username.value.trim(), password: f.elements.password.value });
      start();
    } catch (err) { toast(errorText(err), 'err'); f.elements.password.value = ''; }
  };
}

function passwordScreen(forced) {
  const content = html`
    <form class="form dialog__body" id="pw">
      <h2>${t('pw.title')}</h2>
      ${forced ? html`<div class="alert alert--warn">${t('pw.forced')}</div>` : ''}
      <label class="field"><span>${t('pw.old')}</span><input name="old" type="password" autocomplete="current-password" required></label>
      <label class="field"><span>${t('pw.new')}</span><input name="n1" type="password" autocomplete="new-password" minlength="8" required></label>
      <label class="field"><span>${t('pw.repeat')}</span><input name="n2" type="password" autocomplete="new-password" minlength="8" required></label>
      <div class="dialog__actions">
        ${forced ? html`<button type="button" class="btn btn--ghost" id="pw-logout">${t('logout')}</button>`
          : html`<button type="button" class="btn btn--ghost" data-close>${t('cancel')}</button>`}
        <button class="btn">${t('save')}</button>
      </div>
    </form>`;
  const bind = (root, close) => {
    const f = $('#pw', root);
    const lo = $('#pw-logout', root);
    if (lo) lo.onclick = logout;
    f.onsubmit = async (e) => {
      e.preventDefault();
      if (f.elements.n1.value !== f.elements.n2.value) { toast(t('pw.mismatch'), 'err'); return; }
      await busy(e.submitter, async () => {
        await POST('/api/me/password', { old_password: f.elements.old.value, new_password: f.elements.n1.value });
        toast(t('pw.changed'));
        if (close) close();
        start();
      });
    };
  };
  if (forced) {
    stopClock();
    render(app, html`<div class="login"><div class="login__box card">${content}</div></div>`);
    bind(app);
  } else modal(content, bind);
}

/** Saqlangan (yuklab olingan) fayllar: qaysi papkaga tushgani, ro'yxati va papkani qanday ochish/o'zgartirish */
function filesDialog() {
  const list = downloadsList();
  const when = (ms) => { const d = new Date(ms); return `${fmtDate(localDate(d))} ${d.toTimeString().slice(0, 5)}`; };
  modal(html`
    <div class="dialog__body">
      <div class="card-head"><h2>${t('files.title')}</h2><button type="button" class="btn btn--ghost btn--sm" data-close>×</button></div>
      ${state.settings.word_save_dir ? html`<div class="alert alert--ok files-where">
        <div>${t('files.server_dir')}</div><code>${state.settings.word_save_dir}</code>
        ${['history', 'cash'].filter((f) => state.settings['word_save_dir_' + f]).map((f) => html`
          <div class="small">${t('admin.dir_' + f)}:</div><code>${state.settings['word_save_dir_' + f]}</code>`)}
        <div class="small">${t('files.server_dir_note')}</div></div>` : ''}
      <div class="alert alert--warn files-where">
        <div>${t('files.where')}</div>
        <code>C:\Users\&lt;${t('files.user')}&gt;\Downloads</code>
      </div>
      <ol class="files-help">
        <li>${raw(t('files.open'))}</li>
        <li>${raw(t('files.change'))}</li>
      </ol>
      <h3>${t('files.recent')} (${list.length})</h3>
      ${list.length ? html`<table class="table table--compact"><thead><tr><th>${t('files.name')}</th><th>${t('time')}</th></tr></thead>
        <tbody>${list.map((f) => html`<tr><td><code>${f.name}</code></td><td>${when(f.at)}</td></tr>`)}</tbody></table>`
        : html`<p class="muted">${t('empty')}</p>`}
      <p class="hint">${t('files.note')}</p>
      <div class="dialog__actions">
        ${list.length ? html`<button type="button" class="btn btn--ghost" id="files-clear">${t('files.clear')}</button>` : ''}
        <button type="button" class="btn" data-close>${t('confirm')}</button>
      </div>
    </div>`, (dlg, close) => {
    const c = $('#files-clear', dlg);
    if (c) c.onclick = () => { clearDownloads(); close(); filesDialog(); };
  });
}

async function logout() {
  try { await POST('/api/logout'); } catch { /* baribir chiqamiz */ }
  state.user = null;
  loginScreen();
}

/* ---------- Asosiy oyna ---------- */
let clockTimer = null;
function stopClock() { clearInterval(clockTimer); clockTimer = null; }
function tickClock() {
  const c = $('#clock');
  if (!c) return;
  const d = new Date();
  c.textContent = `${fmtDate(localDate(d))} ${d.toTimeString().slice(0, 8)}`;
}

function shell() {
  const s = state.settings;
  render(app, html`
    <header class="topbar">
      <a class="brand" href="#/">
        ${s.clinic_logo ? html`<img class="brand__logo" src="${s.clinic_logo}" alt="">` : html`<span class="brand__mark">N</span>`}
        <span class="brand__name">${setting('clinic_name') || 'NURMED'}</span></a>
      <nav class="nav" id="nav">${NAV.filter(allowed).map((n) => html`<a href="${n.href}" data-match="${n.match.source}">${t(n.key)}</a>`)}</nav>
      <div class="topbar__right">
        <span class="clock" id="clock"></span>
        ${langSwitch()}${themeButton()}
        <details class="user-menu">
          <summary>${state.user.full_name}</summary>
          <div class="user-menu__body">
            <div class="muted small">${state.user.roles.map((r) => t('role.' + r)).join(', ')}</div>
            <button type="button" class="btn btn--ghost btn--sm" id="files">${t('files.title')}</button>
            <button type="button" class="btn btn--ghost btn--sm" id="chpw">${t('pw.title')}</button>
            <button type="button" class="btn btn--ghost btn--sm" id="logout">${t('logout')}</button>
          </div>
        </details>
      </div>
    </header>
    <main class="main" id="view"></main>`);
  bindLang(app);
  $('#logout').onclick = logout;
  $('#chpw').onclick = () => { $('.user-menu').open = false; passwordScreen(false); };
  $('#files').onclick = () => { $('.user-menu').open = false; filesDialog(); };
  stopClock();
  tickClock();
  clockTimer = setInterval(tickClock, 1000);
}

let renderSeq = 0;
async function route() {
  if (!state.user) return;
  const { path, query } = parseHash();
  $$nav(path);
  // Har bir sahifa yangi idishga chiziladi: oldingi sahifa kechikib yuklansa, u ekrandan uzilgan
  // idishga yoziladi va yangi sahifaning ustiga chiqmaydi.
  const view = document.createElement('div');
  $('#view').replaceChildren(view);
  const r = ROUTES.find((x) => x.re.test(path));
  const my = ++renderSeq;
  state.leaveGuard = null;
  if (!r) { render(view, html`<p class="alert alert--err">${t('err.not_found')}</p>`); return; }
  if (!allowed(r)) { render(view, html`<p class="alert alert--err">${t('err.forbidden')}</p>`); return; }
  render(view, html`<p class="muted">${t('loading')}</p>`);
  try {
    await r.view(view, query, path.match(r.re));
  } catch (e) {
    if (my !== renderSeq) return;
    if (e instanceof ApiError && e.status === 401) return;
    console.error(e);
    render(view, html`<p class="alert alert--err">${errorText(e)}</p>`);
  }
  if (my === renderSeq) window.scrollTo(0, 0);
}
function $$nav(path) {
  document.querySelectorAll('#nav a').forEach((a) => a.classList.toggle('active', new RegExp(a.dataset.match).test(path)));
}

let lastHash = location.hash;
window.addEventListener('hashchange', async () => {
  // Saqlanmagan qabul: avval «Очиқ» holatda saqlashga urinamiz; bo'lmasa (masalan, F.И.Ш. yozilmagan) so'raymiz
  const g = state.leaveGuard;
  if (g && g.dirty()) {
    const saved = g.autosave ? await g.autosave() : false;
    if (!saved && !window.confirm(t('visit.leave_confirm'))) {
      history.replaceState(null, '', lastHash || '#/');
      return;
    }
  }
  lastHash = location.hash;
  route();
});
window.addEventListener('beforeunload', (e) => {
  const g = state.leaveGuard;
  if (g && g.dirty() && !(g.autosaveOnClose && g.autosaveOnClose())) e.preventDefault();
});

setUnauthorizedHandler(() => { state.user = null; loginScreen(t('login.expired')); });
setRefresh(() => route());
document.addEventListener('nurmed:settings', () => { shell(); route(); });

async function start() {
  document.documentElement.lang = state.lang === 'uz' ? 'uz-Cyrl' : 'ru';
  document.title = 'NURMED';
  try {
    const me = await GET('/api/me');
    state.user = me.user;
    state.settings = me.settings;
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) { loginScreen(); return; }
    render(app, html`<div class="login"><div class="alert alert--err">${errorText(e)}</div></div>`);
    return;
  }
  if (state.user.must_change_password) { passwordScreen(true); return; }
  document.title = setting('clinic_name') || 'NURMED';
  shell();
  route();
}

start();
