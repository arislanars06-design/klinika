/*
 * NURMED — LOR shablonlari (shikoyatlar, LOR STATUS, tashxislar ro‘yxati).
 * Bu fayl brauzerda ham (window.LOR), serverda ham (require) ishlatiladi.
 * Server saqlashdan oldin kelgan ma’lumotni shu shablon bo‘yicha tekshiradi.
 *
 * Muhim: hech bir maydon avtomatik "norma" deb to‘ldirilmaydi.
 * Tanlanmagan maydon = tekshirilmagan / qayd etilmagan.
 */
(function (root, factory) {
  const T = factory();
  if (typeof module === 'object' && module.exports) module.exports = T;
  else root.LOR = T;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const o = (code, uz, ru) => ({ code, uz, ru });

  const COMPLAINTS = [
    {
      group: 'nose', uz: 'Burun', ru: 'Нос', items: [
        o('nasal_congestion', 'Burun bitishi', 'Заложенность носа'),
        o('nasal_discharge', 'Burundan ajralma', 'Выделения из носа'),
        o('smell_loss', 'Hid bilish pasayishi', 'Снижение обоняния'),
        o('sneezing', 'Aksirish', 'Чихание'),
        o('epistaxis', 'Burundan qon ketishi', 'Носовое кровотечение'),
        o('snoring', 'Xurrak otish', 'Храп'),
        o('facial_pain', 'Yuz sohasida og‘riq yoki bosim', 'Боль или давление в области лица'),
        o('postnasal', 'Tomoqqa shilliq oqishi', 'Стекание слизи по задней стенке глотки'),
      ],
    },
    {
      group: 'throat', uz: 'Tomoq', ru: 'Горло', items: [
        o('sore_throat', 'Tomoq og‘rig‘i', 'Боль в горле'),
        o('odynophagia', 'Yutishda og‘riq', 'Боль при глотании'),
        o('throat_dryness', 'Tomoqda quruqlik, qichishish', 'Сухость, першение в горле'),
        o('hoarseness', 'Ovoz bo‘g‘ilishi', 'Осиплость голоса'),
        o('cough', 'Yo‘tal', 'Кашель'),
        o('globus', 'Tomoqda yot jism hissi', 'Ощущение кома в горле'),
        o('bad_breath', 'Og‘izdan noxush hid', 'Неприятный запах изо рта'),
      ],
    },
    {
      group: 'ear', uz: 'Quloq', ru: 'Ухо', items: [
        o('ear_pain', 'Quloq og‘rig‘i', 'Боль в ухе'),
        o('hearing_loss', 'Eshitish pasayishi', 'Снижение слуха'),
        o('ear_discharge', 'Quloqdan ajralma', 'Выделения из уха'),
        o('tinnitus', 'Quloqda shovqin', 'Шум в ухе'),
        o('ear_fullness', 'Quloq bitishi', 'Заложенность уха'),
        o('ear_itch', 'Quloq qichishishi', 'Зуд в ухе'),
      ],
    },
    {
      group: 'general', uz: 'Umumiy', ru: 'Общие', items: [
        o('headache', 'Bosh og‘rig‘i', 'Головная боль'),
        o('fever', 'Tana harorati ko‘tarilishi', 'Повышение температуры'),
        o('weakness', 'Holsizlik', 'Слабость'),
        o('dizziness', 'Bosh aylanishi', 'Головокружение'),
      ],
    },
  ];

  // Umumiy variantlar
  const NONE = o('none', 'Yo‘q', 'Нет');
  const MUCOUS = o('mucous', 'Shilliq', 'Слизистое');
  const PURULENT = o('purulent', 'Yiringli', 'Гнойное');
  const HYPEREMIC = o('hyperemic', 'Giperemiyalangan', 'Гиперемия');
  const EDEMATOUS = o('edematous', 'Shishgan', 'Отёк');
  const PINK = o('pink', 'Pushti, nam', 'Розовая, влажная');
  const UNCHANGED = o('normal', 'O‘zgarishsiz', 'Без изменений');
  const NOT_FOUND = o('none', 'Aniqlanmadi', 'Не выявлены');

  // sided: true — o‘ng (r) va chap (l) tomon alohida qayd etiladi
  const SECTIONS = [
    {
      key: 'rhinoscopy', uz: 'Rinoskopiya', ru: 'Риноскопия', fields: [
        { key: 'external_nose', sided: false, uz: 'Tashqi burun', ru: 'Наружный нос', options: [
          UNCHANGED, o('deformed', 'Deformatsiyalangan', 'Деформирован'), o('swelling', 'Shish', 'Отёк'),
          o('tender', 'Paypaslaganda og‘riqli', 'Болезненность при пальпации'),
        ] },
        { key: 'septum', sided: false, uz: 'Burun to‘sig‘i', ru: 'Носовая перегородка', options: [
          o('midline', 'O‘rta chiziqda', 'По средней линии'),
          o('dev_right', 'O‘ngga qiyshaygan', 'Искривлена вправо'),
          o('dev_left', 'Chapga qiyshaygan', 'Искривлена влево'),
          o('s_shaped', 'S-simon qiyshaygan', 'S-образное искривление'),
          o('spur', 'Tikan / qirra', 'Шип / гребень'),
          o('perforation', 'Perforatsiya', 'Перфорация'),
        ] },
        { key: 'passages', sided: true, uz: 'Burun yo‘llari', ru: 'Носовые ходы', options: [
          o('free', 'Erkin', 'Свободные'), o('narrowed', 'Toraygan', 'Сужены'),
          o('discharge', 'Ajralma bor', 'Есть отделяемое'), o('polyps', 'Poliplar', 'Полипы'),
        ] },
        { key: 'mucosa', sided: true, uz: 'Shilliq qavat', ru: 'Слизистая оболочка', options: [
          PINK, HYPEREMIC, EDEMATOUS, o('pale', 'Oqish / ko‘kimtir', 'Бледная / синюшная'),
          o('atrophic', 'Atrofik', 'Атрофична'),
        ] },
        { key: 'turbinates', sided: true, uz: 'Pastki burun chig‘anoqlari', ru: 'Нижние носовые раковины', options: [
          UNCHANGED, o('hypertrophic', 'Gipertrofiyalangan', 'Гипертрофированы'), EDEMATOUS,
          o('contract', 'Vazokonstriktordan qisqaradi', 'Сокращаются на вазоконстриктор'),
        ] },
        { key: 'discharge', sided: true, uz: 'Ajralma', ru: 'Отделяемое', options: [
          NONE, MUCOUS, PURULENT, o('mucopurulent', 'Shilliq-yiringli', 'Слизисто-гнойное'),
          o('watery', 'Suvsimon', 'Водянистое'), o('bloody', 'Qon aralash', 'Кровянистое'),
        ] },
        { key: 'breathing', sided: true, uz: 'Burun nafasi', ru: 'Носовое дыхание', options: [
          o('free', 'Erkin', 'Свободное'), o('difficult', 'Qiyinlashgan', 'Затруднено'),
          o('absent', 'Yo‘q', 'Отсутствует'),
        ] },
        { key: 'smell', sided: true, uz: 'Hid bilish', ru: 'Обоняние', options: [
          o('preserved', 'Saqlangan', 'Сохранено'), o('reduced', 'Pasaygan (giposmiya)', 'Снижено (гипосмия)'),
          o('absent', 'Yo‘q (anosmiya)', 'Отсутствует (аносмия)'),
        ] },
      ],
    },
    {
      key: 'otoscopy', uz: 'Otoskopiya', ru: 'Отоскопия', fields: [
        { key: 'auricle', sided: true, uz: 'Quloq suprasi', ru: 'Ушная раковина', options: [
          UNCHANGED, o('tragus_pain', 'Tragusga bosganda og‘riq', 'Боль при надавливании на козелок'),
          o('swelling', 'Shish', 'Отёк'),
        ] },
        { key: 'canal', sided: true, uz: 'Tashqi eshituv yo‘li', ru: 'Наружный слуховой проход', options: [
          o('wide', 'Keng, erkin', 'Широкий, свободный'), o('narrowed', 'Toraygan', 'Сужен'),
          HYPEREMIC, EDEMATOUS, o('cerumen', 'Oltingugurt tiqini', 'Серная пробка'),
          o('foreign_body', 'Yot jism', 'Инородное тело'), o('fungal', 'Zamburug‘li massalar', 'Грибковые массы'),
        ] },
        { key: 'tm', sided: true, uz: 'Nog‘ora parda', ru: 'Барабанная перепонка', options: [
          o('grey', 'Kulrang, yaltiroq', 'Серая, блестящая'),
          o('landmarks', 'Tanib olish belgilari aniq', 'Опознавательные знаки чёткие'),
          o('dull', 'Xira', 'Мутная'), HYPEREMIC,
          o('retracted', 'Ichkariga tortilgan', 'Втянута'), o('bulging', 'Bo‘rtib chiqqan', 'Выбухает'),
          o('perforation', 'Perforatsiya', 'Перфорация'), o('scarring', 'Chandiqli o‘zgarishlar', 'Рубцовые изменения'),
        ] },
        { key: 'discharge', sided: true, uz: 'Ajralma', ru: 'Отделяемое', options: [
          NONE, o('serous', 'Seroz', 'Серозное'), MUCOUS, PURULENT, o('bloody', 'Qon aralash', 'Кровянистое'),
        ] },
        { key: 'pathology', sided: true, uz: 'Patologik o‘zgarishlar', ru: 'Патологические изменения', options: [
          NOT_FOUND, o('granulation', 'Granulyatsiyalar', 'Грануляции'), o('polyp', 'Polip', 'Полип'),
          o('cholesteatoma', 'Xolesteatoma', 'Холестеатома'),
        ] },
        { key: 'hearing', sided: true, uz: 'Eshitish (shivirli nutq)', ru: 'Слух (шёпотная речь)', options: [
          o('normal', 'Saqlangan (6 m)', 'Сохранён (6 м)'), o('reduced', 'Pasaygan', 'Снижен'),
        ] },
      ],
    },
    {
      key: 'oropharyngoscopy', uz: 'Orofaringoskopiya', ru: 'Орофарингоскопия', fields: [
        { key: 'mucosa', sided: false, uz: 'Halqum shilliq qavati', ru: 'Слизистая глотки', options: [
          PINK, HYPEREMIC, EDEMATOUS, o('dry', 'Quruq', 'Сухая'), o('atrophic', 'Atrofik', 'Атрофична'),
          o('granular', 'Orqa devor granulyar', 'Задняя стенка гранулёзная'),
        ] },
        { key: 'tonsils', sided: true, uz: 'Tanglay bodomcha bezlari', ru: 'Нёбные миндалины', options: [
          o('size1', 'I daraja', 'I степени'), o('size2', 'II daraja', 'II степени'), o('size3', 'III daraja', 'III степени'),
          o('behind_arches', 'Ravoqlar orqasida', 'За дужками'), HYPEREMIC, o('loose', 'G‘ovak', 'Рыхлые'),
          o('plugs', 'Lakunalarda yiringli tiqinlar', 'Гнойные пробки в лакунах'),
          o('exudate', 'Karash', 'Налёт'), o('adhesions', 'Ravoqlar bilan bitishmalar', 'Спайки с дужками'),
        ] },
        { key: 'arches', sided: false, uz: 'Tanglay ravoqlari', ru: 'Нёбные дужки', options: [
          UNCHANGED, HYPEREMIC, o('thickened', 'Qirralari qalinlashgan', 'Валикообразное утолщение краёв'), EDEMATOUS,
        ] },
        { key: 'discharge', sided: false, uz: 'Ajralma va karash', ru: 'Отделяемое и налёт', options: [
          NONE, MUCOUS, PURULENT, o('exudate', 'Karash', 'Налёт'),
        ] },
      ],
    },
    {
      key: 'laryngoscopy', uz: 'Laringoskopiya', ru: 'Ларингоскопия', fields: [
        { key: 'epiglottis', sided: false, uz: 'Hiqildoq usti tog‘ayi', ru: 'Надгортанник', options: [
          UNCHANGED, EDEMATOUS, HYPEREMIC,
        ] },
        { key: 'mucosa', sided: false, uz: 'Hiqildoq shilliq qavati', ru: 'Слизистая гортани', options: [
          o('pink', 'Pushti', 'Розовая'), HYPEREMIC, EDEMATOUS, o('infiltrated', 'Infiltratsiyalangan', 'Инфильтрирована'),
        ] },
        { key: 'cords', sided: true, uz: 'Ovoz boylamlari', ru: 'Голосовые складки', options: [
          o('white', 'Oq, qirralari tekis', 'Белые, края ровные'), HYPEREMIC, o('thickened', 'Qalinlashgan', 'Утолщены'),
          o('nodules', 'Tugunchalar', 'Узелки'), o('polyp', 'Polip', 'Полип'),
          o('leukoplakia', 'Leykoplakiya', 'Лейкоплакия'), o('mass', 'Hosila', 'Новообразование'),
        ] },
        { key: 'mobility', sided: true, uz: 'Ovoz boylamlari harakatchanligi', ru: 'Подвижность голосовых складок', options: [
          o('full', 'To‘liq', 'В полном объёме'), o('limited', 'Cheklangan', 'Ограничена'),
          o('immobile', 'Harakatsiz', 'Неподвижна'),
        ] },
        { key: 'glottis', sided: false, uz: 'Ovoz yorig‘i', ru: 'Голосовая щель', options: [
          o('closure_full', 'To‘liq yopiladi', 'Смыкание полное'),
          o('closure_incomplete', 'To‘liq yopilmaydi', 'Смыкание неполное'),
          o('wide', 'Keng', 'Широкая'), o('narrowed', 'Toraygan', 'Сужена'),
        ] },
        { key: 'pathology', sided: false, uz: 'Patologik o‘zgarishlar', ru: 'Патологические изменения', options: [
          NOT_FOUND,
        ] },
      ],
    },
  ];

  // Tez tanlash uchun tashxislar (XKT-10). Shifokor istalgan matnni ham yozishi mumkin.
  const DIAGNOSES = [
    o('J00', 'O‘tkir nazofaringit', 'Острый назофарингит'),
    o('J01', 'O‘tkir sinusit', 'Острый синусит'),
    o('J02', 'O‘tkir faringit', 'Острый фарингит'),
    o('J03', 'O‘tkir tonzillit', 'Острый тонзиллит'),
    o('J04.0', 'O‘tkir laringit', 'Острый ларингит'),
    o('J30', 'Vazomotor va allergik rinit', 'Вазомоторный и аллергический ринит'),
    o('J31.0', 'Surunkali rinit', 'Хронический ринит'),
    o('J31.2', 'Surunkali faringit', 'Хронический фарингит'),
    o('J32', 'Surunkali sinusit', 'Хронический синусит'),
    o('J33', 'Burun polipi', 'Полип носа'),
    o('J34.2', 'Burun to‘sig‘i qiyshiqligi', 'Искривление носовой перегородки'),
    o('J35.0', 'Surunkali tonzillit', 'Хронический тонзиллит'),
    o('J35.2', 'Adenoidlar gipertrofiyasi', 'Гипертрофия аденоидов'),
    o('J37.0', 'Surunkali laringit', 'Хронический ларингит'),
    o('J38.1', 'Ovoz boylami polipi', 'Полип голосовой складки'),
    o('H60', 'Tashqi otit', 'Наружный отит'),
    o('H61.2', 'Oltingugurt tiqini', 'Серная пробка'),
    o('H65', 'Yiringsiz o‘rta otit', 'Негнойный средний отит'),
    o('H66', 'Yiringli o‘rta otit', 'Гнойный средний отит'),
    o('H68', 'Yevstaxiit', 'Евстахиит'),
    o('H72', 'Nog‘ora parda perforatsiyasi', 'Перфорация барабанной перепонки'),
    o('H90', 'Eshitish pasayishi', 'Тугоухость'),
    o('H93.1', 'Quloqda shovqin (tinnitus)', 'Шум в ушах'),
    o('R04.0', 'Burundan qon ketishi', 'Носовое кровотечение'),
  ];

  const COMPLAINT_CODES = new Set();
  COMPLAINTS.forEach((g) => g.items.forEach((i) => COMPLAINT_CODES.add(i.code)));

  const cleanText = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : '');

  function cleanCodes(arr, allowed) {
    if (!Array.isArray(arr)) return [];
    const out = [];
    for (const c of arr) if (typeof c === 'string' && allowed.has(c) && !out.includes(c)) out.push(c);
    return out;
  }

  /** Faqat shablonda mavjud bo‘lim/maydon/variantlarni qoldiradi. Bo‘sh maydonlar tashlab yuboriladi. */
  function sanitizeLor(input) {
    const src = input && typeof input === 'object' ? input : {};
    const out = {};
    for (const s of SECTIONS) {
      const sIn = src[s.key] && typeof src[s.key] === 'object' ? src[s.key] : {};
      const fIn = sIn.fields && typeof sIn.fields === 'object' ? sIn.fields : {};
      const fields = {};
      for (const f of s.fields) {
        const v = fIn[f.key] && typeof fIn[f.key] === 'object' ? fIn[f.key] : {};
        const allowed = new Set(f.options.map((x) => x.code));
        const res = {};
        if (f.sided) {
          const r = cleanCodes(v.r, allowed);
          const l = cleanCodes(v.l, allowed);
          if (r.length) res.r = r;
          if (l.length) res.l = l;
        } else {
          const vv = cleanCodes(v.v, allowed);
          if (vv.length) res.v = vv;
        }
        const text = cleanText(v.text, 500);
        if (text) res.text = text;
        if (Object.keys(res).length) fields[f.key] = res;
      }
      const note = cleanText(sIn.note, 2000);
      if (Object.keys(fields).length || note) out[s.key] = { fields, note };
    }
    return out;
  }

  function sanitizeComplaints(arr) {
    return cleanCodes(arr, COMPLAINT_CODES);
  }

  function complaintLabel(code, lang) {
    for (const g of COMPLAINTS) for (const i of g.items) if (i.code === code) return i[lang] || i.uz;
    return code;
  }

  return { COMPLAINTS, SECTIONS, DIAGNOSES, sanitizeLor, sanitizeComplaints, complaintLabel };
});
