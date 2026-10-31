// Administrator: klinika rekvizitlari, xodimlar va rollar, xizmatlar narxi, audit jurnali, zaxira nusxalari.
import {
  html, raw, render, $, $$, t, state, GET, POST, PUT, qs, toast, busy, fmtDateTime, pager, modal, refresh, confirmDialog, can,
} from '../core.js';

const TABS = ['settings', 'users', 'services', 'audit', 'backup'];
const ROLES = ['admin', 'doctor', 'registrar', 'cashier'];

export async function adminView(el, query) {
  // Shifokor, registrator va kassir faqat «Клиника» bo'limini ko'radi
  const tabs = can('admin') ? TABS : ['settings'];
  const tab = tabs.includes(query.get('tab')) ? query.get('tab') : 'settings';
  render(el, html`
    <div class="page-head"><h1>${t('nav.admin')}</h1></div>
    <div class="tabs">${tabs.map((x) => html`<a class="tab ${x === tab ? 'tab--active' : ''}" href="#/admin?tab=${x}">${t('admin.' + x)}</a>`)}</div>
    <div id="admin-body"></div>`);
  const body = $('#admin-body', el);
  await ({ settings, users, services, audit, backup })[tab](body, query);
}

/**
 * Logoni brauzerda kichraytirish: eng katta tomoni 480 px, PNG (shaffoflik saqlanadi).
 * Juda katta bo'lsa JPEG. Natija Word ham tushunadigan data:image/png|jpeg.
 */
function shrinkImage(file, max = 480) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const k = Math.min(1, max / Math.max(img.naturalWidth, img.naturalHeight));
      const c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(img.naturalWidth * k));
      c.height = Math.max(1, Math.round(img.naturalHeight * k));
      const g = c.getContext('2d');
      g.imageSmoothingQuality = 'high';
      g.drawImage(img, 0, 0, c.width, c.height);
      let data = c.toDataURL('image/png');
      if (data.length > 600000) {
        const j = document.createElement('canvas'); j.width = c.width; j.height = c.height;
        const jg = j.getContext('2d'); jg.fillStyle = '#fff'; jg.fillRect(0, 0, j.width, j.height); jg.drawImage(c, 0, 0);
        data = j.toDataURL('image/jpeg', 0.88);
      }
      resolve(data);
    };
    img.onerror = () => reject(new Error('bad image'));
    // CSP faqat data: rasmlarga ruxsat beradi, shuning uchun fayl data URL sifatida o'qiladi
    const r = new FileReader();
    r.onload = () => { img.src = r.result; };
    r.onerror = () => reject(new Error('read error'));
    r.readAsDataURL(file);
  });
}

