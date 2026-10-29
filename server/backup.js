'use strict';
/*
 * Zaxira nusxalari: data/backups/ papkasiga SQLite bazaning to'liq nusxasi yoziladi.
 * Server ishlab turganda ham xavfsiz (SQLite online backup API).
 */
const fs = require('node:fs');
const path = require('node:path');
const sqlite = require('node:sqlite');
const { db, DATA_DIR, nowLocal } = require('./db');
const { HttpError } = require('./http');

const DIR = process.env.NURMED_BACKUP_DIR || path.join(DATA_DIR, 'backups');
const KEEP = Number(process.env.NURMED_BACKUP_KEEP || 30);
const NAME_RE = /^nurmed-\d{8}-\d{6}-(auto|manual)\.db$/;

fs.mkdirSync(DIR, { recursive: true });

async function create(kind = 'auto') {
  const stamp = nowLocal().replace(/[-:]/g, '').replace(' ', '-');
  const name = `nurmed-${stamp}-${kind}.db`;
  const file = path.join(DIR, name);
  await sqlite.backup(db, file);
  prune();
  const st = fs.statSync(file);
  return { name, size: st.size, created: nowLocal(st.mtime) };
}

function list() {
  return fs.readdirSync(DIR).filter((n) => NAME_RE.test(n)).sort().reverse().map((name) => {
    const st = fs.statSync(path.join(DIR, name));
    return { name, size: st.size, created: nowLocal(st.mtime) };
  });
}

function prune() {
  const files = fs.readdirSync(DIR).filter((n) => NAME_RE.test(n) && n.endsWith('-auto.db')).sort().reverse();
  for (const n of files.slice(KEEP)) fs.unlinkSync(path.join(DIR, n));
}

function resolve(name) {
  if (!NAME_RE.test(name)) throw new HttpError(400, 'invalid');
  const file = path.join(DIR, name);
  if (!fs.existsSync(file)) throw new HttpError(404, 'not_found');
  return file;
}

function stream(file, res, name) {
  res.writeHead(200, {
    'Content-Type': 'application/octet-stream',
    'Content-Disposition': `attachment; filename="${name}"`,
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
  });
  fs.createReadStream(file).pipe(res);
}

/** Har 24 soatda avtomatik nusxa. Ishga tushganda oxirgi nusxa 24 soatdan eski bo'lsa, darhol olinadi. */
function schedule(log = console) {
  const DAY = 24 * 3600 * 1000;
  const run = () => create('auto').then((i) => log.log(`[backup] ${i.name}`)).catch((e) => log.error('[backup] xato:', e.message));
  const autos = fs.readdirSync(DIR).filter((n) => NAME_RE.test(n)).map((n) => fs.statSync(path.join(DIR, n)).mtimeMs);
  const last = autos.length ? Math.max(...autos) : 0;
  if (Date.now() - last > DAY) run();
  const t = setInterval(run, DAY);
  t.unref();
}

module.exports = { create, list, resolve, stream, schedule, DIR };
