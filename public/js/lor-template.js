/*
 * NURMED: LOR shablonlari (shikoyatlar, ajralma turlari, LOR STATUS, tashxislar).
 * Shikoyatlar va LOR STATUS katalogi eski "Clinic LOR Desktop" dasturidan
 * (src/clinic/catalogs/*.json) ko‘chirilgan, o‘zbekcha matnlar lotin yozuviga o‘girilgan.
 *
 * Bu fayl brauzerda (window.LOR) ham, serverda (require) ham ishlatiladi.
 * Server saqlashdan oldin kelgan ma’lumotni shu shablon bo‘yicha tekshiradi.
 *
 * Muhim: hech bir maydon avtomatik "norma" deb to‘ldirilmaydi.
 * Tanlanmagan maydon tekshirilmagan (qayd etilmagan) hisoblanadi.
 * "is_norm" belgisi faqat ma’lumot sifatida saqlangan.
 *
 * Qabul yozuvidagi ma’lumot shakli:
 *   complaints: [{ code, discharge?, discharge_text? }]
 *   lor_status: {
 *     rhinoscopy:  { parts: { external_nose: { state: 'deformed', deformity_type: ['hump'], side: 'left', _text: '...' } }, note },
 *     otoscopy:    { ears: { AD: { <qism>: {...} }, AS: {...} }, note },
 *   }
 * Maydon turlari: radio → kod, checkbox_multi → [kodlar], side → left|right|both,
 *                 degree → none|I|II|III, checkbox → true.
 */