/* ---------- Klinika rekvizitlari ---------- */
async function settings(el) {
  const s = state.settings;
  render(el, html`
    <form class="form card" id="sf">
      <label class="field"><span>${t('admin.clinic_ministry')}</span><input name="clinic_ministry" maxlength="200" value="${s.clinic_ministry || ''}"></label>
      <label class="field"><span>${t('admin.clinic_name')} *</span><input name="clinic_name" required maxlength="200" value="${s.clinic_name}"></label>
      <label class="field"><span>${t('admin.clinic_subtitle')}</span><input name="clinic_subtitle" maxlength="300" value="${s.clinic_subtitle || ''}"></label>
      <label class="field"><span>${t('admin.clinic_services')}</span><textarea name="clinic_services" rows="5" maxlength="600">${s.clinic_services || ''}</textarea>
        <span class="hint">${t('admin.clinic_services_hint')}</span></label>
      <label class="field"><span>${t('f.address')}</span><input name="clinic_address" maxlength="300" value="${s.clinic_address}"></label>
      <label class="field"><span>${t('admin.clinic_phones')}</span><input name="clinic_phone" maxlength="100" value="${s.clinic_phone}" placeholder="+998 90 123 45 67; +998 99 765 43 21"></label>
      <div class="grid-fields">
        <label class="field"><span>Telegram</span><input name="clinic_telegram" maxlength="60" placeholder="@username" value="${s.clinic_telegram || ''}"></label>
        <label class="field"><span>Instagram</span><input name="clinic_instagram" maxlength="60" placeholder="@username" value="${s.clinic_instagram || ''}"></label>
      </div>
      <label class="field"><span>${t('admin.requisites')}</span><textarea name="clinic_requisites" rows="2" maxlength="500">${s.clinic_requisites}</textarea></label>
      <label class="field"><span>${t('admin.word_save_dir')}</span>
        <input name="word_save_dir" maxlength="400" placeholder="D:\\NURMED\\Ҳужжатлар" value="${s.word_save_dir || ''}" ${can('admin') ? '' : raw('disabled')}>
        <span class="hint">${can('admin') ? t('admin.word_save_dir_hint') : t('admin.word_save_dir_admin')}</span></label>
      <label class="field"><span>${t('admin.print_mode')}</span>
        <select name="print_mode">
          <option value="word" ${s.print_mode !== 'browser' ? raw('selected') : ''}>${t('admin.print_word')}</option>
          <option value="browser" ${s.print_mode === 'browser' ? raw('selected') : ''}>${t('admin.print_browser')}</option>
        </select>
        <span class="hint">${t('admin.print_hint')}</span></label>
      <div class="field"><span>${t('admin.logo')}</span>
        <div class="logo-edit">
          <img id="logo-prev" class="${s.clinic_logo ? '' : 'hidden'}" src="${s.clinic_logo || ''}" alt="">
          <input type="file" id="logo" accept="image/png,image/jpeg,image/webp">
          <button type="button" class="btn btn--ghost btn--sm" id="logo-rm">${t('delete')}</button>
        </div>
        <span class="hint">${t('admin.logo_hint')}</span>
      </div>
      <button class="btn">${t('save')}</button>
    </form>`);
  const f = $('#sf', el);
  let logo = s.clinic_logo || '';
  const prev = $('#logo-prev', el);
  $('#logo', el).onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      logo = await shrinkImage(file);
      prev.src = logo; prev.classList.remove('hidden');
    } catch { toast(t('admin.logo_big'), 'err'); e.target.value = ''; }
  };
  $('#logo-rm', el).onclick = () => { logo = ''; prev.classList.add('hidden'); $('#logo', el).value = ''; };
  f.onsubmit = async (e) => {
    e.preventDefault();
    await busy(e.submitter, async () => {
      const body = Object.fromEntries(['clinic_ministry', 'clinic_name', 'clinic_subtitle', 'clinic_services', 'clinic_address', 'clinic_phone',
        'clinic_telegram', 'clinic_instagram', 'clinic_requisites'].map((k) => [k, f.elements[k].value.trim()]));
      if (can('admin')) body.word_save_dir = f.elements.word_save_dir.value.trim();
      state.settings = await PUT('/api/settings', { ...body, print_mode: f.elements.print_mode.value, clinic_logo: logo });
      document.dispatchEvent(new Event('nurmed:settings'));
      toast(t('saved'));
    });
  };
}

/* ---------- Xodimlar ---------- */
async function users(el) {
  const list = await GET('/api/users');
  render(el, html`
    <section class="card">
      <div class="actions"><button class="btn" id="add">+ ${t('admin.add_user')}</button></div>
      <table class="table"><thead><tr><th>${t('f.full_name')}</th><th>${t('f.username')}</th><th>${t('admin.roles')}</th><th>${t('f.phone')}</th><th>${t('status')}</th><th></th></tr></thead>
      <tbody>${list.map((u) => html`<tr class="${u.active ? '' : 'row--voided'}"><td>${u.full_name}</td><td>${u.username}</td>
        <td>${u.roles.map((r) => t('role.' + r)).join(', ')}</td><td>${u.phone}</td>
        <td>${u.active ? t('admin.active') : t('admin.inactive')}${u.must_change_password ? html`<div class="muted small">${t('admin.must_change')}</div>` : ''}</td>
        <td class="row-actions"><button class="btn btn--ghost btn--sm" data-edit="${u.id}">${t('edit')}</button>
          ${u.id !== state.user.id ? html`<button class="btn btn--danger btn--sm" data-del="${u.id}">${t('delete')}</button>` : ''}</td></tr>`)}</tbody></table>
      <p class="hint">${t('admin.roles_hint')}</p>
    </section>`);
  $('#add', el).onclick = () => userDialog(null);
  $$('[data-edit]', el).forEach((b) => { b.onclick = () => userDialog(list.find((u) => u.id === Number(b.dataset.edit))); });
  $$('[data-del]', el).forEach((b) => {
    b.onclick = async () => {
      const u = list.find((x) => x.id === Number(b.dataset.del));
      if (!(await confirmDialog(t('admin.delete_user_confirm', { name: u.full_name }), { danger: true, okText: t('delete') }))) return;
      await busy(b, async () => { await POST(`/api/users/${u.id}/delete`); toast(t('hist.deleted')); refresh(); });
    };
  });
}

