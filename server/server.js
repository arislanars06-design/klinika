'use strict';
/*
 * NURMED server. Klinikaning lokal tarmog'idagi bitta (markaziy) kompyuterda ishga tushiriladi.
 * Boshqa kompyuterlar brauzer orqali http://<server-IP>:3000 manzilini ochadi.
 */
const fs = require('node:fs');
const http = require('node:http');
const https = require('node:https');
const path = require('node:path');
const { URL } = require('node:url');

const { HttpError, json, parseCookies, serveStatic } = require('./http');
const sec = require('./security');
const { router } = require('./routes');
const backup = require('./backup');
const { DB_PATH } = require('./db');

const PORT = Number(process.env.PORT || 3000);
const HOST = process.env.HOST || '0.0.0.0';
const PUBLIC_DIR = path.resolve(__dirname, '..', 'public');
const TLS_CERT = process.env.NURMED_TLS_CERT;
const TLS_KEY = process.env.NURMED_TLS_KEY;
const SECURE = !!(TLS_CERT && TLS_KEY);
const COOKIE = 'nurmed_session';

async function handle(req, res) {
  const url = new URL(req.url, 'http://localhost');
  const pathname = url.pathname;

  if (!pathname.startsWith('/api/')) {
    if (req.method !== 'GET' && req.method !== 'HEAD') return json(res, 405, { error: 'method_not_allowed' });
    return serveStatic(PUBLIC_DIR, req, res, pathname);
  }

  const cookies = parseCookies(req);
  const token = cookies[COOKIE] || '';
  const extraHeaders = {};
  const ctx = {
    req, res, url, query: url.searchParams, params: {}, token,
    ip: req.socket.remoteAddress || '',
    user: sec.userFromToken(token),
    setSession(t) {
      extraHeaders['Set-Cookie'] = `${COOKIE}=${t}; HttpOnly; SameSite=Strict; Path=/; Max-Age=${Math.floor(sec.SESSION_MS / 1000)}${SECURE ? '; Secure' : ''}`;
    },
    clearSession() {
      extraHeaders['Set-Cookie'] = `${COOKIE}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0${SECURE ? '; Secure' : ''}`;
    },
  };

  try {
    // CSRF himoyasi: o'zgartiruvchi so'rovlar faqat ilovaning o'zidan (maxsus sarlavha bilan) qabul qilinadi
    if (req.method !== 'GET' && req.headers['x-nurmed'] !== '1') throw new HttpError(403, 'csrf');

    const m = router.match(req.method, pathname);
    if (m === 'method') throw new HttpError(405, 'method_not_allowed');
    if (!m) throw new HttpError(404, 'not_found');
    ctx.params = m.params;
    const result = await m.handler(ctx);
    if (result !== undefined) json(res, 200, result, extraHeaders);
  } catch (e) {
    if (e instanceof HttpError) {
      json(res, e.status, { error: e.code, ...(e.extra || {}) }, extraHeaders);
    } else {
      console.error(new Date().toISOString(), req.method, pathname, e);
      json(res, 500, { error: 'server_error' });
    }
  }
}

const server = SECURE
  ? https.createServer({ cert: fs.readFileSync(TLS_CERT), key: fs.readFileSync(TLS_KEY) }, handle)
  : http.createServer(handle);

server.requestTimeout = 30000;

const pw = sec.ensureAdmin();
server.listen(PORT, HOST, () => {
  console.log(`NURMED ishga tushdi: ${SECURE ? 'https' : 'http'}://${HOST === '0.0.0.0' ? '<server-IP>' : HOST}:${PORT}`);
  console.log(`Baza fayli: ${DB_PATH}`);
  console.log(`Zaxira nusxalar: ${backup.DIR}`);
  if (pw) {
    console.log('\n================ BIRINCHI ISHGA TUSHIRISH ================');
    console.log('Administrator login: admin');
    console.log(`Vaqtinchalik parol: ${pw}`);
    console.log('Birinchi kirishda parolni almashtirish talab qilinadi.');
    console.log('==========================================================\n');
  }
});

backup.schedule();
setInterval(() => sec.purgeExpiredSessions(), 3600 * 1000).unref();

for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => { server.close(); process.exit(0); });
}
