'use strict';
const crypto = require('node:crypto');
const { db, nowLocal } = require('./db');

const SESSION_HOURS = Number(process.env.NURMED_SESSION_HOURS || 12);
const SESSION_MS = SESSION_HOURS * 3600 * 1000;

/* ---------- Rollar va huquqlar ---------- */
const ROLES = ['admin', 'doctor', 'registrar', 'cashier'];

const PERMISSIONS = {
  'patient.read': ['admin', 'doctor', 'registrar', 'cashier'],
  'patient.write': ['admin', 'doctor', 'registrar'],
  'visit.list': ['admin', 'doctor', 'registrar', 'cashier'],
  'visit.create': ['doctor', 'registrar'],
  'visit.clinical.read': ['admin', 'doctor'],
  'visit.clinical.write': ['doctor'],
  'visit.cancel': ['admin', 'doctor'],
  'billing.read': ['admin', 'cashier'],
  'billing.write': ['admin', 'cashier'],
  'report.visits': ['admin', 'doctor'],
  'report.finance': ['admin', 'cashier'],
  'export': ['admin', 'doctor'],
  'admin': ['admin'],
};

function permissionsFor(roles) {
  return Object.keys(PERMISSIONS).filter((p) => PERMISSIONS[p].some((r) => roles.includes(r)));
}

function can(user, perm) {
  return !!user && user.perms.includes(perm);
}

/* ---------- Parollar (scrypt) ---------- */
function hashPassword(password) {
  const salt = crypto.randomBytes(16);
  const key = crypto.scryptSync(password, salt, 64, { N: 16384, r: 8, p: 1 });
  return `scrypt$${salt.toString('base64')}$${key.toString('base64')}`;
}

function verifyPassword(password, stored) {
  const [alg, saltB64, keyB64] = String(stored).split('$');
  if (alg !== 'scrypt' || !saltB64 || !keyB64) return false;
  const expected = Buffer.from(keyB64, 'base64');
  const key = crypto.scryptSync(password, Buffer.from(saltB64, 'base64'), expected.length, { N: 16384, r: 8, p: 1 });
  return crypto.timingSafeEqual(key, expected);
}

function validatePasswordStrength(pw) {
  return typeof pw === 'string' && pw.length >= 8 && pw.length <= 200;
}

/* ---------- Sessiyalar ---------- */
const sha256 = (s) => crypto.createHash('sha256').update(s).digest('hex');

function createSession(userId) {
  const token = crypto.randomBytes(32).toString('base64url');
  db.prepare('INSERT INTO sessions(token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)')
    .run(sha256(token), userId, nowLocal(), Date.now() + SESSION_MS);
  return token;
}

function destroySession(token) {
  if (token) db.prepare('DELETE FROM sessions WHERE token_hash = ?').run(sha256(token));
}

function destroyUserSessions(userId) {
  db.prepare('DELETE FROM sessions WHERE user_id = ?').run(userId);
}

function loadUser(row) {
  const roles = JSON.parse(row.roles || '[]');
  return {
    id: row.id, username: row.username, full_name: row.full_name, phone: row.phone,
    roles, perms: permissionsFor(roles), must_change_password: !!row.must_change_password,
  };
}

function userFromToken(token) {
  if (!token) return null;
  const row = db.prepare(`
    SELECT u.*, s.expires_at FROM sessions s JOIN users u ON u.id = s.user_id
    WHERE s.token_hash = ?`).get(sha256(token));
  if (!row) return null;
  if (row.expires_at < Date.now() || !row.active) {
    destroySession(token);
    return null;
  }
  return loadUser(row);
}

function purgeExpiredSessions() {
  db.prepare('DELETE FROM sessions WHERE expires_at < ?').run(Date.now());
}

/* ---------- Kirishga urinishlarni cheklash ---------- */
const attempts = new Map(); // key -> { count, until }
const MAX_ATTEMPTS = 5;
const LOCK_MS = 5 * 60 * 1000;

function isLocked(key) {
  const a = attempts.get(key);
  return !!a && a.until > Date.now();
}
function registerFailure(key) {
  const a = attempts.get(key) || { count: 0, until: 0 };
  a.count += 1;
  if (a.count >= MAX_ATTEMPTS) { a.until = Date.now() + LOCK_MS; a.count = 0; }
  attempts.set(key, a);
}
function clearFailures(key) { attempts.delete(key); }

/* ---------- Audit ---------- */
function audit(user, action, entity = '', entityId = null, details = {}, ip = '') {
  db.prepare('INSERT INTO audit_logs(at, user_id, action, entity, entity_id, details, ip) VALUES (?, ?, ?, ?, ?, ?, ?)')
    .run(nowLocal(), user ? user.id : null, action, entity, entityId, JSON.stringify(details), ip);
}

/* ---------- Birinchi ishga tushirish: administrator ---------- */
function ensureAdmin() {
  const c = db.prepare('SELECT COUNT(*) AS c FROM users').get().c;
  if (c > 0) return null;
  const password = crypto.randomBytes(9).toString('base64url');
  db.prepare(`INSERT INTO users(username, password_hash, full_name, roles, active, must_change_password, created_at)
              VALUES ('admin', ?, 'Administrator', '["admin"]', 1, 1, ?)`).run(hashPassword(password), nowLocal());
  return password;
}

module.exports = {
  ROLES, PERMISSIONS, permissionsFor, can,
  hashPassword, verifyPassword, validatePasswordStrength,
  createSession, destroySession, destroyUserSessions, userFromToken, loadUser, purgeExpiredSessions,
  isLocked, registerFailure, clearFailures, audit, ensureAdmin, SESSION_MS,
};