function userDialog(u) {
  const isNew = !u;
  u = u || { roles: [], active: 1 };
  modal(html`
    <form class="form dialog__body">
      <h2>${isNew ? t('admin.add_user') : u.full_name}</h2>
      <label class="field"><span>${t('f.full_name')} *</span><input name="full_name" required maxlength="200" value="${u.full_name || ''}"></label>
      <label class="field"><span>${t('f.username')} *</span><input name="username" required pattern="[a-zA-Z0-9._\\-]{3,60}" value="${u.username || ''}" ${isNew ? '' : raw('disabled')}></label>
      <label class="field"><span>${t('f.phone')}</span><input name="phone" maxlength="30" value="${u.phone || ''}"></label>
      <fieldset class="field"><legend>${t('admin.roles')} *</legend>
        ${ROLES.map((r) => html`<label class="inline"><input type="checkbox" name="roles" value="${r}" ${u.roles.includes(r) ? raw('checked') : ''}> ${t('role.' + r)}</label>`)}
      </fieldset>
      <label class="field"><span>${isNew ? t('f.password') + ' *' : t('admin.reset_password')}</span>
        <input name="password" type="text" minlength="8" maxlength="200" autocomplete="new-password" ${isNew ? raw('required') : ''}>
        <span class="hint">${t('admin.password_hint')}</span></label>
      ${isNew ? '' : html`<label class="inline"><input type="checkbox" name="active" ${u.active ? raw('checked') : ''}> ${t('admin.active')}</label>`}
      <div class="dialog__actions"><button type="button" class="btn btn--ghost" data-close>${t('cancel')}</button><button class="btn">${t('save')}</button></div>
    </form>`, (dlg, close) => {
    const f = $('form', dlg);
    f.onsubmit = async (e) => {
      e.preventDefault();
      const roles = $$('input[name=roles]:checked', f).map((i) => i.value);
      if (!roles.length) { toast(t('err.required') + ` (${t('admin.roles')})`, 'err'); return; }
      const body = { full_name: f.elements.full_name.value.trim(), phone: f.elements.phone.value.trim(), roles };
      if (f.elements.password.value) body.password = f.elements.password.value;
      await busy(e.submitter, async () => {
        if (isNew) await POST('/api/users', { ...body, username: f.elements.username.value.trim() });
        else await PUT(`/api/users/${u.id}`, { ...body, active: f.elements.active.checked });
        toast(t('saved'));
        close();
        refresh();
      });
    };
  });
}

/* ---------- Xizmatlar katalogi ---------- */
const groupOptions = (sel) => ['', ...window.PRICING.GROUPS].map((g) => html`<option value="${g}" ${g === (sel || '') ? raw('selected') : ''}>${t('pg.' + (g || 'none'))}</option>`);

async function services(el) {
  const list = await GET('/api/services?all=1');
  const row = (s) => html`<tr data-id="${s.id}">
    <td><input name="name" maxlength="200" value="${s.name}" required></td>
    <td class="num"><input name="price" class="num-input" inputmode="numeric" value="${s.price}" required></td>
    <td><select name="price_group">${groupOptions(s.price_group)}</select></td>
    <td><label class="inline"><input type="checkbox" name="active" ${s.active ? raw('checked') : ''}> ${t('admin.active')}</label></td>
    <td class="row-actions"><button class="btn btn--sm" data-save>${t('save')}</button>
      <button class="btn btn--danger btn--sm" data-del>${t('delete')}</button></td></tr>`;
  render(el, html`
    <section class="card">
      <div class="actions"><button class="btn" id="add-svc">+ ${t('cash.add_service')}</button></div>
      ${list.length ? html`<table class="table"><thead><tr><th>${t('cash.service')}</th><th class="num">${t('cash.price')} (${t('sum')})</th><th>${t('admin.price_group')}</th><th>${t('status')}</th><th></th></tr></thead>
        <tbody id="svc">${list.map(row)}</tbody></table>` : html`<p class="muted">${t('empty')}</p>`}
      <p class="hint">${t('admin.services_hint')}</p>
      <p class="hint">${t('admin.price_group_hint')}</p>
    </section>`);
  const readPrice = (v) => Number(String(v).replace(/\s/g, ''));
  $('#add-svc', el).onclick = () => modal(html`
    <form class="form dialog__body">
      <h2>${t('cash.add_service')}</h2>
      <label class="field"><span>${t('cash.service')} *</span><input name="name" required maxlength="200"></label>
      <label class="field"><span>${t('cash.price')} (${t('sum')}) *</span><input name="price" required inputmode="numeric" class="num-input"></label>
      <label class="field"><span>${t('admin.price_group')}</span><select name="price_group">${groupOptions('')}</select></label>
      <div class="dialog__actions"><button type="button" class="btn btn--ghost" data-close>${t('cancel')}</button><button class="btn">${t('save')}</button></div>
    </form>`, (dlg, close) => {
    const f = $('form', dlg);
    setTimeout(() => f.elements.name.focus(), 0);
    f.onsubmit = async (e) => {
      e.preventDefault();
      const price = readPrice(f.elements.price.value);
      if (!f.elements.name.value.trim() || !Number.isInteger(price) || price < 0) { toast(t('err.invalid'), 'err'); return; }
      await busy(e.submitter, async () => {
        await POST('/api/services', { name: f.elements.name.value.trim(), price, active: true, price_group: f.elements.price_group.value });
        toast(t('saved')); close(); refresh();
      });
    };
  });
  const tbody = $('#svc', el);
  if (!tbody) return;
  tbody.addEventListener('click', async (e) => {
    const b = e.target.closest('[data-save], [data-del]');
    if (!b) return;
    const tr = b.closest('tr');
    const get = (n) => $(`[name=${n}]`, tr);
    if (b.hasAttribute('data-del')) {
      if (!(await confirmDialog(t('admin.delete_service_confirm', { name: get('name').value }), { danger: true, okText: t('delete') }))) return;
      await busy(b, async () => { await POST(`/api/services/${tr.dataset.id}/delete`); toast(t('hist.deleted')); refresh(); });
      return;
    }
    const price = readPrice(get('price').value);
    if (!get('name').value.trim() || !Number.isInteger(price) || price < 0) { toast(t('err.invalid'), 'err'); return; }
    await busy(b, async () => {
      await PUT(`/api/services/${tr.dataset.id}`, { name: get('name').value.trim(), price, active: get('active').checked, price_group: get('price_group').value });
      toast(t('saved'));
      refresh();
    });
  });
}

