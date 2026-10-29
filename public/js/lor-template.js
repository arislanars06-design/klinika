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
     "uz": "Умумий шикоятлар",
     "ru": "Общие жалобы",
     "items": [
      {
       "code": "gen_headache",
       "uz": "Бош оғриғи",
       "ru": "Головная боль"
      },
      {
       "code": "gen_fever_subfebrile",
       "uz": "Иситма (субфебрил)",
       "ru": "Температура (субфебрильная)"
      },
      {
       "code": "gen_fever_febrile",
       "uz": "Иситма (фебрил)",
       "ru": "Температура (фебрильная)"
      },
      {
       "code": "gen_fever_pyretic",
       "uz": "Иситма (пиретик)",
       "ru": "Температура (пиретическая)"
      },
      {
       "code": "gen_weakness",
       "uz": "Умумий ҳолсизлик",
       "ru": "Общая слабость"
      },
      {
       "code": "gen_dizziness",
       "uz": "Бош айланиши",
       "ru": "Головокружение"
      },
      {
       "code": "gen_nausea",
       "uz": "Кўнгил айниши",
       "ru": "Тошнота"
      },
      {
       "code": "gen_vomiting",
       "uz": "Қусиш",
       "ru": "Рвота"
      },
      {
       "code": "gen_diarrhea",
       "uz": "Ич кетиши",
       "ru": "Диарея"
      },
      {
       "code": "gen_joint_pain",
       "uz": "Бўғимларда оғриқ",
       "ru": "Боль в суставах"
      },
      {
       "code": "gen_back_pain",
       "uz": "Бел соҳасида оғриқ",
       "ru": "Боль в поясничной области"
      }
     ]
    },
    {
     "code": "ear",
     "uz": "Қулоқ",
     "ru": "Уши",
     "items": [
      {
       "code": "ear_cosmetic",
       "uz": "Қулоқ супрасида косметик нуқсон (шалпанг қулоқлик, деформация, ўсма, отогематома)",
       "ru": "Ушная раковина — косметический дефект (лопоухость, деформация, новообразование, отогематома)"
      },
      {
       "code": "ear_pain",
       "uz": "Қулоқда оғриқ",
       "ru": "Боль в ухе"
      },
      {
       "code": "ear_noise",
       "uz": "Қулоқда шовқин",
       "ru": "Шум в ушах"
      },
      {
       "code": "ear_hearing_loss",
       "uz": "Эшитиш пасайиши",
       "ru": "Снижение слуха"
      },
      {
       "code": "ear_congestion",
       "uz": "Қулоқ битиши",
       "ru": "Заложенность уха"
      },
      {
       "code": "ear_discharge",
       "uz": "Қулоқдан ажралма келиши",
       "ru": "Выделения из уха",
       "has_discharge_type": true
      },
      {
       "code": "ear_itching",
       "uz": "Қулоқда қичишиш",
       "ru": "Зуд в ухе"
      },
      {
       "code": "ear_discomfort",
       "uz": "Қулоқда ноқулайлик ҳисси",
       "ru": "Чувство дискомфорта"
      }
     ]
    },
    {
     "code": "nose",
     "uz": "Бурун ва ёндош бурун бўшлиқлари",
     "ru": "Нос и околоносовые пазухи",
     "items": [
      {
       "code": "nose_cosmetic",
       "uz": "Косметик нуқсон ёки ҳосила",
       "ru": "Косметический дефект, образования"
      },
      {
       "code": "nose_congestion",
       "uz": "Бурун битиши",
       "ru": "Заложенность носа"
      },
      {
       "code": "nose_breathing",
       "uz": "Бурун орқали нафас олишнинг қийинлашиши",
       "ru": "Затруднение дыхания через нос"
      },
      {
       "code": "nose_discharge",
       "uz": "Бурундан ажралма келиши",
       "ru": "Выделения из носа",
       "has_discharge_type": true
      },
      {
       "code": "nose_itching",
       "uz": "Бурунда қичишиш",
       "ru": "Зуд в носу"
      },
      {
       "code": "nose_pain",
       "uz": "Бурун оғриғи",
       "ru": "Боль в носу"
      },
      {
       "code": "nose_trigeminal_pain",
       "uz": "Уч шохли нервнинг I–II шохлари чиқиш нуқталарида оғриқ",
       "ru": "Болезненность точек выхода I–II ветвей тройничного нерва"
      },
      {
       "code": "nose_face_heaviness",
       "uz": "Юз соҳасида оғирлик ҳисси",
       "ru": "Тяжесть в области лица"
      }
     ]
    },
    {
     "code": "pharynx",
     "uz": "Ҳалқум",
     "ru": "Глотка",
     "items": [
      {
       "code": "pharynx_pain",
       "uz": "Томоқ оғриғи",
       "ru": "Боль в горле"
      },
      {
       "code": "pharynx_tickling",
       "uz": "Қирилиш ёки ачишиш ҳисси",
       "ru": "Першение"
      },
      {
       "code": "pharynx_itching",
       "uz": "Қичишиш",
       "ru": "Зуд"
      },
      {
       "code": "pharynx_lump",
       "uz": "«Томоқда тугун» ҳисси",
       "ru": "Чувство «комка»"
      },
      {
       "code": "pharynx_foreign_body",
       "uz": "«Бегона жисм» ҳисси",
       "ru": "Чувство инородного тела"
      },
      {
       "code": "pharynx_discharge",
       "uz": "Ажралма",
       "ru": "Отделяемое",
       "has_discharge_type": true
      },
      {
       "code": "pharynx_swallowing",
       "uz": "Ютишнинг қийинлашиши",
       "ru": "Затрудненное глотание"
      },
      {
       "code": "pharynx_cough",
       "uz": "Йўтал",
       "ru": "Кашель"
      }
     ]
    },
    {
     "code": "larynx",
     "uz": "Ҳиқилдоқ",
     "ru": "Гортань",
     "items": [
      {
       "code": "larynx_voice_change",
       "uz": "Овоз функциясининг ўзгариши (хириллаш, бўғилиш, овоз йўқолиши)",
       "ru": "Изменение голосовой функции (охриплость, осиплость, афония)"
      },
      {
       "code": "larynx_cough",
       "uz": "Йўтал",
       "ru": "Кашель"
      },
      {
       "code": "larynx_pain",
       "uz": "Оғриқ",
       "ru": "Боль"
      },
      {
       "code": "larynx_foreign_body",
       "uz": "Бегона жисм ҳисси",
       "ru": "Чувство инородного тела"
      },
      {
       "code": "larynx_breathing",
       "uz": "Нафас олишнинг қийинлашиши",
       "ru": "Затрудненное дыхание"
      },
      {
       "code": "larynx_swallowing",
       "uz": "Ютишнинг қийинлашиши",
       "ru": "Затрудненное глотание"
      }
     ]
    }
   ],
   "discharge": [
    {
     "code": "purulent",
     "uz": "Йирингли",
     "ru": "Гнойное"
    },
    {
     "code": "serous",
     "uz": "Сероз",
     "ru": "Серозное"
    },
    {
     "code": "mucous",
     "uz": "Шиллиқ",
     "ru": "Слизистое"
    },
    {
     "code": "mucopurulent",
     "uz": "Шиллиқ-йирингли",
     "ru": "Слизисто-гнойное"
    },
    {
     "code": "bloody",
     "uz": "Қонли",
     "ru": "Кровянистое"
    },
    {
     "code": "sanguineous",
     "uz": "Сувли-қонли",
     "ru": "Сукровичное"
    },
    {
     "code": "caseous",
     "uz": "Казеоз",
     "ru": "Казеозное"
    },
    {
     "code": "watery",
     "uz": "Сувли",
     "ru": "Водянистое"
    },
    {
     "code": "other",
     "uz": "Бошқа",
     "ru": "Другое",
     "requires_text": true
    }
   ],
   "sides": [
    {
     "code": "left",
     "uz": "Чапда",
     "ru": "Слева"
    },
    {
     "code": "right",
     "uz": "Ўнгда",
     "ru": "Справа"
    },
    {
     "code": "both",
     "uz": "Икки томонда",
     "ru": "С обеих сторон"
    }
   ],
   "degrees": [
    {
     "code": "none",
     "uz": "Йўқ",
     "ru": "Нет",
     "is_norm": true
    },
    {
     "code": "I",
     "uz": "I даража",
     "ru": "I ст."
    },
    {
     "code": "II",
     "uz": "II даража",
     "ru": "II ст."
    },
    {
     "code": "III",
     "uz": "III даража",
     "ru": "III ст."
    }
   ],
   "methods": [
    {
     "code": "rhinoscopy",
     "uz": "Риноскопия",
     "ru": "Риноскопия",
     "parts": [
      {
       "code": "external_nose",
       "uz": "Ташқи бурун",
       "ru": "Наружный нос",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "unchanged",
           "uz": "Ўзгармаган",
           "ru": "Не изменен",
           "is_norm": true
          },
          {
           "code": "deformed",
           "uz": "Деформация",
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
           "uz": "Чўкиш",
           "ru": "Западение"
          },
          {
           "code": "hump",
           "uz": "Букрилик",
           "ru": "Горбинка"
          },
          {
           "code": "scoliosis",
           "uz": "Сколиоз",
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
           "uz": "Суяк қисми",
           "ru": "Костная часть"
          },
          {
           "code": "cartilage",
           "uz": "Тоғай қисми",
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
           "uz": "Бурун орқаси",
           "ru": "Спинка"
          },
          {
           "code": "wings",
           "uz": "Қанотлари",
           "ru": "Крылья"
          },
          {
           "code": "tip",
           "uz": "Учи",
           "ru": "Кончик"
          },
          {
           "code": "nostrils",
           "uz": "Бурун тешиклари",
           "ru": "Ноздри"
          }
         ]
        }
       ]
      },
      {
       "code": "trigeminal",
       "uz": "Уч шохли нерв чиқиш нуқталари",
       "ru": "Точки выхода тройничного нерва",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "painless",
           "uz": "Оғриқсиз",
           "ru": "Безболезненны",
           "is_norm": true
          },
          {
           "code": "painful",
           "uz": "Оғриқли",
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
           "uz": "I шох",
           "ru": "I ветвь"
          },
          {
           "code": "II",
           "uz": "II шох",
           "ru": "II ветвь"
          },
          {
           "code": "III",
           "uz": "III шох",
           "ru": "III ветвь"
          }
         ]
        }
       ]
      },
      {
       "code": "breathing",
       "uz": "Бурун орқали нафас олиш",
       "ru": "Дыхание через нос",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Эркин",
           "ru": "Свободное",
           "is_norm": true
          },
          {
           "code": "difficult",
           "uz": "Қийинлашган",
           "ru": "Затруднено"
          },
          {
           "code": "absent",
           "uz": "Мавжуд эмас",
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
       "uz": "Бурун даҳлизи",
       "ru": "Преддверие",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "unchanged",
           "uz": "Ўзгармаган",
           "ru": "Не изменено",
           "is_norm": true
          },
          {
           "code": "narrowed",
           "uz": "Торайган",
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
       "uz": "Ҳид билиш",
       "ru": "Обоняние",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "preserved",
           "uz": "Сақланган",
           "ru": "Сохранено",
           "is_norm": true
          },
          {
           "code": "hyposmia",
           "uz": "Гипосмия",
           "ru": "Гипосмия"
          },
          {
           "code": "anosmia",
           "uz": "Аносмия",
           "ru": "Аносмия"
          },
          {
           "code": "hyperosmia",
           "uz": "Гиперосмия",
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
       "uz": "Шиллиқ қават",
       "ru": "Слизистая оболочка",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "pink",
           "uz": "Пушти",
           "ru": "Розовая",
           "is_norm": true
          },
          {
           "code": "pale_pink",
           "uz": "Оқартирилган пушти",
           "ru": "Бледно-розовая"
          },
          {
           "code": "bluish",
           "uz": "Кўкимтир",
           "ru": "Синюшная"
          },
          {
           "code": "hyperemic",
           "uz": "Гиперемияланган",
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
           "uz": "Нам",
           "ru": "Влажная",
           "is_norm": true
          },
          {
           "code": "dry",
           "uz": "Қуруқ",
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
           "uz": "Гипертрофияланган",
           "ru": "Гипертрофирована"
          },
          {
           "code": "ulcerated",
           "uz": "Яраланган",
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
           "uz": "Бурун тўсиғи соҳаси",
           "ru": "Область перегородки носа"
          },
          {
           "code": "turbinate_inferior",
           "uz": "Пастки чиғаноқ",
           "ru": "Нижняя носовая раковина"
          },
          {
           "code": "turbinate_middle",
           "uz": "Ўрта чиғаноқ",
           "ru": "Средняя носовая раковина"
          },
          {
           "code": "turbinate_superior",
           "uz": "Юқори чиғаноқ",
           "ru": "Верхняя носовая раковина"
          },
          {
           "code": "meatus_inferior",
           "uz": "Пастки бурун йўли",
           "ru": "Нижний носовой ход"
          },
          {
           "code": "meatus_middle",
           "uz": "Ўрта бурун йўли",
           "ru": "Средний носовой ход"
          },
          {
           "code": "meatus_superior",
           "uz": "Юқори бурун йўли",
           "ru": "Верхний носовой ход"
          },
          {
           "code": "end_anterior",
           "uz": "Олдинги учи",
           "ru": "Передний конец"
          },
          {
           "code": "end_posterior",
           "uz": "Орқа учи",
           "ru": "Задний конец"
          }
         ]
        }
       ]
      },
      {
       "code": "septum",
       "uz": "Бурун тўсиғи",
       "ru": "Носовая перегородка",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "midline",
           "uz": "Ўрта чизиқда",
           "ru": "По средней линии",
           "is_norm": true
          },
          {
           "code": "curved",
           "uz": "Қийшайган",
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
           "uz": "Бўртма",
           "ru": "Бугор"
          },
          {
           "code": "ridge",
           "uz": "Қирра",
           "ru": "Гребень"
          },
          {
           "code": "spike",
           "uz": "Тиканча",
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
           "uz": "C-симон",
           "ru": "С-образно"
          },
          {
           "code": "s_shaped",
           "uz": "S-симон",
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
           "uz": "Тоғай қисмида",
           "ru": "В хрящевом отделе"
          },
          {
           "code": "bone",
           "uz": "Суяк қисмида",
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
     "uz": "Фарингоскопия",
     "ru": "Фарингоскопия",
     "parts": [
      {
       "code": "mouth_opening",
       "uz": "Оғиз очилиши",
       "ru": "Открывание рта",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Эркин",
           "ru": "Свободное",
           "is_norm": true
          },
          {
           "code": "trismus",
           "uz": "Тризм",
           "ru": "Тризм"
          },
          {
           "code": "painful",
           "uz": "Оғриқли",
           "ru": "Болезненное"
          }
         ]
        }
       ]
      },
      {
       "code": "oral_mucosa",
       "uz": "Оғиз шиллиқ қавати",
       "ru": "Слизистая оболочка полости рта",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "pale_pink",
           "uz": "Оқартирилган пушти",
           "ru": "Бледно-розовая",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Гиперемияланган",
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
           "uz": "Афталар",
           "ru": "Афты"
          },
          {
           "code": "ulcers",
           "uz": "Яралар",
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
           "uz": "Тил",
           "ru": "Язык"
          },
          {
           "code": "soft_palate",
           "uz": "Юмшоқ танглай",
           "ru": "Мягкое небо"
          },
          {
           "code": "mouth_floor",
           "uz": "Оғиз туби",
           "ru": "Дно полости рта"
          }
         ]
        }
       ]
      },
      {
       "code": "tongue",
       "uz": "Тил",
       "ru": "Язык",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "clean",
           "uz": "Тоза, нам",
           "ru": "Чистый, влажный",
           "is_norm": true
          },
          {
           "code": "white_coat",
           "uz": "Оқ караш билан қопланган",
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
           "uz": "Афта",
           "ru": "Афта"
          },
          {
           "code": "ulcer",
           "uz": "Яра",
           "ru": "Язва"
          },
          {
           "code": "infiltration",
           "uz": "Инфильтрация",
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
           "uz": "Оғриқ йўқ",
           "ru": "Безболезненный",
           "is_norm": true
          },
          {
           "code": "present",
           "uz": "Оғриқли",
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
       "uz": "Тишлар",
       "ru": "Зубы",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "healthy",
           "uz": "Соғлом",
           "ru": "Здоровы",
           "is_norm": true
          },
          {
           "code": "sanitized",
           "uz": "Санация қилинган",
           "ru": "Санированы"
          },
          {
           "code": "caries",
           "uz": "Кариес",
           "ru": "Кариес"
          }
         ]
        },
        {
         "code": "prostheses",
         "type": "checkbox",
         "uz": "Протезлар мавжуд",
         "ru": "Протезы имеются"
        }
       ]
      },
      {
       "code": "palatine_arches",
       "uz": "Танглай ёйлари",
       "ru": "Небные дужки",
       "fields": [
        {
         "code": "visibility",
         "type": "radio",
         "options": [
          {
           "code": "well_visible",
           "uz": "Яхши кўринади",
           "ru": "Хорошо контурируются",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "Ўзгарган",
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
           "uz": "Шишган",
           "ru": "Отечны"
          },
          {
           "code": "hyperemic",
           "uz": "Гиперемияланган",
           "ru": "Гиперемированы"
          },
          {
           "code": "infiltrated",
           "uz": "Инфильтрацияланган",
           "ru": "Инфильтрированы"
          },
          {
           "code": "adherent",
           "uz": "Бодомсимон без билан ёпишган",
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
           "uz": "Ёстиқсимон бўртиш",
           "ru": "Подушкообразное выпячивание"
          },
          {
           "code": "hiss_fold",
           "uz": "Гисс бурмаси қалинлашган",
           "ru": "Складка Гиса утолщена"
          }
         ]
        }
       ]
      },
      {
       "code": "palatine_tonsils",
       "uz": "Танглай бодомсимон безлари",
       "ru": "Небные миндалины",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "not_protruding",
           "uz": "Танглай ёйидан чиқмайди",
           "ru": "Не выступают из-за дужек",
           "is_norm": true
          },
          {
           "code": "hypertrophied",
           "uz": "Гипертрофия",
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
           "uz": "Силлиқ",
           "ru": "Гладкая",
           "is_norm": true
          },
          {
           "code": "bumpy",
           "uz": "Ғадир-будир",
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
           "uz": "Лакуналар кенгаймаган",
           "ru": "Лакуны не расширены",
           "is_norm": true
          },
          {
           "code": "dilated",
           "uz": "Лакуналар кенгайган",
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
           "uz": "Йўқ",
           "ru": "Нет",
           "is_norm": true
          },
          {
           "code": "caseous_plugs",
           "uz": "Казеоз тиқинлар",
           "ru": "Казеозные пробки"
          },
          {
           "code": "purulent_plugs",
           "uz": "Йирингли тиқинлар",
           "ru": "Гнойные пробки"
          },
          {
           "code": "mucous_plugs",
           "uz": "Шиллиқ тиқинлар",
           "ru": "Слизистые пробки"
          },
          {
           "code": "pus",
           "uz": "Йиринг",
           "ru": "Гной"
          },
          {
           "code": "mucus",
           "uz": "Шиллиқ",
           "ru": "Слизь"
          }
         ]
        }
       ]
      },
      {
       "code": "posterior_pharynx",
       "uz": "Ҳалқум орқа девори",
       "ru": "Задняя стенка глотки",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "pink_smooth",
           "uz": "Пушти, силлиқ",
           "ru": "Розовая, гладкая",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "Ўзгарган",
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
           "uz": "Лимфоид гранулалар гипертрофияси",
           "ru": "Гипертрофия лимфоидных гранул"
          },
          {
           "code": "lateral_hyper",
           "uz": "Ён валиклар гипертрофияси",
           "ru": "Гипертрофия боковых валиков"
          },
          {
           "code": "atrophy",
           "uz": "Атрофия",
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
           "uz": "Йиринг",
           "ru": "Гной"
          },
          {
           "code": "crusts",
           "uz": "Қобиқлар",
           "ru": "Корки"
          },
          {
           "code": "mucus",
           "uz": "Шиллиқ",
           "ru": "Слизь"
          },
          {
           "code": "blood",
           "uz": "Қон",
           "ru": "Кровь"
          }
         ]
        }
       ]
      },
      {
       "code": "pharyngeal_reflex",
       "uz": "Ҳалқум рефлекси",
       "ru": "Глоточный рефлекс",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "preserved",
           "uz": "Сақланган",
           "ru": "Сохранен",
           "is_norm": true
          },
          {
           "code": "reduced",
           "uz": "Пасайган",
           "ru": "Снижен"
          },
          {
           "code": "elevated",
           "uz": "Юқори",
           "ru": "Высокий"
          }
         ]
        }
       ]
      },
      {
       "code": "posterior_choanae",
       "uz": "Хоаналар (орқа риноскопия)",
       "ru": "Хоаны (задняя риноскопия)",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Эркин",
           "ru": "Свободны",
           "is_norm": true
          },
          {
           "code": "closed",
           "uz": "Ёпилган",
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
           "uz": "Пастки чиғаноқлар гипертрофияси",
           "ru": "Гипертрофия нижних раковин"
          },
          {
           "code": "turbinate_hyper_mid",
           "uz": "Ўрта чиғаноқлар гипертрофияси",
           "ru": "Гипертрофия средних раковин"
          },
          {
           "code": "polyp",
           "uz": "Полип",
           "ru": "Полип"
          },
          {
           "code": "tumor",
           "uz": "Ўсма",
           "ru": "Новообразование"
          },
          {
           "code": "adenoids",
           "uz": "Аденоидлар",
           "ru": "Аденоиды"
          }
         ]
        }
       ]
      },
      {
       "code": "posterior_vault",
       "uz": "Гумбаз",
       "ru": "Свод",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Эркин",
           "ru": "Свободен",
           "is_norm": true
          },
          {
           "code": "tumor",
           "uz": "Ўсма",
           "ru": "Новообразование"
          },
          {
           "code": "adenoids",
           "uz": "Аденоидлар",
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
       "uz": "Эшитув найлари оғзи",
       "ru": "Устья слуховых труб",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "well_visible",
           "uz": "Яхши кўринади, эркин",
           "ru": "Хорошо контурируются, свободны",
           "is_norm": true
          },
          {
           "code": "narrowed",
           "uz": "Торайган",
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
           "uz": "Шиллиқ",
           "ru": "Слизь"
          },
          {
           "code": "pus",
           "uz": "Йиринг",
           "ru": "Гной"
          }
         ]
        },
        {
         "code": "hypertrophy",
         "type": "checkbox",
         "uz": "Най валиклари ва бодомсимон безлар гипертрофияси",
         "ru": "Гипертрофия трубных валиков и миндалин"
        }
       ]
      }
     ]
    },
    {
     "code": "otoscopy",
     "uz": "Отоскопия (AD/AS)",
     "ru": "Отоскопия (AD/AS)",
     "ears": [
      {
       "code": "AD",
       "uz": "AD (ўнг)",
       "ru": "AD (правое)"
      },
      {
       "code": "AS",
       "uz": "AS (чап)",
       "ru": "AS (левое)"
      }
     ],
     "parts": [
      {
       "code": "auricle_canal",
       "uz": "Қулоқ супраси ва ташқи эшитув йўли",
       "ru": "Ушная раковина и наружный слуховой проход",
       "fields": [
        {
         "code": "shape",
         "type": "radio",
         "options": [
          {
           "code": "normal",
           "uz": "Тўғри шаклда",
           "ru": "Правильной формы",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "Ўзгарган",
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
           "uz": "Нормал",
           "ru": "Нормальный",
           "is_norm": true
          },
          {
           "code": "wide",
           "uz": "Кенг",
           "ru": "Широкий"
          },
          {
           "code": "narrow",
           "uz": "Тор",
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
           "uz": "Экзостоз",
           "ru": "Экзостоз"
          },
          {
           "code": "pain",
           "uz": "Оғриқли",
           "ru": "Болезненный"
          },
          {
           "code": "infiltration",
           "uz": "Инфильтрация",
           "ru": "Инфильтрация"
          },
          {
           "code": "hyperemia",
           "uz": "Гиперемия",
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
           "uz": "Суяк қисми",
           "ru": "Костная часть"
          },
          {
           "code": "cartilage",
           "uz": "Тоғай қисми",
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
           "uz": "Тоза",
           "ru": "Свободный",
           "is_norm": true
          },
          {
           "code": "cerumen",
           "uz": "Олтингугурт",
           "ru": "Сера"
          },
          {
           "code": "crusts",
           "uz": "Қобиқлар",
           "ru": "Корки"
          },
          {
           "code": "plug",
           "uz": "Тиқин",
           "ru": "Пробка"
          },
          {
           "code": "pus",
           "uz": "Йиринг",
           "ru": "Гной"
          },
          {
           "code": "blood",
           "uz": "Қон",
           "ru": "Кровь"
          },
          {
           "code": "films",
           "uz": "Пардалар",
           "ru": "Пленки"
          }
         ]
        }
       ]
      },
      {
       "code": "tympanic_membrane",
       "uz": "Барабан пардаси",
       "ru": "Барабанная перепонка",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "pearly_gray",
           "uz": "Марваридсимон кулранг",
           "ru": "Перламутрово-серая",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Гиперемияланган",
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
           "uz": "Яхши кўринади",
           "ru": "Выражены хорошо",
           "is_norm": true
          },
          {
           "code": "not_visible",
           "uz": "Яхши кўринмайди",
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
           "uz": "Йўқ",
           "ru": "Нет",
           "is_norm": true
          },
          {
           "code": "marginal",
           "uz": "Чекка",
           "ru": "Краевая"
          },
          {
           "code": "central",
           "uz": "Марказий",
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
           "uz": "Пульсацияловчи рефлекс",
           "ru": "Пульсирующий рефлекс"
          },
          {
           "code": "infiltration",
           "uz": "Инфильтрация",
           "ru": "Инфильтрация"
          },
          {
           "code": "retraction",
           "uz": "Ретраксия",
           "ru": "Втянутость"
          },
          {
           "code": "scars",
           "uz": "Чандиқлар",
           "ru": "Рубцы"
          },
          {
           "code": "calcinates",
           "uz": "Кальцинатлар",
           "ru": "Кальцинаты"
          }
         ]
        }
       ]
      },
      {
       "code": "tympanic_cavity",
       "uz": "Барабан бўшлиғи",
       "ru": "Барабанная полость",
       "needs_perforation": true,
       "fields": [
        {
         "code": "contents",
         "type": "checkbox_multi",
         "options": [
          {
           "code": "pus",
           "uz": "Йиринг",
           "ru": "Гной"
          },
          {
           "code": "granulations",
           "uz": "Грануляциялар",
           "ru": "Грануляции"
          },
          {
           "code": "polyp",
           "uz": "Полип",
           "ru": "Полип"
          },
          {
           "code": "cholesteatoma",
           "uz": "Холестеатома массалари",
           "ru": "Холестеатомные массы"
          },
          {
           "code": "blood",
           "uz": "Қон",
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
     "uz": "Ларингоскопия",
     "ru": "Ларингоскопия",
     "parts": [
      {
       "code": "lingual_tonsil",
       "uz": "Тил бодомсимон бези",
       "ru": "Язычная миндалина",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "not_enlarged",
           "uz": "Катталашмаган",
           "ru": "Не увеличена",
           "is_norm": true
          },
          {
           "code": "enlarged",
           "uz": "Катталашган",
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
           "uz": "Караш йўқ",
           "ru": "Налетов нет",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Гиперемияланган",
           "ru": "Гиперемирована"
          }
         ]
        }
       ]
      },
      {
       "code": "valleculae",
       "uz": "Валлекулалар",
       "ru": "Валлекулы",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "free",
           "uz": "Эркин",
           "ru": "Свободны",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "Ўзгарган",
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
           "uz": "Оқартирилган пушти",
           "ru": "Бледно-розовая",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Гиперемияланган",
           "ru": "Гиперемирована"
          }
         ]
        }
       ]
      },
      {
       "code": "pharynx_walls",
       "uz": "Орқа ва ён деворлар",
       "ru": "Задняя и боковые стенки",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "pale_pink",
           "uz": "Оқартирилган пушти",
           "ru": "Бледно-розовая",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Гиперемияланган",
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
           "uz": "Шишган",
           "ru": "Отечна"
          },
          {
           "code": "infiltrated",
           "uz": "Инфильтрацияланган",
           "ru": "Инфильтрирована"
          }
         ]
        }
       ]
      },
      {
       "code": "external_larynx",
       "uz": "Ҳиқилдоқ ташқи кўриги",
       "ru": "Гортань — наружный осмотр",
       "fields": [
        {
         "code": "contour",
         "type": "radio",
         "options": [
          {
           "code": "well",
           "uz": "Яхши контурланади",
           "ru": "Хорошо контурируется",
           "is_norm": true
          },
          {
           "code": "altered",
           "uz": "Ўзгарган",
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
           "uz": "Пассив ҳаракатчан",
           "ru": "Пассивно подвижна",
           "is_norm": true
          },
          {
           "code": "immobile",
           "uz": "Ҳаракатсиз",
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
           "uz": "Тўғри шаклда",
           "ru": "Правильной формы",
           "is_norm": true
          },
          {
           "code": "deformed",
           "uz": "Деформация",
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
           "uz": "«Тоғай қирсиллаши» манфий",
           "ru": "Симптом «хруста хрящей» отрицательный",
           "is_norm": true
          },
          {
           "code": "positive",
           "uz": "«Тоғай қирсиллаши» мусбат",
           "ru": "Симптом «хруста хрящей» положительный"
          }
         ]
        }
       ]
      },
      {
       "code": "vocal_folds",
       "uz": "Овоз бойламлари",
       "ru": "Голосовые складки",
       "fields": [
        {
         "code": "color",
         "type": "radio",
         "options": [
          {
           "code": "whitish",
           "uz": "Оқартирилган",
           "ru": "Белесоватые",
           "is_norm": true
          },
          {
           "code": "hyperemic",
           "uz": "Гиперемияланган",
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
           "uz": "Тоза",
           "ru": "Чистые",
           "is_norm": true
          },
          {
           "code": "plaques",
           "uz": "Карашлар мавжуд",
           "ru": "Налеты"
          },
          {
           "code": "tumor",
           "uz": "Ўсма",
           "ru": "Новообразование"
          },
          {
           "code": "hypertrophy",
           "uz": "Гипертрофия",
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
           "uz": "Фонацияда тўлиқ ёпилади",
           "ru": "Полностью смыкаются",
           "is_norm": true
          },
          {
           "code": "not_full",
           "uz": "Фонацияда тўлиқ ёпилмайди",
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
           "uz": "Эркин",
           "ru": "Свободные",
           "is_norm": true
          },
          {
           "code": "limited",
           "uz": "Ҳаракати чекланган",
           "ru": "Ограничены в движении"
          },
          {
           "code": "immobile",
           "uz": "Ҳаракатсиз",
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
       "uz": "Овоз",
       "ru": "Голос",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "sonorous",
           "uz": "Жарангдор",
           "ru": "Звучный",
           "is_norm": true
          },
          {
           "code": "hoarse",
           "uz": "Хириллаган",
           "ru": "Хриплый"
          },
          {
           "code": "aphonia",
           "uz": "Афония",
           "ru": "Афония"
          }
         ]
        }
       ]
      },
      {
       "code": "dyspnea",
       "uz": "Ҳансираш",
       "ru": "Одышка",
       "fields": [
        {
         "code": "state",
         "type": "radio",
         "options": [
          {
           "code": "none",
           "uz": "Йўқ",
           "ru": "Нет",
           "is_norm": true
          },
          {
           "code": "present",
           "uz": "Бор",
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
           "uz": "Инспиратор",
           "ru": "Инспираторная"
          },
          {
           "code": "expiratory",
           "uz": "Экспиратор",
           "ru": "Экспираторная"
          },
          {
           "code": "mixed",
           "uz": "Аралаш",
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
           "uz": "Тинч ҳолатда",
           "ru": "В покое"
          },
          {
           "code": "exertion",
           "uz": "Юкламада",
           "ru": "При нагрузке"
          }
         ]
        }
       ]
      },
      {
       "code": "stenosis",
       "uz": "Ҳиқилдоқ стенози",
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
    state: { uz: 'Ҳолати', ru: 'Состояние' },
    deformity_type: { uz: 'Деформация тури', ru: 'Вид деформации' },
    side: { uz: 'Томони', ru: 'Сторона' },
    part: { uz: 'Қисми', ru: 'Отдел' },
    location: { uz: 'Жойлашуви', ru: 'Локализация' },
    branch: { uz: 'Шохлари', ru: 'Ветви' },
    color: { uz: 'Ранги', ru: 'Цвет' },
    moisture: { uz: 'Намлиги', ru: 'Влажность' },
    condition: { uz: 'Ўзгаришлар', ru: 'Изменения' },
    features: { uz: 'Хусусиятлари', ru: 'Особенности' },
    shape: { uz: 'Шакли', ru: 'Форма' },
    pathology: { uz: 'Патологик ўзгаришлар', ru: 'Патологические изменения' },
    pain: { uz: 'Оғриқ', ru: 'Болезненность' },
    visibility: { uz: 'Кўриниши', ru: 'Видимость' },
    hypertrophy_degree: { uz: 'Гипертрофия даражаси', ru: 'Степень гипертрофии' },
    surface: { uz: 'Юзаси', ru: 'Поверхность' },
    lacunae: { uz: 'Лакуналар', ru: 'Лакуны' },
    lacunae_contents: { uz: 'Лакуналар таркиби', ru: 'Содержимое лакун' },
    contents: { uz: 'Таркиби', ru: 'Содержимое' },
    cause: { uz: 'Сабаби', ru: 'Причина' },
    adenoid_degree: { uz: 'Аденоидлар даражаси', ru: 'Степень аденоидов' },
    canal_width: { uz: 'Эшитув йўли кенглиги', ru: 'Ширина слухового прохода' },
    pain_part: { uz: 'Оғриқли қисм', ru: 'Болезненный отдел' },
    landmarks: { uz: 'Таниб олиш белгилари', ru: 'Опознавательные знаки' },
    perforation: { uz: 'Перфорация', ru: 'Перфорация' },
    contour: { uz: 'Контури', ru: 'Контуры' },
    mobility: { uz: 'Ҳаракатчанлиги', ru: 'Подвижность' },
    crepitus: { uz: 'Крепитация', ru: 'Крепитация' },
    closure: { uz: 'Ёпилиши', ru: 'Смыкание' },
    movement: { uz: 'Ҳаракати', ru: 'Движение' },
    type: { uz: 'Тури', ru: 'Тип' },
    when: { uz: 'Қачон', ru: 'Когда' },
    degree: { uz: 'Даражаси', ru: 'Степень' },
  };

  // Tez tanlash uchun tashxislar (XKT-10). Shifokor istalgan matnni ham yozishi mumkin.
  const o = (code, uz, ru) => ({ code, uz, ru });
  const DIAGNOSES = [
    o('J00', 'Ўткир назофарингит', 'Острый назофарингит'),
    o('J01', 'Ўткир синусит', 'Острый синусит'),
    o('J02', 'Ўткир фарингит', 'Острый фарингит'),
    o('J03', 'Ўткир тонзиллит', 'Острый тонзиллит'),
    o('J04.0', 'Ўткир ларингит', 'Острый ларингит'),
    o('J30', 'Вазомотор ва аллергик ринит', 'Вазомоторный и аллергический ринит'),
    o('J31.0', 'Сурункали ринит', 'Хронический ринит'),
    o('J31.2', 'Сурункали фарингит', 'Хронический фарингит'),
    o('J32', 'Сурункали синусит', 'Хронический синусит'),
    o('J33', 'Бурун полипи', 'Полип носа'),
    o('J34.2', 'Бурун тўсиғи қийшиқлиги', 'Искривление носовой перегородки'),
    o('J35.0', 'Сурункали тонзиллит', 'Хронический тонзиллит'),
    o('J35.2', 'Аденоидлар гипертрофияси', 'Гипертрофия аденоидов'),
    o('J37.0', 'Сурункали ларингит', 'Хронический ларингит'),
    o('J38.1', 'Овоз бойлами полипи', 'Полип голосовой складки'),
    o('H60', 'Ташқи отит', 'Наружный отит'),
    o('H61.2', 'Олтингугурт тиқини', 'Серная пробка'),
    o('H65', 'Йирингсиз ўрта отит', 'Негнойный средний отит'),
    o('H66', 'Йирингли ўрта отит', 'Гнойный средний отит'),
    o('H68', 'Евстахиит', 'Евстахиит'),
    o('H72', 'Ноғора парда перфорацияси', 'Перфорация барабанной перепонки'),
    o('H90', 'Эшитиш пасайиши', 'Тугоухость'),
    o('H93.1', 'Қулоқда шовқин (тиннитус)', 'Шум в ушах'),
    o('R04.0', 'Бурундан қон кетиши', 'Носовое кровотечение'),
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
