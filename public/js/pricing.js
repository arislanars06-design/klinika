/*
 * NURMED: kassadagi paket chegirmalari. Brauzer (window.PRICING) va server (require) bir xil hisoblaydi.
 *
 * Har bir xizmatning "chegirma guruhi" (services.price_group) bor:
 *   lor_exam  — ЛОР кўриги
 *   lor_proc  — муолажалар: томоқ (бодомча) ювиш, бурун ювиш, қулоқ тозалаш, лимфотроп блокада
 *   inj_drip  — томчилатиб юбориш (капельница)
 *   inj_iv    — вена ичига секин юбориш
 *   inj_im    — мушак орасига / тери орасига юбориш
 *
 * 1) ЛОР кўриги + муолажалар (муолажалар сони n, миқдорлари қўшилади):
 *      n = 1  → 70 000
 *      n = 2  → 100 000
 *      n ≥ 3  → 100 000 + (n − 2) × 35 000      (масалан, n = 3 → 135 000)
 *    Пакетга битта ЛОР кўриги киради. ЛОР кўригисиз муолажалар оддий нархда.
 *
 * 2) Уколлар (донабай нарх):
 *      капельница: 1 та → 25 000, 2 та ва ундан кўп → ҳар бири 20 000
 *      венадан секин: ёлғиз ва битта бўлса → 15 000;
 *                     2 та ва кўп бўлса ёки капельница / мушак орасига билан бирга → ҳар бири 10 000
 *      (масалан, 1 капельница + 1 венадан секин = 25 000 + 10 000 = 35 000)
 *      мушак / тери орасига → каталог нархи
 *
 * Чегирма = каталог нархи бўйича сумма − пакет нархи (манфий бўлмайди).
 * Нархлар ўзгарса, қуйидаги RULES қийматларини ўзгартиринг.
 */
(function (root, factory) {
  const P = factory();
  if (typeof module === 'object' && module.exports) module.exports = P;
  else root.PRICING = P;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const GROUPS = ['lor_exam', 'lor_proc', 'inj_drip', 'inj_iv', 'inj_im'];

  const RULES = {
    lorPackage: { one: 70000, two: 100000, eachNext: 35000 },
    drip: { single: 25000, multi: 20000 },
    iv: { single: 15000, combined: 10000 },
  };

  /** n ta muolaja bilan LOR ko'rigi paketi narxi */
  function lorPackagePrice(n) {
    const r = RULES.lorPackage;
    if (n <= 0) return null;
    if (n === 1) return r.one;
    return r.two + (n - 2) * r.eachNext;
  }

  /**
   * items: [{ price_group, unit_price, qty, name }]
   * Natija: { subtotal, discount, total, lines: [{ uz, ru, amount }] }
   */
  function calculate(items) {
    const list = (Array.isArray(items) ? items : []).filter((i) => i && i.qty > 0);
    const subtotal = list.reduce((a, i) => a + i.unit_price * i.qty, 0);
    const by = (g) => list.filter((i) => i.price_group === g);
    const qtyOf = (arr) => arr.reduce((a, i) => a + i.qty, 0);
    const sumOf = (arr) => arr.reduce((a, i) => a + i.unit_price * i.qty, 0);
    const lines = [];

    // 1) LOR ko'rigi + muolajalar
    const exams = by('lor_exam');
    const procs = by('lor_proc');
    const n = qtyOf(procs);
    if (exams.length && n > 0) {
      const examUnit = Math.max(...exams.map((e) => e.unit_price));
      const normal = examUnit + sumOf(procs);
      const pkg = lorPackagePrice(n);
      const d = normal - pkg;
      if (d > 0) {
        lines.push({
          uz: `ЛОР кўриги + ${n} та муолажа = ${fmt(pkg)}`,
          ru: `ЛОР-осмотр + процедур: ${n} = ${fmt(pkg)}`,
          amount: d,
        });
      }
    }

    // 2) Ukollar
    const drips = by('inj_drip');
    const ivs = by('inj_iv');
    const ims = by('inj_im');
    const dq = qtyOf(drips);
    const vq = qtyOf(ivs);
    const mq = qtyOf(ims);
    if (dq || vq) {
      const dripUnit = dq >= 2 ? RULES.drip.multi : RULES.drip.single;
      const ivUnit = vq >= 2 || dq > 0 || mq > 0 ? RULES.iv.combined : RULES.iv.single;
      const normal = sumOf(drips) + sumOf(ivs);
      const pkg = dq * dripUnit + vq * ivUnit;
      const d = normal - pkg;
      if (d > 0) {
        const parts = [];
        if (dq) parts.push({ uz: `${dq} капельница × ${fmt(dripUnit)}`, ru: `${dq} капельница × ${fmt(dripUnit)}` });
        if (vq) parts.push({ uz: `${vq} венадан секин × ${fmt(ivUnit)}`, ru: `${vq} в/в медленно × ${fmt(ivUnit)}` });
        lines.push({ uz: `Уколлар: ${parts.map((p) => p.uz).join(', ')}`, ru: `Инъекции: ${parts.map((p) => p.ru).join(', ')}`, amount: d });
      }
    }

    const discount = Math.min(subtotal, lines.reduce((a, l) => a + l.amount, 0));
    return { subtotal, discount, total: subtotal - discount, lines };
  }

  function fmt(n) {
    return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  }

  return { GROUPS, RULES, calculate, lorPackagePrice };
});