/* ---------- Audit jurnali ---------- */
async function audit(el, query) {
  const f = { date: query.get('date') || '', action: query.get('action') || '', page: Number(query.get('page')) || 1 };
  const load = async (o) => {
    const d = await GET('/api/audit' + qs(o));
    render(el, html`
      <form class="filters card" id="af">
        <label class="inline">${t('date')}: <input type="date" name="date" value="${o.date}"></label>
        <input name="action" value="${o.action}" placeholder="${t('admin.action_ph')}">
        <button class="btn">${t('search')}</button>
      </form>
      <section class="card"><table class="table table--compact"><thead><tr><th>${t('time')}</th><th>${t('admin.user')}</th><th>${t('admin.action')}</th>
        <th>${t('admin.object')}</th><th>${t('admin.details')}</th><th>IP</th></tr></thead>
        <tbody>${d.rows.map((a) => html`<tr><td>${fmtDateTime(a.at)}</td><td>${a.user_name || '—'}</td><td><code>${a.action}</code></td>
          <td>${a.entity}${a.entity_id ? ' #' + a.entity_id : ''}</td><td class="details"><code>${a.details === '{}' ? '' : a.details}</code></td><td>${a.ip}</td></tr>`)}</tbody></table>
        <div id="pg"></div></section>`);
    $('#pg', el).appendChild(pager(d, (pg) => load({ ...o, page: pg })));
    const form = $('#af', el);
    form.onsubmit = (e) => { e.preventDefault(); load({ date: form.elements.date.value, action: form.elements.action.value.trim(), page: 1 }); };
  };
  await load(f);
}

/* ---------- Zaxira nusxalari ---------- */
async function backup(el) {
  const list = await GET('/api/backups');
  const size = (n) => (n > 1048576 ? (n / 1048576).toFixed(1) + ' MB' : Math.ceil(n / 1024) + ' KB');
  render(el, html`
    <section class="card">
      <p>${t('admin.backup_info')}</p>
      <div class="actions"><button class="btn" id="mk">${t('admin.backup_now')}</button></div>
      <table class="table"><thead><tr><th>${t('admin.file')}</th><th>${t('date')}</th><th class="num">${t('admin.size')}</th><th></th></tr></thead>
        <tbody>${list.map((b) => html`<tr><td><code>${b.name}</code></td><td>${fmtDateTime(b.created)}</td><td class="num">${size(b.size)}</td>
          <td class="row-actions"><a class="btn btn--ghost btn--sm" href="/api/backups/${encodeURIComponent(b.name)}" download>${t('admin.download')}</a>
            <button class="btn btn--danger btn--sm" data-del="${b.name}">${t('delete')}</button></td></tr>`)}</tbody></table>
      <div class="alert alert--warn">${t('admin.backup_warn')}</div>
    </section>`);
  $('#mk', el).onclick = (e) => busy(e.target, async () => { await POST('/api/backups'); toast(t('saved')); refresh(); });
  $$('[data-del]', el).forEach((b) => {
    b.onclick = async () => {
      if (!(await confirmDialog(t('admin.delete_backup_confirm', { name: b.dataset.del }), { danger: true, okText: t('delete') }))) return;
      await busy(b, async () => { await POST(`/api/backups/${encodeURIComponent(b.dataset.del)}/delete`); toast(t('hist.deleted')); refresh(); });
    };
  });
}
