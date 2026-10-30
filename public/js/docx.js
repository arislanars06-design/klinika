// NURMED: chop etiladigan hujjatni Word (.docx) fayliga aylantirish.
// Chop etish uchun tayyorlangan HTML (.doc) olinadi va A5 o'lchamli Word hujjati yasaladi.
// Tashqi kutubxona ishlatilmaydi: .docx bu XML fayllardan iborat ZIP arxiv.

const MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
const enc = new TextEncoder();

// Sahifa o'lchamlari (twip = 1/1440 dyuym). A5 — hujjatlar, A4 yotiq — jadval ko'rinishidagi ro'yxatlar.
const PAGES = {
  a5: { w: 8391, h: 11906, margin: 510, top: 454, font: 17 },          // 148 × 210 mm, chetlari ≈ 9 mm, 8.5 pt
  a4l: { w: 16838, h: 11906, margin: 567, top: 567, font: 16, landscape: true }, // 297 × 210 mm, 8 pt
};
let TABLE_SZ = 16;
let CONTENT_W = PAGES.a5.w - 2 * PAGES.a5.margin;

/* ---------------- ZIP (siqmasdan, "stored") ---------------- */
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(b) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < b.length; i++) c = CRC_TABLE[(c ^ b[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}
function zip(files) {
  const parts = [];
  const central = [];
  let offset = 0;
  for (const f of files) {
    const name = enc.encode(f.name);
    const data = typeof f.data === 'string' ? enc.encode(f.data) : f.data;
    const crc = crc32(data);
    const lh = new DataView(new ArrayBuffer(30));
    lh.setUint32(0, 0x04034b50, true); lh.setUint16(4, 20, true); lh.setUint16(6, 0x0800, true);
    lh.setUint16(12, 0x21, true); // 1980-01-01
    lh.setUint32(14, crc, true); lh.setUint32(18, data.length, true); lh.setUint32(22, data.length, true);
    lh.setUint16(26, name.length, true);
    parts.push(new Uint8Array(lh.buffer), name, data);
    const ch = new DataView(new ArrayBuffer(46));
    ch.setUint32(0, 0x02014b50, true); ch.setUint16(4, 20, true); ch.setUint16(6, 20, true); ch.setUint16(8, 0x0800, true);
    ch.setUint16(14, 0x21, true);
    ch.setUint32(16, crc, true); ch.setUint32(20, data.length, true); ch.setUint32(24, data.length, true);
    ch.setUint16(28, name.length, true); ch.setUint32(42, offset, true);
    central.push(new Uint8Array(ch.buffer), name);
    offset += 30 + name.length + data.length;
  }
  const cdSize = central.reduce((a, b) => a + b.length, 0);
  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); end.setUint16(8, files.length, true); end.setUint16(10, files.length, true);
  end.setUint32(12, cdSize, true); end.setUint32(16, offset, true);
  return new Blob([...parts, ...central, new Uint8Array(end.buffer)], { type: MIME });
}

/* ---------------- WordprocessingML ---------------- */
// eslint-disable-next-line no-control-regex
const xmlEsc = (s) => String(s).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function runXml(r, base = {}) {
  if (r.br) return '<w:r><w:br/></w:r>';
  if (r.tab) return '<w:r><w:tab/></w:r>';
  if (r.img) return r.img;
  const b = r.b ?? base.b;
  const i = r.i ?? base.i;
  const sz = r.sz ?? base.sz;
  const pr = `${b ? '<w:b/>' : ''}${i ? '<w:i/>' : ''}${r.gray ? '<w:color w:val="555555"/>' : ''}${sz ? `<w:sz w:val="${sz}"/><w:szCs w:val="${sz}"/>` : ''}`;
  return `<w:r>${pr ? `<w:rPr>${pr}</w:rPr>` : ''}<w:t xml:space="preserve">${xmlEsc(r.t)}</w:t></w:r>`;
}

/** Paragraf. opts: align, b, i, sz, before, after, border ('bottom'), tabRight, keepNext */
function P(runs, opts = {}) {
  const ppr = [
    opts.keepNext ? '<w:keepNext/>' : '',
    opts.border ? '<w:pBdr><w:bottom w:val="single" w:sz="8" w:space="2" w:color="000000"/></w:pBdr>' : '',
    opts.tabRight ? `<w:tabs><w:tab w:val="right" w:pos="${CONTENT_W}"/></w:tabs>` : '',
    `<w:spacing w:before="${opts.before || 0}" w:after="${opts.after ?? 10}"/>`,
    opts.align ? `<w:jc w:val="${opts.align}"/>` : '',
  ].join('');
  return `<w:p><w:pPr>${ppr}</w:pPr>${tidy(runs).map((r) => runXml(r, opts)).join('')}</w:p>`;
}

/** Bo'shliqlarni HTML kabi siqish: ketma-ket bo'shliqlar bitta bo'ladi, boshi va oxiri kesiladi */
function tidy(runs) {
  const out = [];
  let prevSpace = true;
  for (const r of runs) {
    if (r.br || r.tab || r.img) { out.push(r); prevSpace = true; continue; }
    let t = r.pre ? r.t : r.t.replace(/\s+/g, ' ');
    if (prevSpace && !r.pre) t = t.replace(/^ /, '');
    if (!t) continue;
    prevSpace = /\s$/.test(t);
    out.push({ ...r, t });
  }
  for (let k = out.length - 1; k >= 0; k--) {
    const r = out[k];
    if (r.br || r.tab || r.img) break;
    r.t = r.t.replace(/\s+$/, '');
    if (r.t) break;
    out.splice(k, 1);
  }
  return out;
}

/* ---------------- HTML → runlar ---------------- */
function inline(node, st = {}, out = []) {
  for (const c of node.childNodes) {
    if (c.nodeType === 3) { out.push({ t: c.textContent, ...st }); continue; }
    if (c.nodeType !== 1) continue;
    const tag = c.tagName;
    if (tag === 'BR') { out.push({ br: true }); continue; }
    if (tag === 'IMG' || c.classList.contains('hidden')) continue;
    const s = { ...st };
    if (tag === 'B' || tag === 'STRONG' || tag === 'TH') s.b = true;
    if (tag === 'I' || tag === 'EM') s.i = true;
    if (c.classList.contains('doc__ear')) { s.b = true; s.i = true; }
    if (c.classList.contains('muted')) s.gray = true;
    if (c.classList.contains('small')) s.sz = 15;
    if (c.classList.contains('pre')) { out.push(...preRuns(c, s)); continue; }
    inline(c, s, out);
  }
  return out;
}

/** Ko'p qatorli matn (.pre): har bir qator alohida, orasida qator ko'chirish */
function preRuns(el, st = {}) {
  const lines = el.textContent.replace(/\r/g, '').trim().split('\n');
  const out = [];
  lines.forEach((l, i) => { if (i) out.push({ br: true }); out.push({ ...st, t: l, pre: true }); });
  return out;
}

const BLOCK_TAGS = new Set(['DIV', 'P', 'TABLE', 'DL', 'H2', 'H3', 'H4', 'HEADER', 'FOOTER', 'SECTION', 'ARTICLE']);
const hasBlocks = (el) => [...el.children].some((x) => BLOCK_TAGS.has(x.tagName));
const contentRuns = (el) => (el.classList.contains('pre') ? preRuns(el) : inline(el));

/* ---------------- Hujjat qismlari ---------------- */
/** Bemor ma'lumotlari: chegarasiz ikki ustunli ixcham jadval (Ф.И.Ш. to'liq qatorda) */
function patientTable(cells) {
  const half = Math.floor(CONTENT_W / 2);
  const cell = (c, span) => `<w:tc><w:tcPr><w:tcW w:w="${span ? CONTENT_W : half}" w:type="dxa"/>${span ? '<w:gridSpan w:val="2"/>' : ''}</w:tcPr>${P(c ? inline(c) : [], { after: 0 })}</w:tc>`;
  const rows = [];
  const rest = [];
  for (const c of cells) {
    if (c.classList.contains('doc__wide')) rows.push(`<w:tr>${cell(c, true)}</w:tr>`);
    else rest.push(c);
  }
  for (let i = 0; i < rest.length; i += 2) rows.push(`<w:tr>${cell(rest[i])}${cell(rest[i + 1])}</w:tr>`);
  return `<w:tbl><w:tblPr><w:tblW w:w="${CONTENT_W}" w:type="dxa"/><w:tblLayout w:type="fixed"/>`
    + '<w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="57" w:type="dxa"/></w:tblCellMar></w:tblPr>'
    + `<w:tblGrid><w:gridCol w:w="${half}"/><w:gridCol w:w="${half}"/></w:tblGrid>${rows.join('')}</w:tbl>${P([], { after: 30, sz: 6 })}`;
}

function table(t) {
  const rows = [...t.rows];
  const n = Math.max(...rows.map((r) => r.cells.length));
  const colW = Math.floor(CONTENT_W / n);
  const border = '<w:top w:val="single" w:sz="4" w:color="777777"/><w:left w:val="single" w:sz="4" w:color="777777"/>'
    + '<w:bottom w:val="single" w:sz="4" w:color="777777"/><w:right w:val="single" w:sz="4" w:color="777777"/>'
    + '<w:insideH w:val="single" w:sz="4" w:color="777777"/><w:insideV w:val="single" w:sz="4" w:color="777777"/>';
  const body = rows.map((r) => `<w:tr>${[...r.cells].map((c) => `<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>${
    P(inline(c), { after: 0, sz: TABLE_SZ, b: c.tagName === 'TH', align: c.classList.contains('num') ? 'right' : undefined })}</w:tc>`).join('')}</w:tr>`).join('');
  return `<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>${border}</w:tblBorders>`
    + '<w:tblCellMar><w:left w:w="57" w:type="dxa"/><w:right w:w="57" w:type="dxa"/></w:tblCellMar></w:tblPr>'
    + `<w:tblGrid>${Array.from({ length: n }, () => `<w:gridCol w:w="${colW}"/>`).join('')}</w:tblGrid>${body}</w:tbl>`
    + P([], { after: 30, sz: 6 });
}

/** LOR STATUS metodi: "Риноскопия: Ташқи бурун: …; Шиллиқ қават: …". Jadval (эшитиш, вестибуляр паспорт) alohida. */
function lor(el, out) {
  const h = el.querySelector(':scope > h4');
  let runs = h ? [{ t: h.textContent + ': ', b: true }] : [];
  let groups = 0;
  let titled = false; // sarlavha allaqachon chiqarildimi
  const flush = (keepNext) => {
    if (runs.length) out.push(P(runs, keepNext ? { keepNext: true } : {}));
    titled = true; runs = []; groups = 0;
  };
  for (const c of el.children) {
    if (c === h) continue;
    if (c.tagName === 'TABLE') { flush(!groups); out.push(table(c)); continue; }
    if (c.classList.contains('doc__grp')) {
      if (groups) runs.push({ t: '. ' });
      const ear = c.querySelector(':scope > .doc__ear');
      if (ear) runs.push({ t: ear.textContent.trim() + ' ', b: true, i: true });
      [...c.querySelectorAll(':scope > .doc__ln')].forEach((ln, li) => {
        if (li) runs.push({ t: '; ' });
        runs.push(...inline(ln));
      });
      groups += 1;
      continue;
    }
    if (c.classList.contains('pre')) { flush(false); out.push(P(preRuns(c))); }
  }
  if (groups || !titled) flush(false);
}

/** Bo'lim: sarlavha birinchi matn bilan bir qatorda ("АНАМНЕЗ: …"), qolganlari alohida paragraf */
function block(el, out) {
  if (el.classList.contains('doc__patient')) {
    out.push(patientTable([...el.children]));
    return;
  }
  const h = el.querySelector(':scope > h3');
  let heading = h ? [{ t: h.textContent.trim().toUpperCase() + ': ', b: true }] : null;
  const flush = () => { if (heading) { out.push(P(heading, { keepNext: true })); heading = null; } };
  for (const c of el.children) {
    if (c === h) continue;
    if (c.classList.contains('doc__lor')) { flush(); lor(c, out); continue; }
    if (c.tagName === 'TABLE') { flush(); out.push(table(c)); continue; }
    if (hasBlocks(c)) { flush(); blocks(c, out); continue; }
    const runs = contentRuns(c);
    if (heading) { out.push(P([...heading, ...runs])); heading = null; } else out.push(P(runs));
  }
  flush();
}

function header(el, out, media) {
  const img = el.querySelector('img');
  const name = el.querySelector('.doc__clinic');
  const reqs = [...el.querySelectorAll('.doc__req')].filter((r) => r.textContent.trim());
  const logo = img ? logoRun(img, media) : null;
  out.push(P([...(logo ? [logo, { t: '  ' }] : []), ...(name ? inline(name) : [])], { b: true, sz: 21, after: 0, border: !reqs.length }));
  reqs.forEach((r, i) => out.push(P(inline(r), { sz: 14, after: 0, border: i === reqs.length - 1 })));
  out.push(P([], { after: 20, sz: 6 }));
}

function logoRun(img, media) {
  const m = /^data:image\/(png|jpeg);base64,(.+)$/.exec(img.getAttribute('src') || '');
  if (!m) return null; // WEBP va boshqalarni Word har doim ham ochmaydi
  const bin = atob(m[2]);
  const data = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) data[i] = bin.charCodeAt(i);
  const ext = m[1] === 'png' ? 'png' : 'jpeg';
  media.push({ name: `word/media/logo.${ext}`, data, ext });
  const nw = img.naturalWidth || 1;
  const nh = img.naturalHeight || 1;
  const scale = Math.min(36 / nh, 110 / nw);
  const cx = Math.round(nw * scale * 9525);
  const cy = Math.round(nh * scale * 9525);
  return {
    img: `<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="${cx}" cy="${cy}"/><wp:docPr id="1" name="Logo"/>`
      + '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
      + '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="0" name="logo"/><pic:cNvPicPr/></pic:nvPicPr>'
      + '<pic:blipFill><a:blip r:embed="rIdLogo"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
      + `<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="${cx}" cy="${cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>`
      + '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>',
  };
}