(function (root, factory) {
  const T = factory();
  if (typeof module === 'object' && module.exports) module.exports = T;
  else root.LOR = T;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const CATALOG = {
   "complaints": [
    {
     "code": "general",
     "uz": "Umumiy shikoyatlar",
     "ru": "Общие жалобы",
     "items": [
      {
       "code": "gen_headache",
       "uz": "Bosh og‘rig‘i",
       "ru": "Головная боль"
      },
      {
       "code": "gen_fever_subfebrile",
       "uz": "Isitma (subfebril)",
       "ru": "Температура (субфебрильная)"
      },
      {
       "code": "gen_fever_febrile",
       "uz": "Isitma (febril)",
       "ru": "Температура (фебрильная)"
      },
      {
       "code": "gen_fever_pyretic",
       "uz": "Isitma (piretik)",
       "ru": "Температура (пиретическая)"
      },
      {
       "code": "gen_weakness",
       "uz": "Umumiy holsizlik",
       "ru": "Общая слабость"
      },
      {
       "code": "gen_dizziness",
       "uz": "Bosh aylanishi",
       "ru": "Головокружение"
      },
      {
       "code": "gen_nausea",
       "uz": "Ko‘ngil aynishi",
       "ru": "Тошнота"
      },
      {
       "code": "gen_vomiting",
       "uz": "Qusish",
       "ru": "Рвота"
      },
      {
       "code": "gen_diarrhea",
       "uz": "Ich ketishi",
       "ru": "Диарея"
      },
      {
       "code": "gen_joint_pain",
       "uz": "Bo‘g‘imlarda og‘riq",
       "ru": "Боль в суставах"
      },
      {
       "code": "gen_back_pain",
       "uz": "Bel sohasida og‘riq",
       "ru": "Боль в поясничной области"
      }
     ]
    },
    {
     "code": "ear",
     "uz": "Quloq",
     "ru": "Уши",
     "items": [
      {
       "code": "ear_cosmetic",
       "uz": "Quloq suprasida kosmetik nuqson (shalpang quloqlik, deformatsiya, o‘sma, otogematoma)",
       "ru": "Ушная раковина — косметический дефект (лопоухость, деформация, новообразование, отогематома)"
      },
      {
       "code": "ear_pain",
       "uz": "Quloqda og‘riq",
       "ru": "Боль в ухе"
      },
      {
       "code": "ear_noise",
       "uz": "Quloqda shovqin",
       "ru": "Шум в ушах"
      },
      {
       "code": "ear_hearing_loss",
       "uz": "Eshitish pasayishi",
       "ru": "Снижение слуха"
      },
      {
       "code": "ear_congestion",
       "uz": "Quloq bitishi",
       "ru": "Заложенность уха"
      },
      {
       "code": "ear_discharge",
       "uz": "Quloqdan ajralma kelishi",
       "ru": "Выделения из уха",
       "has_discharge_type": true
      },
      {
       "code": "ear_itching",
       "uz": "Quloqda qichishish",
       "ru": "Зуд в ухе"
      },
      {
       "code": "ear_discomfort",
       "uz": "Quloqda noqulaylik hissi",
       "ru": "Чувство дискомфорта"
      }
     ]
    },
    {
     "code": "nose",
     "uz": "Burun va yondosh burun bo‘shliqlari",
     "ru": "Нос и околоносовые пазухи",
     "items": [
      {
       "code": "nose_cosmetic",
       "uz": "Kosmetik nuqson yoki hosila",
       "ru": "Косметический дефект, образования"
      },
      {
       "code": "nose_congestion",
       "uz": "Burun bitishi",
       "ru": "Заложенность носа"
      },
      {
       "code": "nose_breathing",
       "uz": "Burun orqali nafas olishning qiyinlashishi",
       "ru": "Затруднение дыхания через нос"
      },
      {
       "code": "nose_discharge",
       "uz": "Burundan ajralma kelishi",
       "ru": "Выделения из носа",
       "has_discharge_type": true
      },
      {
       "code": "nose_itching",
       "uz": "Burunda qichishish",
       "ru": "Зуд в носу"
      },
      {
       "code": "nose_pain",
       "uz": "Burun og‘rig‘i",
       "ru": "Боль в носу"
      },
      {
       "code": "nose_trigeminal_pain",
       "uz": "Uch shoxli nervning I–II shoxlari chiqish nuqtalarida og‘riq",
       "ru": "Болезненность точек выхода I–II ветвей тройничного нерва"
      },
      {
       "code": "nose_face_heaviness",
       "uz": "Yuz sohasida og‘irlik hissi",
       "ru": "Тяжесть в области лица"
      }
     ]
    },
    {
     "code": "pharynx",
     "uz": "Halqum",
     "ru": "Глотка",
     "items": [
      {
       "code": "pharynx_pain",
       "uz": "Tomoq og‘rig‘i",
       "ru": "Боль в горле"
      },
      {
       "code": "pharynx_tickling",
       "uz": "Qirilish yoki achishish hissi",
       "ru": "Першение"
      },
      {
       "code": "pharynx_itching",
       "uz": "Qichishish",
       "ru": "Зуд"
      },
      {
       "code": "pharynx_lump",
       "uz": "«Tomoqda tugun» hissi",
       "ru": "Чувство «комка»"
      },
      {
       "code": "pharynx_foreign_body",
       "uz": "«Begona jism» hissi",
       "ru": "Чувство инородного тела"
      },
      {
       "code": "pharynx_discharge",
       "uz": "Ajralma",
       "ru": "Отделяемое",
       "has_discharge_type": true
      },
      {
       "code": "pharynx_swallowing",
       "uz": "Yutishning qiyinlashishi",
       "ru": "Затрудненное глотание"
      },
      {
       "code": "pharynx_cough",
       "uz": "Yo‘tal",
       "ru": "Кашель"
      }
     ]
    },
    {
     "code": "larynx",
     "uz": "Hiqildoq",
     "ru": "Гортань",
     "items": [
      {
       "code": "larynx_voice_change",
       "uz": "Ovoz funksiyasining o‘zgarishi (xirillash, bo‘g‘ilish, ovoz yo‘qolishi)",
       "ru": "Изменение голосовой функции (охриплость, осиплость, афония)"
      },
      {
       "code": "larynx_cough",
       "uz": "Yo‘tal",
       "ru": "Кашель"
      },
      {
       "code": "larynx_pain",
       "uz": "Og‘riq",
       "ru": "Боль"
      },
      {
       "code": "larynx_foreign_body",
       "uz": "Begona jism hissi",
       "ru": "Чувство инородного тела"
      },
      {
       "code": "larynx_breathing",
       "uz": "Nafas olishning qiyinlashishi",
       "ru": "Затрудненное дыхание"
      },
      {
       "code": "larynx_swallowing",
       "uz": "Yutishning qiyinlashishi",
       "ru": "Затрудненное глотание"
      }
     ]
    }
   ],
   "discharge": [
    {
     "code": "purulent",
     "uz": "Yiringli",
     "ru": "Гнойное"
    },
    {
     "code": "serous",
     "uz": "Seroz",
     "ru": "Серозное"
    },
    {
     "code": "mucous",
     "uz": "Shilliq",
     "ru": "Слизистое"
    },
    {
     "code": "mucopurulent",
     "uz": "Shilliq-yiringli",
     "ru": "Слизисто-гнойное"
    },
    {
     "code": "bloody",
     "uz": "Qonli",
     "ru": "Кровянистое"
    },
    {
     "code": "sanguineous",
     "uz": "Suvli-qonli",
     "ru": "Сукровичное"
    },
    {
     "code": "caseous",
     "uz": "Kazeoz",
     "ru": "Казеозное"
    },
    {
     "code": "watery",
     "uz": "Suvli",
     "ru": "Водянистое"
    },
    {
     "code": "other",
     "uz": "Boshqa",
     "ru": "Другое",
     "requires_text": true
    }
   ],
   "sides": [
    {
     "code": "left",
     "uz": "Chapda",
     "ru": "Слева"
    },
    {
     "code": "right",
     "uz": "O‘ngda",
     "ru": "Справа"
    },
    {
     "code": "both",
     "uz": "Ikki tomonda",
     "ru": "С обеих сторон"
    }
   ],
   "degrees": [
    {
     "code": "none",
     "uz": "Yo‘q",
     "ru": "Нет",
     "is_norm": true
    },
    {
     "code": "I",
     "uz": "I daraja",
     "ru": "I ст."
    },
    {
     "code": "II",
     "uz": "II daraja",
     "ru": "II ст."
    },
    {
     "code": "III",
     "uz": "III daraja",
     "ru": "III ст."
    }
   ],
   "methods": [
    {
     "code": "rhinoscopy",
     "uz": "Rinoskopiya",
     "ru": "Риноскопия",
     "parts": [
      {
       "code": "external_nose",
       "uz": "Tashqi burun",
       "ru": "Наружный нос",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "unchanged",
           "uz": "O‘zgarmagan",
           "ru": "Не изменен",
           "is_norm": true
          },
          {
           "code": "deformed",
           "uz": "Deformatsiya",
           "ru": "Деформация"
          }
         ]
        },
        {
         "code": "deformity_type",
         "type": "checkbox_multi",
         "when": {
          "state": "deformed"
         },
         "options": [
          {
           "code": "sunken",
           "uz": "Cho‘kish",
           "ru": "Западение"
          },
          {
           "code": "hump",
           "uz": "Bukrilik",
           "ru": "Горбинка"
          },
          {
           "code": "scoliosis",
           "uz": "Skolioz",
           "ru": "Сколиоз"
          }
         ]
        },
        {
         "code": "side",
         "type": "side",
         "when": {
          "state": "deformed"
         }
        },
        {
         "code": "part",
         "type": "radio",
         "when": {
          "state": "deformed"
         },
         "options": [
          {
           "code": "bone",
           "uz": "Suyak qismi",
           "ru": "Костная часть"
          },
          {
           "code": "cartilage",
           "uz": "Tog‘ay qismi",
           "ru": "Хрящевая часть"
          }
         ]
        },
        {
         "code": "location",
         "type": "checkbox_multi",
         "when": {
          "state": "deformed"
         },
         "options": [
          {
           "code": "dorsum",
           "uz": "Burun orqasi",
           "ru": "Спинка"
          },
          {
           "code": "wings",
           "uz": "Qanotlari",
           "ru": "Крылья"
          },
          {
           "code": "tip",
           "uz": "Uchi",
           "ru": "Кончик"
          },
          {
           "code": "nostrils",
           "uz": "Burun teshiklari",
           "ru": "Ноздри"
          }
         ]
        }
       ]
      },
      {
       "code": "trigeminal",
       "uz": "Uch shoxli nerv chiqish nuqtalari",
       "ru": "Точки выхода тройничного нерва",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "painless",
           "uz": "Og‘riqsiz",
           "ru": "Безболезненны",
           "is_norm": true
          },
          {
           "code": "painful",
           "uz": "Og‘riqli",
           "ru": "Болезненны"
          }
         ]
        },
        {
         "code": "side",
         "type": "side",
         "when": {
          "state": "painful"
         }
        },
        {
         "code": "branch",
         "type": "checkbox_multi",
         "when": {
          "state": "painful"
         },
         "options": [
          {
           "code": "I",
           "uz": "I shox",
           "ru": "I ветвь"
          },
          {
           "code": "II",
           "uz": "II shox",
           "ru": "II ветвь"
          },
          {
           "code": "III",
           "uz": "III shox",
           "ru": "III ветвь"
          }
         ]
        }
       ]
      },
      {
       "code": "breathing",
       "uz": "Burun orqali nafas olish",
       "ru": "Дыхание через нос",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Erkin",
           "ru": "Свободное",
           "is_norm": true
          },
          {
           "code": "difficult",
           "uz": "Qiyinlashgan",
           "ru": "Затруднено"
          },
          {
           "code": "absent",
           "uz": "Mavjud emas",
           "ru": "Отсутствует"
          }
         ]
        },
        {
         "code": "side",
         "type": "side",
         "when": {
          "state": [
           "difficult",
           "absent"
          ]
         }
        }
       ]
      },
      {
       "code": "vestibule",
       "uz": "Burun dahlizi",
       "ru": "Преддверие",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "unchanged",
           "uz": "O‘zgarmagan",
           "ru": "Не изменено",
           "is_norm": true
          },
          {
           "code": "narrowed",
           "uz": "Toraygan",
           "ru": "Сужено"
          }
         ]
        },
        {
         "code": "side",
         "type": "side",
         "when": {
          "state": "narrowed"
         }
        }
       ]
      },
      {
       "code": "olfaction",
       "uz": "Hid bilish",
       "ru": "Обоняние",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "preserved",
           "uz": "Saqlangan",
           "ru": "Сохранено",
           "is_norm": true
          },
          {
           "code": "hyposmia",
           "uz": "Giposmiya",
           "ru": "Гипосмия"
          },
          {
           "code": "anosmia",
           "uz": "Anosmiya",
           "ru": "Аносмия"
          },
          {
           "code": "hyperosmia",
           "uz": "Giperosmiya",
           "ru": "Гиперосмия"
          }
         ]
        },
        {
         "code": "side",
         "type": "side",
         "when": {
          "state": [
           "hyposmia",
           "anosmia",
           "hyperosmia"
          ]
         }
        }
       ]
      },
      {
       "code": "mucosa",
       "uz": "Shilliq qavat",
       "ru": "Слизистая оболочка",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "pink",
           "uz": "Pushti",
           "ru": "Розовая",
           "is_norm": true
          },
          {
           "code": "pale_pink",
           "uz": "Oqartirilgan pushti",
           "ru": "Бледно-розовая"
          },
          {
           "code": "bluish",
           "uz": "Ko‘kimtir",
           "ru": "Синюшная"
          },
          {
           "code": "hyperemic",
           "uz": "Giperemiyalangan",
           "ru": "Гиперемирована"
          }
         ]
        },
        {
         "code": "moisture",
         "type": "radio",
         "options": [
          {
           "code": "moist",
           "uz": "Nam",
           "ru": "Влажная",
           "is_norm": true
          },
          {
           "code": "dry",
           "uz": "Quruq",
           "ru": "Сухая"
          }
         ]
        },
        {
         "code": "condition",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "hypertrophied",
           "uz": "Gipertrofiyalangan",
           "ru": "Гипертрофирована"
          },
          {
           "code": "ulcerated",
           "uz": "Yaralangan",
           "ru": "Изъязвлена"
          }
         ]
        },
        {
         "code": "location",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "septum",
           "uz": "Burun to‘sig‘i sohasi",
           "ru": "Область перегородки носа"
          },
          {
           "code": "turbinate_inferior",
           "uz": "Pastki chig‘anoq",
           "ru": "Нижняя носовая раковина"
          },
          {
           "code": "turbinate_middle",
           "uz": "O‘rta chig‘anoq",
           "ru": "Средняя носовая раковина"
          },
          {
           "code": "turbinate_superior",
           "uz": "Yuqori chig‘anoq",
           "ru": "Верхняя носовая раковина"
          },
          {
           "code": "meatus_inferior",
           "uz": "Pastki burun yo‘li",
           "ru": "Нижний носовой ход"
          },
          {
           "code": "meatus_middle",
           "uz": "O‘rta burun yo‘li",
           "ru": "Средний носовой ход"
          },
          {
           "code": "meatus_superior",
           "uz": "Yuqori burun yo‘li",
           "ru": "Верхний носовой ход"
          },
          {
           "code": "end_anterior",
           "uz": "Oldingi uchi",
           "ru": "Передний конец"
          },
          {
           "code": "end_posterior",
           "uz": "Orqa uchi",
           "ru": "Задний конец"
          }
         ]
        }
       ]
      },
      {
       "code": "septum",
       "uz": "Burun to‘sig‘i",
       "ru": "Носовая перегородка",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "midline",
           "uz": "O‘rta chiziqda",
           "ru": "По средней линии",
           "is_norm": true
          },
          {
           "code": "curved",
           "uz": "Qiyshaygan",
           "ru": "Искривлена"
          }
         ]
        },
        {
         "code": "features",
         "type": "checkbox_multi",
         "when": {
          "state": "curved"
         },
         "options": [
          {
           "code": "bulge",
           "uz": "Bo‘rtma",
           "ru": "Бугор"
          },
          {
           "code": "ridge",
           "uz": "Qirra",
           "ru": "Гребень"
          },
          {
           "code": "spike",
           "uz": "Tikancha",
           "ru": "Шип"
          }
         ]
        },
        {
         "code": "shape",
         "type": "radio",
         "when": {
          "state": "curved"
         },
         "options": [
          {
           "code": "c_shaped",
           "uz": "C-simon",
           "ru": "С-образно"
          },
          {
           "code": "s_shaped",
           "uz": "S-simon",
           "ru": "S-образно"
          }
         ]
        },
        {
         "code": "side",
         "type": "side",
         "when": {
          "state": "curved"
         }
        },
        {
         "code": "part",
         "type": "radio",
         "when": {
          "state": "curved"
         },
         "options": [
          {
           "code": "cartilage",
           "uz": "Tog‘ay qismida",
           "ru": "В хрящевом отделе"
          },
          {
           "code": "bone",
           "uz": "Suyak qismida",
           "ru": "В костном отделе"
          }
         ]
        }
       ]
      }
     ]
    },
    {
     "code": "pharyngoscopy",
     "uz": "Faringoskopiya",
     "ru": "Фарингоскопия",
     "parts": [
      {
       "code": "mouth_opening",
       "uz": "Og‘iz ochilishi",
       "ru": "Открывание рта",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Erkin",
           "ru": "Свободное",
           "is_norm": true
          },
          {
           "code": "trismus",
           "uz": "Trizm",
           "ru": "Тризм"
          },
          {
           "code": "painful",
           "uz": "Og‘riqli",
           "ru": "Болезненное"
          }
         ]
        }
       ]
      },
      {
       "code": "oral_mucosa",
       "uz": "Og‘iz shilliq qavati",
       "ru": "Слизистая оболочка полости рта",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "pale_pink",
           "uz": "Oqartirilgan pushti",
           "ru": "Бледно-розовая",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Giperemiyalangan",
           "ru": "Гиперемирована"
          }
         ]
        },
        {
         "code": "pathology",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "aphthae",
           "uz": "Aftalar",
           "ru": "Афты"
          },
          {
           "code": "ulcers",
           "uz": "Yaralar",
           "ru": "Язвы"
          }
         ]
        },
        {
         "code": "location",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "tongue",
           "uz": "Til",
           "ru": "Язык"
          },
          {
           "code": "soft_palate",
           "uz": "Yumshoq tanglay",
           "ru": "Мягкое небо"
          },
          {
           "code": "mouth_floor",
           "uz": "Og‘iz tubi",
           "ru": "Дно полости рта"
          }
         ]
        }
       ]
      },
      {
       "code": "tongue",
       "uz": "Til",
       "ru": "Язык",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "clean",
           "uz": "Toza, nam",
           "ru": "Чистый, влажный",
           "is_norm": true
          },
          {
           "code": "white_coat",
           "uz": "Oq karash bilan qoplangan",
           "ru": "Обложен белым налетом"
          }
         ]
        },
        {
         "code": "pathology",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "aphtha",
           "uz": "Afta",
           "ru": "Афта"
          },
          {
           "code": "ulcer",
           "uz": "Yara",
           "ru": "Язва"
          },
          {
           "code": "infiltration",
           "uz": "Infiltratsiya",
           "ru": "Инфильтрация"
          }
         ]
        },
        {
         "code": "pain",
         "type": "radio",
         "options": [
          {
           "code": "none",
           "uz": "Og‘riq yo‘q",
           "ru": "Безболезненный",
           "is_norm": true
          },
          {
           "code": "present",
           "uz": "Og‘riqli",
           "ru": "Болезненный"
          }
         ]
        },
        {
         "code": "side",
         "type": "side",
         "when": {
          "pain": "present"
         }
        }
       ]
      },
      {
       "code": "teeth",
       "uz": "Tishlar",
       "ru": "Зубы",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "healthy",
           "uz": "Sog‘lom",
           "ru": "Здоровы",
           "is_norm": true
          },
          {
           "code": "sanitized",
           "uz": "Sanatsiya qilingan",
           "ru": "Санированы"
          },
          {
           "code": "caries",
           "uz": "Karies",
           "ru": "Кариес"
          }
         ]
        },
        {
         "code": "prostheses",
         "type": "checkbox",
         "uz": "Protezlar mavjud",
         "ru": "Протезы имеются"
        }
       ]
      },
      {
       "code": "palatine_arches",
       "uz": "Tanglay yoylari",
       "ru": "Небные дужки",
       "fields": [
        {
         "code": "visibility",
         "type": "radio",
         "options": [
          {
           "code": "well_visible",
           "uz": "Yaxshi ko‘rinadi",
           "ru": "Хорошо контурируются",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "O‘zgargan",
           "ru": "Изменены"
          }
         ]
        },
        {
         "code": "pathology",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "edema",
           "uz": "Shishgan",
           "ru": "Отечны"
          },
          {
           "code": "hyperemic",
           "uz": "Giperemiyalangan",
           "ru": "Гиперемированы"
          },
          {
           "code": "infiltrated",
           "uz": "Infiltratsiyalangan",
           "ru": "Инфильтрированы"
          },
          {
           "code": "adherent",
           "uz": "Bodomsimon bez bilan yopishgan",
           "ru": "Спаяны с миндалиной"
          }
         ]
        },
        {
         "code": "features",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "cushion",
           "uz": "Yostiqsimon bo‘rtish",
           "ru": "Подушкообразное выпячивание"
          },
          {
           "code": "hiss_fold",
           "uz": "Giss burmasi qalinlashgan",
           "ru": "Складка Гиса утолщена"
          }
         ]
        }
       ]
      },
      {
       "code": "palatine_tonsils",
       "uz": "Tanglay bodomsimon bezlari",
       "ru": "Небные миндалины",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "not_protruding",
           "uz": "Tanglay yoyidan chiqmaydi",
           "ru": "Не выступают из-за дужек",
           "is_norm": true
          },
          {
           "code": "hypertrophied",
           "uz": "Gipertrofiya",
           "ru": "Гипертрофия"
          }
         ]
        },
        {
         "code": "hypertrophy_degree",
         "type": "degree",
         "when": {
          "state": "hypertrophied"
         }
        },
        {
         "code": "surface",
         "type": "radio",
         "options": [
          {
           "code": "smooth",
           "uz": "Silliq",
           "ru": "Гладкая",
           "is_norm": true
          },
          {
           "code": "bumpy",
           "uz": "G‘adir-budir",
           "ru": "Бугристая"
          }
         ]
        },
        {
         "code": "lacunae",
         "type": "radio",
         "options": [
          {
           "code": "not_dilated",
           "uz": "Lakunalar kengaymagan",
           "ru": "Лакуны не расширены",
           "is_norm": true
          },
          {
           "code": "dilated",
           "uz": "Lakunalar kengaygan",
           "ru": "Лакуны расширены"
          }
         ]
        },
        {
         "code": "lacunae_contents",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "none",
           "uz": "Yo‘q",
           "ru": "Нет",
           "is_norm": true
          },
          {
           "code": "caseous_plugs",
           "uz": "Kazeoz tiqinlar",
           "ru": "Казеозные пробки"
          },
          {
           "code": "purulent_plugs",
           "uz": "Yiringli tiqinlar",
           "ru": "Гнойные пробки"
          },
          {
           "code": "mucous_plugs",
           "uz": "Shilliq tiqinlar",
           "ru": "Слизистые пробки"
          },
          {
           "code": "pus",
           "uz": "Yiring",
           "ru": "Гной"
          },
          {
           "code": "mucus",
           "uz": "Shilliq",
           "ru": "Слизь"
          }
         ]
        }
       ]
      },
      {
       "code": "posterior_pharynx",
       "uz": "Halqum orqa devori",
       "ru": "Задняя стенка глотки",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "pink_smooth",
           "uz": "Pushti, silliq",
           "ru": "Розовая, гладкая",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "O‘zgargan",
           "ru": "Изменена"
          }
         ]
        },
        {
         "code": "pathology",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "granules_hyper",
           "uz": "Limfoid granulalar gipertrofiyasi",
           "ru": "Гипертрофия лимфоидных гранул"
          },
          {
           "code": "lateral_hyper",
           "uz": "Yon valiklar gipertrofiyasi",
           "ru": "Гипертрофия боковых валиков"
          },
          {
           "code": "atrophy",
           "uz": "Atrofiya",
           "ru": "Атрофия"
          }
         ]
        },
        {
         "code": "contents",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "pus",
           "uz": "Yiring",
           "ru": "Гной"
          },
          {
           "code": "crusts",
           "uz": "Qobiqlar",
           "ru": "Корки"
          },
          {
           "code": "mucus",
           "uz": "Shilliq",
           "ru": "Слизь"
          },
          {
           "code": "blood",
           "uz": "Qon",
           "ru": "Кровь"
          }
         ]
        }
       ]
      },
      {
       "code": "pharyngeal_reflex",
       "uz": "Halqum refleksi",
       "ru": "Глоточный рефлекс",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "preserved",
           "uz": "Saqlangan",
           "ru": "Сохранен",
           "is_norm": true
          },
          {
           "code": "reduced",
           "uz": "Pasaygan",
           "ru": "Снижен"
          },
          {
           "code": "elevated",
           "uz": "Yuqori",
           "ru": "Высокий"
          }
         ]
        }
       ]
      },
      {
       "code": "posterior_choanae",
       "uz": "Xoanalar (orqa rinoskopiya)",
       "ru": "Хоаны (задняя риноскопия)",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Erkin",
           "ru": "Свободны",
           "is_norm": true
          },
          {
           "code": "closed",
           "uz": "Yopilgan",
           "ru": "Закрыты"
          }
         ]
        },
        {
         "code": "cause",
         "type": "checkbox_multi",
         "when": {
          "state": "closed"
         },
         "options": [
          {
           "code": "turbinate_hyper_inf",
           "uz": "Pastki chig‘anoqlar gipertrofiyasi",
           "ru": "Гипертрофия нижних раковин"
          },
          {
           "code": "turbinate_hyper_mid",
           "uz": "O‘rta chig‘anoqlar gipertrofiyasi",
           "ru": "Гипертрофия средних раковин"
          },
          {
           "code": "polyp",
           "uz": "Polip",
           "ru": "Полип"
          },
          {
           "code": "tumor",
           "uz": "O‘sma",
           "ru": "Новообразование"
          },
          {
           "code": "adenoids",
           "uz": "Adenoidlar",
           "ru": "Аденоиды"
          }
         ]
        }
       ]
      },
      {
       "code": "posterior_vault",
       "uz": "Gumbaz",
       "ru": "Свод",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Erkin",
           "ru": "Свободен",
           "is_norm": true
          },
          {
           "code": "tumor",
           "uz": "O‘sma",
           "ru": "Новообразование"
          },
          {
           "code": "adenoids",
           "uz": "Adenoidlar",
           "ru": "Аденоиды"
          }
         ]
        },
        {
         "code": "adenoid_degree",
         "type": "degree",
         "when": {
          "state": "adenoids"
         }
        }
       ]
      },
      {
       "code": "auditory_tubes",
       "uz": "Eshituv naylari og‘zi",
       "ru": "Устья слуховых труб",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "well_visible",
           "uz": "Yaxshi ko‘rinadi, erkin",
           "ru": "Хорошо контурируются, свободны",
           "is_norm": true
          },
          {
           "code": "narrowed",
           "uz": "Toraygan",
           "ru": "Сужены"
          }
         ]
        },
        {
         "code": "contents",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "mucus",
           "uz": "Shilliq",
           "ru": "Слизь"
          },
          {
           "code": "pus",
           "uz": "Yiring",
           "ru": "Гной"
          }
         ]
        },
        {
         "code": "hypertrophy",
         "type": "checkbox",
         "uz": "Nay valiklari va bodomsimon bezlar gipertrofiyasi",
         "ru": "Гипертрофия трубных валиков и миндалин"
        }
       ]
      }
     ]
    },
    {
     "code": "otoscopy",
     "uz": "Otoskopiya (AD/AS)",
     "ru": "Отоскопия (AD/AS)",
     "ears": [
      {
       "code": "AD",
       "uz": "AD (o‘ng)",
       "ru": "AD (правое)"
      },
      {
       "code": "AS",
       "uz": "AS (chap)",
       "ru": "AS (левое)"
      }
     ],
     "parts": [
      {
       "code": "auricle_canal",
       "uz": "Quloq suprasi va tashqi eshituv yo‘li",
       "ru": "Ушная раковина и наружный слуховой проход",
       "fields": [
        {
         "code": "shape",
         "type": "radio",
         "options": [
          {
           "code": "normal",
           "uz": "To‘g‘ri shaklda",
           "ru": "Правильной формы",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "O‘zgargan",
           "ru": "Изменена"
          }
         ]
        },
        {
         "code": "canal_width",
         "type": "radio",
         "options": [
          {
           "code": "normal",
           "uz": "Normal",
           "ru": "Нормальный",
           "is_norm": true
          },
          {
           "code": "wide",
           "uz": "Keng",
           "ru": "Широкий"
          },
          {
           "code": "narrow",
           "uz": "Tor",
           "ru": "Узкий"
          }
         ]
        },
        {
         "code": "pathology",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "exostosis",
           "uz": "Ekzostoz",
           "ru": "Экзостоз"
          },
          {
           "code": "pain",
           "uz": "Og‘riqli",
           "ru": "Болезненный"
          },
          {
           "code": "infiltration",
           "uz": "Infiltratsiya",
           "ru": "Инфильтрация"
          },
          {
           "code": "hyperemia",
           "uz": "Giperemiya",
           "ru": "Гиперемия"
          }
         ]
        },
        {
         "code": "pain_part",
         "type": "radio",
         "when": {
          "pathology": "pain"
         },
         "options": [
          {
           "code": "bone",
           "uz": "Suyak qismi",
           "ru": "Костная часть"
          },
          {
           "code": "cartilage",
           "uz": "Tog‘ay qismi",
           "ru": "Хрящевая часть"
          }
         ]
        },
        {
         "code": "contents",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "clean",
           "uz": "Toza",
           "ru": "Свободный",
           "is_norm": true
          },
          {
           "code": "cerumen",
           "uz": "Oltingugurt",
           "ru": "Сера"
          },
          {
           "code": "crusts",
           "uz": "Qobiqlar",
           "ru": "Корки"
          },
          {
           "code": "plug",
           "uz": "Tiqin",
           "ru": "Пробка"
          },
          {
           "code": "pus",
           "uz": "Yiring",
           "ru": "Гной"
          },
          {
           "code": "blood",
           "uz": "Qon",
           "ru": "Кровь"
          },
          {
           "code": "films",
           "uz": "Pardalar",
           "ru": "Пленки"
          }
         ]
        }
       ]
      },
      {
       "code": "tympanic_membrane",
       "uz": "Baraban pardasi",
       "ru": "Барабанная перепонка",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "pearly_gray",
           "uz": "Marvaridsimon kulrang",
           "ru": "Перламутрово-серая",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Giperemiyalangan",
           "ru": "Гиперемирована"
          }
         ]
        },
        {
         "code": "landmarks",
         "type": "radio",
         "options": [
          {
           "code": "visible",
           "uz": "Yaxshi ko‘rinadi",
           "ru": "Выражены хорошо",
           "is_norm": true
          },
          {
           "code": "not_visible",
           "uz": "Yaxshi ko‘rinmaydi",
           "ru": "Не выражены"
          }
         ]
        },
        {
         "code": "perforation",
         "type": "radio",
         "options": [
          {
           "code": "none",
           "uz": "Yo‘q",
           "ru": "Нет",
           "is_norm": true
          },
          {
           "code": "marginal",
           "uz": "Chekka",
           "ru": "Краевая"
          },
          {
           "code": "central",
           "uz": "Markaziy",
           "ru": "Некраевая (центральная)"
          }
         ]
        },
        {
         "code": "pathology",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "pulsating",
           "uz": "Pulsatsiyalovchi refleks",
           "ru": "Пульсирующий рефлекс"
          },
          {
           "code": "infiltration",
           "uz": "Infiltratsiya",
           "ru": "Инфильтрация"
          },
          {
           "code": "retraction",
           "uz": "Retraksiya",
           "ru": "Втянутость"
          },
          {
           "code": "scars",
           "uz": "Chandiqlar",
           "ru": "Рубцы"
          },
          {
           "code": "calcinates",
           "uz": "Kalsinatlar",
           "ru": "Кальцинаты"
          }
         ]
        }
       ]
      },
      {
       "code": "tympanic_cavity",
       "uz": "Baraban bo‘shlig‘i",
       "ru": "Барабанная полость",
       "needs_perforation": true,
       "fields": [
        {
         "code": "contents",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "pus",
           "uz": "Yiring",
           "ru": "Гной"
          },
          {
           "code": "granulations",
           "uz": "Granulyatsiyalar",
           "ru": "Грануляции"
          },
          {
           "code": "polyp",
           "uz": "Polip",
           "ru": "Полип"
          },
          {
           "code": "cholesteatoma",
           "uz": "Xolesteatoma massalari",
           "ru": "Холестеатомные массы"
          },
          {
           "code": "blood",
           "uz": "Qon",
           "ru": "Кровь"
          }
         ]
        }
       ]
      }
     ]
    },
    {
     "code": "laryngoscopy",
     "uz": "Laringoskopiya",
     "ru": "Ларингоскопия",
     "parts": [
      {
       "code": "lingual_tonsil",
       "uz": "Til bodomsimon bezi",
       "ru": "Язычная миндалина",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "not_enlarged",
           "uz": "Kattalashmagan",
           "ru": "Не увеличена",
           "is_norm": true
          },
          {
           "code": "enlarged",
           "uz": "Kattalashgan",
           "ru": "Увеличена"
          }
         ]
        },
        {
         "code": "features",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "no_plaque",
           "uz": "Karash yo‘q",
           "ru": "Налетов нет",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Giperemiyalangan",
           "ru": "Гиперемирована"
          }
         ]
        }
       ]
      },
      {
       "code": "valleculae",
       "uz": "Vallekulalar",
       "ru": "Валлекулы",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Erkin",
           "ru": "Свободны",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "O‘zgargan",
           "ru": "Изменены"
          }
         ]
        },
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "pale_pink",
           "uz": "Oqartirilgan pushti",
           "ru": "Бледно-розовая",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Giperemiyalangan",
           "ru": "Гиперемирована"
          }
         ]
        }
       ]
      },
      {
       "code": "pharynx_walls",
       "uz": "Orqa va yon devorlar",
       "ru": "Задняя и боковые стенки",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "pale_pink",
           "uz": "Oqartirilgan pushti",
           "ru": "Бледно-розовая",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Giperemiyalangan",
           "ru": "Гиперемирована"
          }
         ]
        },
        {
         "code": "pathology",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "edema",
           "uz": "Shishgan",
           "ru": "Отечна"
          },
          {
           "code": "infiltrated",
           "uz": "Infiltratsiyalangan",
           "ru": "Инфильтрирована"
          }
         ]
        }
       ]
      },
      {
       "code": "external_larynx",
       "uz": "Hiqildoq tashqi ko‘rigi",
       "ru": "Гортань — наружный осмотр",
       "fields": [
        {
         "code": "contour",
         "type": "radio",
         "options": [
          {
           "code": "well",
           "uz": "Yaxshi konturlanadi",
           "ru": "Хорошо контурируется",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "O‘zgargan",
           "ru": "Изменена"
          }
         ]
        },
        {
         "code": "mobility",
         "type": "radio",
         "options": [
          {
           "code": "passive_mobile",
           "uz": "Passiv harakatchan",
           "ru": "Пассивно подвижна",
           "is_norm": true
          },
          {
           "code": "immobile",
           "uz": "Harakatsiz",
           "ru": "Неподвижна"
          }
         ]
        },
        {
         "code": "shape",
         "type": "radio",
         "options": [
          {
           "code": "normal",
           "uz": "To‘g‘ri shaklda",
           "ru": "Правильной формы",
           "is_norm": true
          },
          {
           "code": "deformed",
           "uz": "Deformatsiya",
           "ru": "Деформирована"
          }
         ]
        },
        {
         "code": "crepitus",
         "type": "radio",
         "options": [
          {
           "code": "negative",
           "uz": "«Tog‘ay qirsillashi» manfiy",
           "ru": "Симптом «хруста хрящей» отрицательный",
           "is_norm": true
          },
          {
           "code": "positive",
           "uz": "«Tog‘ay qirsillashi» musbat",
           "ru": "Симптом «хруста хрящей» положительный"
          }
         ]
        }
       ]
      },
      {
       "code": "vocal_folds",
       "uz": "Ovoz boylamlari",
       "ru": "Голосовые складки",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "whitish",
           "uz": "Oqartirilgan",
           "ru": "Белесоватые",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Giperemiyalangan",
           "ru": "Гиперемированы"
          }
         ]
        },
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "clean",
           "uz": "Toza",
           "ru": "Чистые",
           "is_norm": true
          },
          {
           "code": "plaques",
           "uz": "Karashlar mavjud",
           "ru": "Налеты"
          },
          {
           "code": "tumor",
           "uz": "O‘sma",
           "ru": "Новообразование"
          },
          {
           "code": "hypertrophy",
           "uz": "Gipertrofiya",
           "ru": "Гипертрофия"
          }
         ]
        },
        {
         "code": "closure",
         "type": "radio",
         "options": [
          {
           "code": "full",
           "uz": "Fonatsiyada to‘liq yopiladi",
           "ru": "Полностью смыкаются",
           "is_norm": true
          },
          {
           "code": "not_full",
           "uz": "Fonatsiyada to‘liq yopilmaydi",
           "ru": "Полностью не смыкаются"
          }
         ]
        },
        {
         "code": "movement",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Erkin",
           "ru": "Свободные",
           "is_norm": true
          },
          {
           "code": "limited",
           "uz": "Harakati cheklangan",
           "ru": "Ограничены в движении"
          },
          {
           "code": "immobile",
           "uz": "Harakatsiz",
           "ru": "Неподвижны"
          }
         ]
        },
        {
         "code": "side",
         "type": "side",
         "when": {
          "state": [
           "plaques",
           "tumor",
           "hypertrophy"
          ]
         }
        }
       ]
      },
      {
       "code": "voice",
       "uz": "Ovoz",
       "ru": "Голос",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "sonorous",
           "uz": "Jarangdor",
           "ru": "Звучный",
           "is_norm": true
          },
          {
           "code": "hoarse",
           "uz": "Xirillagan",
           "ru": "Хриплый"
          },
          {
           "code": "aphonia",
           "uz": "Afoniya",
           "ru": "Афония"
          }
         ]
        }
       ]
      },
      {
       "code": "dyspnea",
       "uz": "Hansirash",
       "ru": "Одышка",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "none",
           "uz": "Yo‘q",
           "ru": "Нет",
           "is_norm": true
          },
          {
           "code": "present",
           "uz": "Bor",
           "ru": "Есть"
          }
         ]
        },
        {
         "code": "type",
         "type": "radio",
         "when": {
          "state": "present"
         },
         "options": [
          {
           "code": "inspiratory",
           "uz": "Inspirator",
           "ru": "Инспираторная"
          },
          {
           "code": "expiratory",
           "uz": "Ekspirator",
           "ru": "Экспираторная"
          },
          {
           "code": "mixed",
           "uz": "Aralash",
           "ru": "Смешанная"
          }
         ]
        },
        {
         "code": "when",
         "type": "radio",
         "when": {
          "state": "present"
         },
         "options": [
          {
           "code": "rest",
           "uz": "Tinch holatda",
           "ru": "В покое"
          },
          {
           "code": "exertion",
           "uz": "Yuklamada",
           "ru": "При нагрузке"
          }
         ]
        }
       ]
      },
      {
       "code": "stenosis",
       "uz": "Hiqildoq stenozi",
       "ru": "Стеноз гортани",
       "fields": [
        {
         "code": "degree",
         "type": "degree"
        }
       ]
      }
     ]
    }
   ]
  };

  const { complaints: COMPLAINTS, discharge: DISCHARGE, sides: SIDES, degrees: DEGREES, methods: METHODS } = CATALOG;

  // Formadagi maydon sarlavhalari (hujjatda chiqmaydi, faqat formada).
  const FIELD_LABELS = {
    state: { uz: 'Holati', ru: 'Состояние' },
    deformity_type: { uz: 'Deformatsiya turi', ru: 'Вид деформации' },
    side: { uz: 'Tomoni', ru: 'Сторона' },
    part: { uz: 'Qismi', ru: 'Отдел' },
    location: { uz: 'Joylashuvi', ru: 'Локализация' },
    branch: { uz: 'Shoxlari', ru: 'Ветви' },
    color: { uz: 'Rangi', ru: 'Цвет' },
    moisture: { uz: 'Namligi', ru: 'Влажность' },
    condition: { uz: 'O‘zgarishlar', ru: 'Изменения' },
    features: { uz: 'Xususiyatlari', ru: 'Особенности' },
    shape: { uz: 'Shakli', ru: 'Форма' },
    pathology: { uz: 'Patologik o‘zgarishlar', ru: 'Патологические изменения' },
    pain: { uz: 'Og‘riq', ru: 'Болезненность' },
    visibility: { uz: 'Ko‘rinishi', ru: 'Видимость' },
    hypertrophy_degree: { uz: 'Gipertrofiya darajasi', ru: 'Степень гипертрофии' },
    surface: { uz: 'Yuzasi', ru: 'Поверхность' },
    lacunae: { uz: 'Lakunalar', ru: 'Лакуны' },
    lacunae_contents: { uz: 'Lakunalar tarkibi', ru: 'Содержимое лакун' },
    contents: { uz: 'Tarkibi', ru: 'Содержимое' },
    cause: { uz: 'Sababi', ru: 'Причина' },
    adenoid_degree: { uz: 'Adenoidlar darajasi', ru: 'Степень аденоидов' },
    canal_width: { uz: 'Eshituv yo‘li kengligi', ru: 'Ширина слухового прохода' },
    pain_part: { uz: 'Og‘riqli qism', ru: 'Болезненный отдел' },
    landmarks: { uz: 'Tanib olish belgilari', ru: 'Опознавательные знаки' },
    perforation: { uz: 'Perforatsiya', ru: 'Перфорация' },
    contour: { uz: 'Konturi', ru: 'Контуры' },
    mobility: { uz: 'Harakatchanligi', ru: 'Подвижность' },
    crepitus: { uz: 'Krepitatsiya', ru: 'Крепитация' },
    closure: { uz: 'Yopilishi', ru: 'Смыкание' },
    movement: { uz: 'Harakati', ru: 'Движение' },
    type: { uz: 'Turi', ru: 'Тип' },
    when: { uz: 'Qachon', ru: 'Когда' },
    degree: { uz: 'Darajasi', ru: 'Степень' },
  };

  // Tez tanlash uchun tashxislar (XKT-10). Shifokor istalgan matnni ham yozishi mumkin.
  const o = (code, uz, ru) => ({ code, uz, ru });
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

  /* ---------------- Yordamchilar ---------------- */
  const L = (x, lang) => (x ? x[lang] || x.uz || '' : '');
  const text = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : '');

  const COMPLAINT_INDEX = {};
  COMPLAINTS.forEach((g) => g.items.forEach((i) => { COMPLAINT_INDEX[i.code] = i; }));
  const DISCHARGE_CODES = new Set(DISCHARGE.map((d) => d.code));

  function choicesOf(field) {
    if (field.type === 'side') return SIDES;
    if (field.type === 'degree') return DEGREES;
    return field.options || [];
  }

  /** Maydon ko‘rinadimi (visible_when sharti bajarilganmi) */
  function fieldVisible(field, partValue) {
    if (!field.when) return true;
    return Object.entries(field.when).every(([k, want]) => {
      const targets = Array.isArray(want) ? want : [want];
      const v = partValue ? partValue[k] : undefined;
      if (Array.isArray(v)) return v.some((x) => targets.includes(x));
      return v !== undefined && targets.includes(v);
    });
  }

  /** Qism ko‘rinadimi (baraban bo‘shlig‘i faqat perforatsiya bo‘lsa) */
  function partVisible(part, partsValue) {
    if (!part.needs_perforation) return true;
    const tm = partsValue && partsValue.tympanic_membrane;
    return !!tm && !!tm.perforation && tm.perforation !== 'none';
  }

  /* ---------------- Tekshirish (server ham ishlatadi) ---------------- */
  function cleanField(field, v) {
    const allowed = new Set(choicesOf(field).map((x) => x.code));
    switch (field.type) {
      case 'radio': case 'side': case 'degree':
        return typeof v === 'string' && allowed.has(v) ? v : undefined;
      case 'checkbox_multi': {
        if (!Array.isArray(v)) return undefined;
        const out = [...new Set(v.filter((x) => typeof x === 'string' && allowed.has(x)))];
        return out.length ? out : undefined;
      }
      case 'checkbox':
        return v === true ? true : undefined;
      default:
        return undefined;
    }
  }

  function sanitizeParts(method, raw) {
    const src = raw && typeof raw === 'object' ? raw : {};
    const out = {};
    for (const part of method.parts) {
      if (!partVisible(part, out)) continue;
      const pIn = src[part.code] && typeof src[part.code] === 'object' ? src[part.code] : {};
      const pOut = {};
      for (const field of part.fields) {
        const v = cleanField(field, pIn[field.code]);
        if (v !== undefined && fieldVisible(field, pOut)) pOut[field.code] = v;
      }
      const t = text(pIn._text, 500);
      if (t) pOut._text = t;
      if (Object.keys(pOut).length) out[part.code] = pOut;
    }
    return out;
  }

  /** Faqat shablonda mavjud qiymatlarni qoldiradi. Bo‘sh maydonlar tashlab yuboriladi. */
  function sanitizeLor(input) {
    const src = input && typeof input === 'object' ? input : {};
    const out = {};
    for (const m of METHODS) {
      const mIn = src[m.code] && typeof src[m.code] === 'object' ? src[m.code] : {};
      const res = {};
      if (m.ears) {
        const earsIn = mIn.ears && typeof mIn.ears === 'object' ? mIn.ears : {};
        const ears = {};
        for (const e of m.ears) {
          const p = sanitizeParts(m, earsIn[e.code]);
          if (Object.keys(p).length) ears[e.code] = p;
        }
        if (Object.keys(ears).length) res.ears = ears;
      } else {
        const p = sanitizeParts(m, mIn.parts);
        if (Object.keys(p).length) res.parts = p;
      }
      const note = text(mIn.note, 2000);
      if (note) res.note = note;
      if (Object.keys(res).length) out[m.code] = res;
    }
    return out;
  }

  function sanitizeComplaints(arr) {
    if (!Array.isArray(arr)) return [];
    const out = [];
    const seen = new Set();
    for (const raw of arr) {
      const item = typeof raw === 'string' ? { code: raw } : raw && typeof raw === 'object' ? raw : null;
      if (!item || typeof item.code !== 'string' || !COMPLAINT_INDEX[item.code] || seen.has(item.code)) continue;
      seen.add(item.code);
      const c = { code: item.code };
      if (COMPLAINT_INDEX[item.code].has_discharge_type && DISCHARGE_CODES.has(item.discharge)) {
        c.discharge = item.discharge;
        const t = text(item.discharge_text, 200);
        if (item.discharge === 'other' && t) c.discharge_text = t;
      }
      out.push(c);
    }
    return out;
  }

  /* ---------------- Hujjat matni ---------------- */
  // Birinchi bo‘lakdan keyingilari kichik harf bilan: "Deformatsiya, bukrilik, chapda".
  const lowerFirst = (s) => (/^\p{Lu}\p{Ll}/u.test(s) ? s[0].toLowerCase() + s.slice(1) : s);

  // Faqat qiymatning o‘zi tushunarsiz bo‘ladigan maydonlarda sarlavha ham chop etiladi ("perforatsiya: yo‘q").
  const PRINT_WITH_LABEL = new Set(['perforation', 'lacunae_contents', 'contents', 'cause', 'location', 'branch', 'pain_part']);

  function fieldText(field, v, lang) {
    if (field.type === 'checkbox') return L(field, lang);
    const ch = choicesOf(field);
    const label = (code) => L(ch.find((x) => x.code === code), lang) || code;
    const value = Array.isArray(v) ? v.map((c, i) => (i ? lowerFirst(label(c)) : label(c))).join(', ') : label(v);
    return PRINT_WITH_LABEL.has(field.code) && FIELD_LABELS[field.code]
      ? `${L(FIELD_LABELS[field.code], lang)}: ${lowerFirst(value)}` : value;
  }

  function partsLines(method, parts, lang) {
    const lines = [];
    for (const part of method.parts) {
      const pv = parts[part.code];
      if (!pv) continue;
      const pieces = [];
      for (const f of part.fields) if (pv[f.code] !== undefined) pieces.push(fieldText(f, pv[f.code], lang));
      if (pv._text) pieces.push(pv._text);
      const joined = pieces.map((p, i) => (i ? lowerFirst(p) : p)).join(', ');
      lines.push({ label: L(part, lang), text: joined });
    }
    return lines;
  }

  /** [{ title, groups: [{ sub, lines: [{label, text}] }], note }] — faqat qayd etilgan qismlar */
  function lorStatusText(lor, lang) {
    const out = [];
    const src = lor && typeof lor === 'object' ? lor : {};
    for (const m of METHODS) {
      const mv = src[m.code];
      if (!mv) continue;
      const groups = [];
      if (m.ears) {
        for (const e of m.ears) {
          const p = mv.ears && mv.ears[e.code];
          if (p) groups.push({ sub: L(e, lang), lines: partsLines(m, p, lang) });
        }
      } else if (mv.parts) {
        groups.push({ sub: '', lines: partsLines(m, mv.parts, lang) });
      }
      if (groups.length || mv.note) out.push({ title: L(m, lang), groups, note: mv.note || '' });
    }
    return out;
  }

  function complaintLabel(code, lang) {
    return COMPLAINT_INDEX[code] ? L(COMPLAINT_INDEX[code], lang) : code;
  }

  /** "Burun bitishi, quloqdan ajralma kelishi (yiringli)" */
  function complaintsText(items, lang) {
    return (Array.isArray(items) ? items : []).map((raw, i) => {
      const c = typeof raw === 'string' ? { code: raw } : raw;
      let s = complaintLabel(c.code, lang);
      if (c.discharge) {
        const d = DISCHARGE.find((x) => x.code === c.discharge);
        const dl = c.discharge === 'other' && c.discharge_text ? c.discharge_text : L(d, lang);
        s += ` (${lowerFirst(dl)})`;
      }
      return i ? lowerFirst(s) : s;
    }).join(', ');
  }

  return {
    COMPLAINTS, DISCHARGE, SIDES, DEGREES, METHODS, FIELD_LABELS, DIAGNOSES,
    choicesOf, fieldVisible, partVisible,
    sanitizeLor, sanitizeComplaints, lorStatusText, complaintLabel, complaintsText,
  };
});