function totals(dl, out) {
  const kids = [...dl.children];
  for (let i = 0; i < kids.length; i += 2) {
    const big = kids[i].classList.contains('totals__big');
    out.push(P([...inline(kids[i]), { t: '  ' }, ...(kids[i + 1] ? inline(kids[i + 1]) : [])], { align: 'right', after: 0, b: big || undefined }));
  }
  out.push(P([], { after: 40 }));
}

function footer(el, out) {
  let first = true;
  for (const c of el.children) {
    const before = first ? 140 : 0;
    first = false;
    if (c.classList.contains('doc__foot-row')) {
      const [a, b] = c.children;
      out.push(P([...(a ? inline(a) : []), { tab: true }, ...(b ? inline(b) : [])], { tabRight: true, before }));
    } else out.push(P(inline(c), { before }));
  }
}

function blocks(el, out, media) {
  for (const c of el.children) {
    const cl = c.classList;
    if (cl.contains('hidden')) continue;
    if (cl.contains('doc__head')) header(c, out, media);
    else if (cl.contains('doc__title')) out.push(P(inline(c).map((r) => ({ ...r, t: r.t && r.t.toUpperCase() })), { align: 'center', b: true, sz: 19, after: 60 }));
    else if (cl.contains('doc__block')) block(c, out);
    else if (c.tagName === 'TABLE') out.push(table(c));
    else if (c.tagName === 'DL') totals(c, out);
    else if (c.tagName === 'FOOTER' || cl.contains('doc__foot')) footer(c, out);
    else if (cl.contains('doc__sign')) out.push(P(inline(c), { before: 200 }));
    else if (hasBlocks(c)) blocks(c, out, media);
    else out.push(P(contentRuns(c)));
  }
}

/** Chop etish uchun tayyorlangan hujjat elementidan (.doc) Word fayli (Blob) */
export function docToDocx(docEl, pageName = 'a5') {
  const pg = PAGES[pageName] || PAGES.a5;
  CONTENT_W = pg.w - 2 * pg.margin;
  TABLE_SZ = pg.landscape ? pg.font : 16;
  const media = [];
  const body = [];
  blocks(docEl, body, media);
  const document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    + '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    + ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    + ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"><w:body>'
    + body.join('')
    + `<w:sectPr><w:pgSz w:w="${pg.w}" w:h="${pg.h}"${pg.landscape ? ' w:orient="landscape"' : ''}/><w:pgMar w:top="${pg.top}" w:right="${pg.margin}" w:bottom="${pg.margin}" w:left="${pg.margin}" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>`
    + '</w:body></w:document>';
  const styles = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    + '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults>'
    + `<w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial" w:eastAsia="Arial"/><w:sz w:val="${pg.font}"/><w:szCs w:val="${pg.font}"/><w:lang w:val="uz-Cyrl-UZ"/></w:rPr></w:rPrDefault>`
    + '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="228" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
    + '</w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style></w:styles>';
  const rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    + media.map((m) => `<Relationship Id="rIdLogo" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo.${m.ext}"/>`).join('')
    + '</Relationships>';
  const types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    + '<Default Extension="xml" ContentType="application/xml"/>'
    + '<Default Extension="png" ContentType="image/png"/><Default Extension="jpeg" ContentType="image/jpeg"/>'
    + '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    + '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    + '</Types>';
  const root = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    + '</Relationships>';
  return zip([
    { name: '[Content_Types].xml', data: types },
    { name: '_rels/.rels', data: root },
    { name: 'word/document.xml', data: document },
    { name: 'word/styles.xml', data: styles },
    { name: 'word/_rels/document.xml.rels', data: rels },
    ...media.slice(0, 1).map((m) => ({ name: m.name, data: m.data })),
  ]);
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

/** Fayl nomi uchun xavfsiz matn: "Алиев Али 29.10.2026" → "Алиев_Али_29.10.2026" */
export const safeName = (s) => String(s).replace(/[\\/:*?"<>|\u0000-\u001F]/g, '').trim().replace(/\s+/g, '_').slice(0, 120) || 'hujjat';
