/*
 * NURMED: LOR shablonlari (shikoyatlar, ajralma turlari, LOR STATUS, tashxislar).
 * Shikoyatlar katalogi eski "Clinic LOR Desktop" dasturidan olingan.
 * LOR STATUS — klinika shabloni: 8 bo'lim (бурун, бурун-ҳалқум, оғиз-ҳалқум, гипофаринкс, ҳиқилдоқ,
 * қулоқлар AD/AS, эшитиш паспорти, вестибуляр паспорт). Barcha matnlar o'zbekcha (kirill) va ruscha.
 *
 * Bu fayl brauzerda (window.LOR) ham, serverda (require) ham ishlatiladi.
 * Server saqlashdan oldin kelgan ma’lumotni shu shablon bo‘yicha tekshiradi.
 *
 * Hech bir maydon avtomatik "norma" deb to‘ldirilmaydi. "Норма" tugmasini shifokor o'zi bosadi.
 *
 * Ma’lumot shakli (qabul yozuvida):
 *   lor_status[metod] = {
 *     parts: { <qism>: { <maydon>: qiymat, _text: 'izoh' } },   // umumiy qismlar (yoki ears bo'lmagan metodning barcha qismlari)
 *     ears:  { AD: { <qism>: {...} }, AS: {...} },             // ears bo'lgan metodlar: har bir tomon alohida
 *     same:  true,                                              // "AD = AS" — faqat birinchi tomon saqlanadi
 *     note:  'bo‘lim izohi',
 *   }
 * Maydon turlari: radio → kod, checkbox_multi → [kodlar], side → left|right|both, degree → none|I|II|III,
 *                 checkbox → true, text → matn.
 * Qism belgilari: common: 'before' | 'after' — ears bo'lgan metodda tomonlarga bo'linmaydigan umumiy qism.
 * Eski shablondagi (rinoskopiya, faringoskopiya, otoskopiya, laringoskopiya) yozuvlar LEGACY_METHODS orqali
 * saqlanadi va hujjatda chiqadi, lekin formada ko'rsatilmaydi.
 */
(function (root, factory) {
  const T = factory();
  if (typeof module === 'object' && module.exports) module.exports = T;
  else root.LOR = T;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const BASE = {"complaints":[{"code":"general","uz":"Умумий шикоятлар","ru":"Общие жалобы","items":[{"code":"gen_headache","uz":"Бош оғриғи","ru":"Головная боль"},{"code":"gen_fever_subfebrile","uz":"Иситма (субфебрил)","ru":"Температура (субфебрильная)"},{"code":"gen_fever_febrile","uz":"Иситма (фебрил)","ru":"Температура (фебрильная)"},{"code":"gen_fever_pyretic","uz":"Иситма (пиретик)","ru":"Температура (пиретическая)"},{"code":"gen_chills","uz":"Қалтираш, эт жунжикиши","ru":"Озноб"},{"code":"gen_weakness","uz":"Умумий ҳолсизлик","ru":"Общая слабость"},{"code":"gen_malaise","uz":"Ўзини ёмон ҳис қилиш","ru":"Недомогание"},{"code":"gen_appetite_loss","uz":"Иштаҳа йўқлиги","ru":"Отсутствие аппетита"},{"code":"gen_dizziness","uz":"Бош айланиши","ru":"Головокружение"},{"code":"gen_nausea","uz":"Кўнгил айниши","ru":"Тошнота"},{"code":"gen_vomiting","uz":"Қусиш","ru":"Рвота"},{"code":"gen_diarrhea","uz":"Ич кетиши","ru":"Диарея"},{"code":"gen_joint_pain","uz":"Бўғимларда оғриқ","ru":"Боль в суставах"},{"code":"gen_back_pain","uz":"Бел соҳасида оғриқ","ru":"Боль в поясничной области"},{"code":"gen_frequent_uri","uz":"Тез-тез ЎРИ","ru":"Частые ОРИ"},{"code":"gen_sleep_disturbance","uz":"Уйқу бузилиши (уйқуда чўчиш)","ru":"Беспокойный сон"}]},{"code":"pharynx","uz":"Ҳалқум","ru":"Глотка","items":[{"code":"pharynx_pain","uz":"Томоқ оғриғи","ru":"Боль в горле"},{"code":"pharynx_swallow_pain","uz":"Ютишда оғриқ","ru":"Боль при глотании"},{"code":"pharynx_speech_pain","uz":"Гапирганда ёки тилни чиқарганда оғриқ","ru":"Боль при разговоре или высовывании языка"},{"code":"pharynx_tickling","uz":"Қирилиш ҳисси","ru":"Першение"},{"code":"pharynx_burning","uz":"Ачишиш","ru":"Жжение"},{"code":"pharynx_itching","uz":"Қичишиш","ru":"Зуд"},{"code":"pharynx_dryness","uz":"Томоқда қуруқлик","ru":"Сухость в горле"},{"code":"pharynx_lump","uz":"«Томоқда тугун» ҳисси","ru":"Чувство «комка»"},{"code":"pharynx_foreign_body","uz":"«Бегона жисм» ҳисси","ru":"Чувство инородного тела"},{"code":"pharynx_swallowing","uz":"Ютишнинг қийинлашиши","ru":"Затрудненное глотание"},{"code":"pharynx_food_sticking","uz":"Овқат тиқилиши, тўш орқасида оғриқ","ru":"Застревание пищи, боль за грудиной"},{"code":"pharynx_discharge","uz":"Ажралма","ru":"Отделяемое","has_discharge_type":true},{"code":"pharynx_salivation","uz":"Сўлак оқиши","ru":"Слюнотечение"},{"code":"pharynx_trismus","uz":"Оғиз очилмаслиги (тризм)","ru":"Затрудненное открывание рта (тризм)"},{"code":"pharynx_halitosis","uz":"Оғиздан ёқимсиз ҳид","ru":"Неприятный запах изо рта"},{"code":"pharynx_tongue_pain","uz":"Тилда оғриқ, ачишиш","ru":"Боль, жжение в языке"},{"code":"pharynx_nasal_voice","uz":"Овоз ғунғиллиги","ru":"Гнусавость голоса"},{"code":"pharynx_frequent_tonsillitis","uz":"Тез-тез ангина","ru":"Частые ангины"},{"code":"pharynx_heart_pain","uz":"Юрак соҳасида оғриқ","ru":"Боль в области сердца"},{"code":"pharynx_neck_pain","uz":"Бўйинда оғриқ","ru":"Боль в шее"},{"code":"pharynx_neck_swelling","uz":"Бўйинда шиш, тугун","ru":"Припухлость, узел на шее"},{"code":"pharynx_heartburn","uz":"Жиғилдон қайнаши, нордон кекириш","ru":"Изжога, отрыжка кислым"}]},{"code":"larynx","uz":"Ҳиқилдоқ","ru":"Гортань","items":[{"code":"larynx_voice_change","uz":"Овоз функциясининг ўзгариши (хириллаш, бўғилиш, овоз йўқолиши)","ru":"Изменение голосовой функции (охриплость, осиплость, афония)"},{"code":"larynx_voice_fatigue","uz":"Овознинг тез чарчаши","ru":"Быстрая утомляемость голоса"},{"code":"larynx_cough","uz":"Йўтал","ru":"Кашель"},{"code":"larynx_hemoptysis","uz":"Қон туфлаш (балғамда қон)","ru":"Кровохарканье"},{"code":"larynx_pain","uz":"Оғриқ","ru":"Боль"},{"code":"larynx_dryness","uz":"Ҳиқилдоқда қуруқлик, қобиқ кўчиши","ru":"Сухость в гортани, отхаркивание корок"},{"code":"larynx_breathing","uz":"Нафас олишнинг қийинлашиши","ru":"Затрудненное дыхание"},{"code":"larynx_stridor","uz":"Бўғилиш хуружи, шовқинли нафас","ru":"Приступ удушья, шумное дыхание"}]},{"code":"nose","uz":"Бурун ва ёндош бурун бўшлиқлари","ru":"Нос и околоносовые пазухи","items":[{"code":"nose_congestion","uz":"Бурун битиши","ru":"Заложенность носа"},{"code":"nose_breathing","uz":"Бурун орқали нафас олишнинг қийинлашиши","ru":"Затруднение дыхания через нос"},{"code":"nose_discharge","uz":"Бурундан ажралма келиши","ru":"Выделения из носа","has_discharge_type":true},{"code":"nose_bleeding","uz":"Бурундан қон кетиши","ru":"Носовое кровотечение"},{"code":"nose_smell_loss","uz":"Ҳид билишнинг пасайиши ёки йўқлиги","ru":"Снижение или отсутствие обоняния"},{"code":"nose_dryness","uz":"Бурунда қуруқлик, қатқалоқлар","ru":"Сухость, корки в носу"},{"code":"nose_odor","uz":"Бурундан ёқимсиз ҳид","ru":"Неприятный запах из носа"},{"code":"nose_sneezing","uz":"Аксириш","ru":"Чихание"},{"code":"nose_lacrimation","uz":"Кўз ёшланиши","ru":"Слезотечение"},{"code":"nose_itching","uz":"Бурунда қичишиш","ru":"Зуд в носу"},{"code":"nose_pain","uz":"Бурун оғриғи","ru":"Боль в носу"},{"code":"nose_burning","uz":"Бурунда ачишиш","ru":"Жжение в носу"},{"code":"nose_sinus_pain","uz":"Бурун ёндош бўшлиқлари проекциясида оғриқ (ёноқ, пешона, кўз атрофи)","ru":"Боль в проекции околоносовых пазух (щека, лоб, область глаз)"},{"code":"nose_face_heaviness","uz":"Юз соҳасида оғирлик ҳисси","ru":"Тяжесть в области лица"},{"code":"nose_trigeminal_pain","uz":"Уч шохли нервнинг I–II шохлари чиқиш нуқталарида оғриқ","ru":"Болезненность точек выхода I–II ветвей тройничного нерва"},{"code":"nose_external_swelling","uz":"Ташқи бурун шиши, қизариши","ru":"Припухлость, покраснение наружного носа"},{"code":"nose_face_edema","uz":"Қовоқ, ёноқ, юқори лаб шиши","ru":"Отёк век, щеки, верхней губы"},{"code":"nose_eye_bulge","uz":"Кўз ички бурчагида бўртма","ru":"Выпячивание у внутреннего угла глаза"},{"code":"nose_cosmetic","uz":"Косметик нуқсон ёки ҳосила","ru":"Косметический дефект, образования"},{"code":"nose_snoring","uz":"Хуррак","ru":"Храп"},{"code":"nose_mouth_breathing","uz":"Оғиз орқали нафас олиш","ru":"Дыхание через рот"},{"code":"nose_enuresis","uz":"Тунги энурез (сийдик тута олмаслик)","ru":"Ночное недержание мочи"},{"code":"nose_foreign_body","uz":"Бурунга бегона жисм тушиши","ru":"Попадание инородного тела в нос"}]},{"code":"ear","uz":"Қулоқ","ru":"Уши","items":[{"code":"ear_pain","uz":"Қулоқда оғриқ","ru":"Боль в ухе"},{"code":"ear_retroauricular","uz":"Қулоқ орқасида оғриқ, шиш","ru":"Боль, припухлость в заушной области"},{"code":"ear_auricle_pain","uz":"Қулоқ супраси оғриғи ва шиши","ru":"Боль, припухлость ушной раковины"},{"code":"ear_burning","uz":"Қулоқ супрасида ачишиш","ru":"Жжение в области ушной раковины"},{"code":"ear_itching","uz":"Қулоқда қичишиш","ru":"Зуд в ухе"},{"code":"ear_noise","uz":"Қулоқда шовқин","ru":"Шум в ушах"},{"code":"ear_hearing_loss","uz":"Эшитиш пасайиши","ru":"Снижение слуха"},{"code":"ear_congestion","uz":"Қулоқ битиши","ru":"Заложенность уха"},{"code":"ear_fluid","uz":"Қулоқда суюқлик чайқалиши","ru":"Ощущение переливания жидкости в ухе"},{"code":"ear_fullness","uz":"Қулоқда тўлиб туриш (босим) ҳисси","ru":"Чувство распирания в ухе"},{"code":"ear_discharge","uz":"Қулоқдан ажралма келиши","ru":"Выделения из уха","has_discharge_type":true},{"code":"ear_fb_sensation","uz":"Қулоқда бегона жисм ҳисси","ru":"Ощущение инородного тела в ухе"},{"code":"ear_foreign_body","uz":"Қулоққа бегона жисм тушиши","ru":"Попадание инородного тела в ухо"},{"code":"ear_discomfort","uz":"Қулоқда ноқулайлик ҳисси","ru":"Чувство дискомфорта"},{"code":"ear_cosmetic","uz":"Қулоқ супрасида косметик нуқсон (шалпанг қулоқлик, деформация, ўсма, отогематома)","ru":"Ушная раковина — косметический дефект (лопоухость, деформация, новообразование, отогематома)"},{"code":"ear_imbalance","uz":"Мувозанат бузилиши, юришда чайқалиш","ru":"Нарушение равновесия, шаткость походки"},{"code":"ear_facial_asymmetry","uz":"Юз асимметрияси","ru":"Асимметрия лица"},{"code":"ear_facial_numbness","uz":"Юзда увишиш, таъм сезишнинг пасайиши","ru":"Онемение лица, снижение вкуса"}]}],"discharge":[{"code":"purulent","uz":"Йирингли","ru":"Гнойное"},{"code":"serous","uz":"Сероз","ru":"Серозное"},{"code":"mucous","uz":"Шиллиқ","ru":"Слизистое"},{"code":"mucopurulent","uz":"Шиллиқ-йирингли","ru":"Слизисто-гнойное"},{"code":"bloody","uz":"Қонли","ru":"Кровянистое"},{"code":"sanguineous","uz":"Сувли-қонли","ru":"Сукровичное"},{"code":"caseous","uz":"Казеоз","ru":"Казеозное"},{"code":"watery","uz":"Сувли","ru":"Водянистое"},{"code":"other","uz":"Бошқа","ru":"Другое","requires_text":true}],"sides":[{"code":"left","uz":"Чапда","ru":"Слева"},{"code":"right","uz":"Ўнгда","ru":"Справа"},{"code":"both","uz":"Икки томонда","ru":"С обеих сторон"}],"degrees":[{"code":"none","uz":"Йўқ","ru":"Нет","is_norm":true},{"code":"I","uz":"I даража","ru":"I ст."},{"code":"II","uz":"II даража","ru":"II ст."},{"code":"III","uz":"III даража","ru":"III ст."}],"legacy":[{"code":"rhinoscopy","uz":"Риноскопия","ru":"Риноскопия","parts":[{"code":"external_nose","uz":"Ташқи бурун","ru":"Наружный нос","fields":[{"code":"state","type":"radio","options":[{"code":"unchanged","uz":"Ўзгармаган","ru":"Не изменен","is_norm":true},{"code":"deformed","uz":"Деформация","ru":"Деформация"}]},{"code":"deformity_type","type":"checkbox_multi","when":{"state":"deformed"},"options":[{"code":"sunken","uz":"Чўкиш","ru":"Западение"},{"code":"hump","uz":"Букрилик","ru":"Горбинка"},{"code":"scoliosis","uz":"Сколиоз","ru":"Сколиоз"}]},{"code":"side","type":"side","when":{"state":"deformed"}},{"code":"part","type":"radio","when":{"state":"deformed"},"options":[{"code":"bone","uz":"Суяк қисми","ru":"Костная часть"},{"code":"cartilage","uz":"Тоғай қисми","ru":"Хрящевая часть"}]},{"code":"location","type":"checkbox_multi","when":{"state":"deformed"},"options":[{"code":"dorsum","uz":"Бурун орқаси","ru":"Спинка"},{"code":"wings","uz":"Қанотлари","ru":"Крылья"},{"code":"tip","uz":"Учи","ru":"Кончик"},{"code":"nostrils","uz":"Бурун тешиклари","ru":"Ноздри"}]}]},{"code":"trigeminal","uz":"Уч шохли нерв чиқиш нуқталари","ru":"Точки выхода тройничного нерва","fields":[{"code":"state","type":"radio","options":[{"code":"painless","uz":"Оғриқсиз","ru":"Безболезненны","is_norm":true},{"code":"painful","uz":"Оғриқли","ru":"Болезненны"}]},{"code":"side","type":"side","when":{"state":"painful"}},{"code":"branch","type":"checkbox_multi","when":{"state":"painful"},"options":[{"code":"I","uz":"I шох","ru":"I ветвь"},{"code":"II","uz":"II шох","ru":"II ветвь"},{"code":"III","uz":"III шох","ru":"III ветвь"}]}]},{"code":"breathing","uz":"Бурун орқали нафас олиш","ru":"Дыхание через нос","fields":[{"code":"state","type":"radio","options":[{"code":"free","uz":"Эркин","ru":"Свободное","is_norm":true},{"code":"difficult","uz":"Қийинлашган","ru":"Затруднено"},{"code":"absent","uz":"Мавжуд эмас","ru":"Отсутствует"}]},{"code":"side","type":"side","when":{"state":["difficult","absent"]}}]},{"code":"vestibule","uz":"Бурун даҳлизи","ru":"Преддверие","fields":[{"code":"state","type":"radio","options":[{"code":"unchanged","uz":"Ўзгармаган","ru":"Не изменено","is_norm":true},{"code":"narrowed","uz":"Торайган","ru":"Сужено"}]},{"code":"side","type":"side","when":{"state":"narrowed"}}]},{"code":"olfaction","uz":"Ҳид билиш","ru":"Обоняние","fields":[{"code":"state","type":"radio","options":[{"code":"preserved","uz":"Сақланган","ru":"Сохранено","is_norm":true},{"code":"hyposmia","uz":"Гипосмия","ru":"Гипосмия"},{"code":"anosmia","uz":"Аносмия","ru":"Аносмия"},{"code":"hyperosmia","uz":"Гиперосмия","ru":"Гиперосмия"}]},{"code":"side","type":"side","when":{"state":["hyposmia","anosmia","hyperosmia"]}}]},{"code":"mucosa","uz":"Шиллиқ қават","ru":"Слизистая оболочка","fields":[{"code":"color","type":"radio","options":[{"code":"pink","uz":"Пушти","ru":"Розовая","is_norm":true},{"code":"pale_pink","uz":"Оқартирилган пушти","ru":"Бледно-розовая"},{"code":"bluish","uz":"Кўкимтир","ru":"Синюшная"},{"code":"hyperemic","uz":"Гиперемияланган","ru":"Гиперемирована"}]},{"code":"moisture","type":"radio","options":[{"code":"moist","uz":"Нам","ru":"Влажная","is_norm":true},{"code":"dry","uz":"Қуруқ","ru":"Сухая"}]},{"code":"condition","type":"checkbox_multi","options":[{"code":"hypertrophied","uz":"Гипертрофияланган","ru":"Гипертрофирована"},{"code":"ulcerated","uz":"Яраланган","ru":"Изъязвлена"}]},{"code":"location","type":"checkbox_multi","options":[{"code":"septum","uz":"Бурун тўсиғи соҳаси","ru":"Область перегородки носа"},{"code":"turbinate_inferior","uz":"Пастки чиғаноқ","ru":"Нижняя носовая раковина"},{"code":"turbinate_middle","uz":"Ўрта чиғаноқ","ru":"Средняя носовая раковина"},{"code":"turbinate_superior","uz":"Юқори чиғаноқ","ru":"Верхняя носовая раковина"},{"code":"meatus_inferior","uz":"Пастки бурун йўли","ru":"Нижний носовой ход"},{"code":"meatus_middle","uz":"Ўрта бурун йўли","ru":"Средний носовой ход"},{"code":"meatus_superior","uz":"Юқори бурун йўли","ru":"Верхний носовой ход"},{"code":"end_anterior","uz":"Олдинги учи","ru":"Передний конец"},{"code":"end_posterior","uz":"Орқа учи","ru":"Задний конец"}]}]},{"code":"septum","uz":"Бурун тўсиғи","ru":"Носовая перегородка","fields":[{"code":"state","type":"radio","options":[{"code":"midline","uz":"Ўрта чизиқда","ru":"По средней линии","is_norm":true},{"code":"curved","uz":"Қийшайган","ru":"Искривлена"}]},{"code":"features","type":"checkbox_multi","when":{"state":"curved"},"options":[{"code":"bulge","uz":"Бўртма","ru":"Бугор"},{"code":"ridge","uz":"Қирра","ru":"Гребень"},{"code":"spike","uz":"Тиканча","ru":"Шип"}]},{"code":"shape","type":"radio","when":{"state":"curved"},"options":[{"code":"c_shaped","uz":"C-симон","ru":"С-образно"},{"code":"s_shaped","uz":"S-симон","ru":"S-образно"}]},{"code":"side","type":"side","when":{"state":"curved"}},{"code":"part","type":"radio","when":{"state":"curved"},"options":[{"code":"cartilage","uz":"Тоғай қисмида","ru":"В хрящевом отделе"},{"code":"bone","uz":"Суяк қисмида","ru":"В костном отделе"}]}]}]},{"code":"pharyngoscopy","uz":"Фарингоскопия","ru":"Фарингоскопия","parts":[{"code":"mouth_opening","uz":"Оғиз очилиши","ru":"Открывание рта","fields":[{"code":"state","type":"radio","options":[{"code":"free","uz":"Эркин","ru":"Свободное","is_norm":true},{"code":"trismus","uz":"Тризм","ru":"Тризм"},{"code":"painful","uz":"Оғриқли","ru":"Болезненное"}]}]},{"code":"oral_mucosa","uz":"Оғиз шиллиқ қавати","ru":"Слизистая оболочка полости рта","fields":[{"code":"color","type":"radio","options":[{"code":"pale_pink","uz":"Оқартирилган пушти","ru":"Бледно-розовая","is_norm":true},{"code":"hyperemic","uz":"Гиперемияланган","ru":"Гиперемирована"}]},{"code":"pathology","type":"checkbox_multi","options":[{"code":"aphthae","uz":"Афталар","ru":"Афты"},{"code":"ulcers","uz":"Яралар","ru":"Язвы"}]},{"code":"location","type":"checkbox_multi","options":[{"code":"tongue","uz":"Тил","ru":"Язык"},{"code":"soft_palate","uz":"Юмшоқ танглай","ru":"Мягкое небо"},{"code":"mouth_floor","uz":"Оғиз туби","ru":"Дно полости рта"}]}]},{"code":"tongue","uz":"Тил","ru":"Язык","fields":[{"code":"state","type":"radio","options":[{"code":"clean","uz":"Тоза, нам","ru":"Чистый, влажный","is_norm":true},{"code":"white_coat","uz":"Оқ караш билан қопланган","ru":"Обложен белым налетом"}]},{"code":"pathology","type":"checkbox_multi","options":[{"code":"aphtha","uz":"Афта","ru":"Афта"},{"code":"ulcer","uz":"Яра","ru":"Язва"},{"code":"infiltration","uz":"Инфильтрация","ru":"Инфильтрация"}]},{"code":"pain","type":"radio","options":[{"code":"none","uz":"Оғриқ йўқ","ru":"Безболезненный","is_norm":true},{"code":"present","uz":"Оғриқли","ru":"Болезненный"}]},{"code":"side","type":"side","when":{"pain":"present"}}]},{"code":"teeth","uz":"Тишлар","ru":"Зубы","fields":[{"code":"state","type":"radio","options":[{"code":"healthy","uz":"Соғлом","ru":"Здоровы","is_norm":true},{"code":"sanitized","uz":"Санация қилинган","ru":"Санированы"},{"code":"caries","uz":"Кариес","ru":"Кариес"}]},{"code":"prostheses","type":"checkbox","uz":"Протезлар мавжуд","ru":"Протезы имеются"}]},{"code":"palatine_arches","uz":"Танглай ёйлари","ru":"Небные дужки","fields":[{"code":"visibility","type":"radio","options":[{"code":"well_visible","uz":"Яхши кўринади","ru":"Хорошо контурируются","is_norm":true},{"code":"altered","uz":"Ўзгарган","ru":"Изменены"}]},{"code":"pathology","type":"checkbox_multi","options":[{"code":"edema","uz":"Шишган","ru":"Отечны"},{"code":"hyperemic","uz":"Гиперемияланган","ru":"Гиперемированы"},{"code":"infiltrated","uz":"Инфильтрацияланган","ru":"Инфильтрированы"},{"code":"adherent","uz":"Бодомсимон без билан ёпишган","ru":"Спаяны с миндалиной"}]},{"code":"features","type":"checkbox_multi","options":[{"code":"cushion","uz":"Ёстиқсимон бўртиш","ru":"Подушкообразное выпячивание"},{"code":"hiss_fold","uz":"Гисс бурмаси қалинлашган","ru":"Складка Гиса утолщена"}]}]},{"code":"palatine_tonsils","uz":"Танглай бодомсимон безлари","ru":"Небные миндалины","fields":[{"code":"state","type":"radio","options":[{"code":"not_protruding","uz":"Танглай ёйидан чиқмайди","ru":"Не выступают из-за дужек","is_norm":true},{"code":"hypertrophied","uz":"Гипертрофия","ru":"Гипертрофия"}]},{"code":"hypertrophy_degree","type":"degree","when":{"state":"hypertrophied"}},{"code":"surface","type":"radio","options":[{"code":"smooth","uz":"Силлиқ","ru":"Гладкая","is_norm":true},{"code":"bumpy","uz":"Ғадир-будир","ru":"Бугристая"}]},{"code":"lacunae","type":"radio","options":[{"code":"not_dilated","uz":"Лакуналар кенгаймаган","ru":"Лакуны не расширены","is_norm":true},{"code":"dilated","uz":"Лакуналар кенгайган","ru":"Лакуны расширены"}]},{"code":"lacunae_contents","type":"checkbox_multi","options":[{"code":"none","uz":"Йўқ","ru":"Нет","is_norm":true},{"code":"caseous_plugs","uz":"Казеоз тиқинлар","ru":"Казеозные пробки"},{"code":"purulent_plugs","uz":"Йирингли тиқинлар","ru":"Гнойные пробки"},{"code":"mucous_plugs","uz":"Шиллиқ тиқинлар","ru":"Слизистые пробки"},{"code":"pus","uz":"Йиринг","ru":"Гной"},{"code":"mucus","uz":"Шиллиқ","ru":"Слизь"}]}]},{"code":"posterior_pharynx","uz":"Ҳалқум орқа девори","ru":"Задняя стенка глотки","fields":[{"code":"state","type":"radio","options":[{"code":"pink_smooth","uz":"Пушти, силлиқ","ru":"Розовая, гладкая","is_norm":true},{"code":"altered","uz":"Ўзгарган","ru":"Изменена"}]},{"code":"pathology","type":"checkbox_multi","options":[{"code":"granules_hyper","uz":"Лимфоид гранулалар гипертрофияси","ru":"Гипертрофия лимфоидных гранул"},{"code":"lateral_hyper","uz":"Ён валиклар гипертрофияси","ru":"Гипертрофия боковых валиков"},{"code":"atrophy","uz":"Атрофия","ru":"Атрофия"}]},{"code":"contents","type":"checkbox_multi","options":[{"code":"pus","uz":"Йиринг","ru":"Гной"},{"code":"crusts","uz":"Қобиқлар","ru":"Корки"},{"code":"mucus","uz":"Шиллиқ","ru":"Слизь"},{"code":"blood","uz":"Қон","ru":"Кровь"}]}]},{"code":"pharyngeal_reflex","uz":"Ҳалқум рефлекси","ru":"Глоточный рефлекс","fields":[{"code":"state","type":"radio","options":[{"code":"preserved","uz":"Сақланган","ru":"Сохранен","is_norm":true},{"code":"reduced","uz":"Пасайган","ru":"Снижен"},{"code":"elevated","uz":"Юқори","ru":"Высокий"}]}]},{"code":"posterior_choanae","uz":"Хоаналар (орқа риноскопия)","ru":"Хоаны (задняя риноскопия)","fields":[{"code":"state","type":"radio","options":[{"code":"free","uz":"Эркин","ru":"Свободны","is_norm":true},{"code":"closed","uz":"Ёпилган","ru":"Закрыты"}]},{"code":"cause","type":"checkbox_multi","when":{"state":"closed"},"options":[{"code":"turbinate_hyper_inf","uz":"Пастки чиғаноқлар гипертрофияси","ru":"Гипертрофия нижних раковин"},{"code":"turbinate_hyper_mid","uz":"Ўрта чиғаноқлар гипертрофияси","ru":"Гипертрофия средних раковин"},{"code":"polyp","uz":"Полип","ru":"Полип"},{"code":"tumor","uz":"Ўсма","ru":"Новообразование"},{"code":"adenoids","uz":"Аденоидлар","ru":"Аденоиды"}]}]},{"code":"posterior_vault","uz":"Гумбаз","ru":"Свод","fields":[{"code":"state","type":"radio","options":[{"code":"free","uz":"Эркин","ru":"Свободен","is_norm":true},{"code":"tumor","uz":"Ўсма","ru":"Новообразование"},{"code":"adenoids","uz":"Аденоидлар","ru":"Аденоиды"}]},{"code":"adenoid_degree","type":"degree","when":{"state":"adenoids"}}]},{"code":"auditory_tubes","uz":"Эшитув найлари оғзи","ru":"Устья слуховых труб","fields":[{"code":"state","type":"radio","options":[{"code":"well_visible","uz":"Яхши кўринади, эркин","ru":"Хорошо контурируются, свободны","is_norm":true},{"code":"narrowed","uz":"Торайган","ru":"Сужены"}]},{"code":"contents","type":"checkbox_multi","options":[{"code":"mucus","uz":"Шиллиқ","ru":"Слизь"},{"code":"pus","uz":"Йиринг","ru":"Гной"}]},{"code":"hypertrophy","type":"checkbox","uz":"Най валиклари ва бодомсимон безлар гипертрофияси","ru":"Гипертрофия трубных валиков и миндалин"}]}]},{"code":"otoscopy","uz":"Отоскопия (AD/AS)","ru":"Отоскопия (AD/AS)","ears":[{"code":"AD","uz":"AD (ўнг)","ru":"AD (правое)"},{"code":"AS","uz":"AS (чап)","ru":"AS (левое)"}],"parts":[{"code":"auricle_canal","uz":"Қулоқ супраси ва ташқи эшитув йўли","ru":"Ушная раковина и наружный слуховой проход","fields":[{"code":"shape","type":"radio","options":[{"code":"normal","uz":"Тўғри шаклда","ru":"Правильной формы","is_norm":true},{"code":"altered","uz":"Ўзгарган","ru":"Изменена"}]},{"code":"canal_width","type":"radio","options":[{"code":"normal","uz":"Нормал","ru":"Нормальный","is_norm":true},{"code":"wide","uz":"Кенг","ru":"Широкий"},{"code":"narrow","uz":"Тор","ru":"Узкий"}]},{"code":"pathology","type":"checkbox_multi","options":[{"code":"exostosis","uz":"Экзостоз","ru":"Экзостоз"},{"code":"pain","uz":"Оғриқли","ru":"Болезненный"},{"code":"infiltration","uz":"Инфильтрация","ru":"Инфильтрация"},{"code":"hyperemia","uz":"Гиперемия","ru":"Гиперемия"}]},{"code":"pain_part","type":"radio","when":{"pathology":"pain"},"options":[{"code":"bone","uz":"Суяк қисми","ru":"Костная часть"},{"code":"cartilage","uz":"Тоғай қисми","ru":"Хрящевая часть"}]},{"code":"contents","type":"checkbox_multi","options":[{"code":"clean","uz":"Тоза","ru":"Свободный","is_norm":true},{"code":"cerumen","uz":"Олтингугурт","ru":"Сера"},{"code":"crusts","uz":"Қобиқлар","ru":"Корки"},{"code":"plug","uz":"Тиқин","ru":"Пробка"},{"code":"pus","uz":"Йиринг","ru":"Гной"},{"code":"blood","uz":"Қон","ru":"Кровь"},{"code":"films","uz":"Пардалар","ru":"Пленки"}]}]},{"code":"tympanic_membrane","uz":"Барабан пардаси","ru":"Барабанная перепонка","fields":[{"code":"color","type":"radio","options":[{"code":"pearly_gray","uz":"Марваридсимон кулранг","ru":"Перламутрово-серая","is_norm":true},{"code":"hyperemic","uz":"Гиперемияланган","ru":"Гиперемирована"}]},{"code":"landmarks","type":"radio","options":[{"code":"visible","uz":"Яхши кўринади","ru":"Выражены хорошо","is_norm":true},{"code":"not_visible","uz":"Яхши кўринмайди","ru":"Не выражены"}]},{"code":"perforation","type":"radio","options":[{"code":"none","uz":"Йўқ","ru":"Нет","is_norm":true},{"code":"marginal","uz":"Чекка","ru":"Краевая"},{"code":"central","uz":"Марказий","ru":"Некраевая (центральная)"}]},{"code":"pathology","type":"checkbox_multi","options":[{"code":"pulsating","uz":"Пульсацияловчи рефлекс","ru":"Пульсирующий рефлекс"},{"code":"infiltration","uz":"Инфильтрация","ru":"Инфильтрация"},{"code":"retraction","uz":"Ретраксия","ru":"Втянутость"},{"code":"scars","uz":"Чандиқлар","ru":"Рубцы"},{"code":"calcinates","uz":"Кальцинатлар","ru":"Кальцинаты"}]}]},{"code":"tympanic_cavity","uz":"Барабан бўшлиғи","ru":"Барабанная полость","needs_perforation":true,"fields":[{"code":"contents","type":"checkbox_multi","options":[{"code":"pus","uz":"Йиринг","ru":"Гной"},{"code":"granulations","uz":"Грануляциялар","ru":"Грануляции"},{"code":"polyp","uz":"Полип","ru":"Полип"},{"code":"cholesteatoma","uz":"Холестеатома массалари","ru":"Холестеатомные массы"},{"code":"blood","uz":"Қон","ru":"Кровь"}]}]}]},{"code":"laryngoscopy","uz":"Ларингоскопия","ru":"Ларингоскопия","parts":[{"code":"lingual_tonsil","uz":"Тил бодомсимон бези","ru":"Язычная миндалина","fields":[{"code":"state","type":"radio","options":[{"code":"not_enlarged","uz":"Катталашмаган","ru":"Не увеличена","is_norm":true},{"code":"enlarged","uz":"Катталашган","ru":"Увеличена"}]},{"code":"features","type":"checkbox_multi","options":[{"code":"no_plaque","uz":"Караш йўқ","ru":"Налетов нет","is_norm":true},{"code":"hyperemic","uz":"Гиперемияланган","ru":"Гиперемирована"}]}]},{"code":"valleculae","uz":"Валлекулалар","ru":"Валлекулы","fields":[{"code":"state","type":"radio","options":[{"code":"free","uz":"Эркин","ru":"Свободны","is_norm":true},{"code":"altered","uz":"Ўзгарган","ru":"Изменены"}]},{"code":"color","type":"radio","options":[{"code":"pale_pink","uz":"Оқартирилган пушти","ru":"Бледно-розовая","is_norm":true},{"code":"hyperemic","uz":"Гиперемияланган","ru":"Гиперемирована"}]}]},{"code":"pharynx_walls","uz":"Орқа ва ён деворлар","ru":"Задняя и боковые стенки","fields":[{"code":"color","type":"radio","options":[{"code":"pale_pink","uz":"Оқартирилган пушти","ru":"Бледно-розовая","is_norm":true},{"code":"hyperemic","uz":"Гиперемияланган","ru":"Гиперемирована"}]},{"code":"pathology","type":"checkbox_multi","options":[{"code":"edema","uz":"Шишган","ru":"Отечна"},{"code":"infiltrated","uz":"Инфильтрацияланган","ru":"Инфильтрирована"}]}]},{"code":"external_larynx","uz":"Ҳиқилдоқ ташқи кўриги","ru":"Гортань — наружный осмотр","fields":[{"code":"contour","type":"radio","options":[{"code":"well","uz":"Яхши контурланади","ru":"Хорошо контурируется","is_norm":true},{"code":"altered","uz":"Ўзгарган","ru":"Изменена"}]},{"code":"mobility","type":"radio","options":[{"code":"passive_mobile","uz":"Пассив ҳаракатчан","ru":"Пассивно подвижна","is_norm":true},{"code":"immobile","uz":"Ҳаракатсиз","ru":"Неподвижна"}]},{"code":"shape","type":"radio","options":[{"code":"normal","uz":"Тўғри шаклда","ru":"Правильной формы","is_norm":true},{"code":"deformed","uz":"Деформация","ru":"Деформирована"}]},{"code":"crepitus","type":"radio","options":[{"code":"negative","uz":"«Тоғай қирсиллаши» манфий","ru":"Симптом «хруста хрящей» отрицательный","is_norm":true},{"code":"positive","uz":"«Тоғай қирсиллаши» мусбат","ru":"Симптом «хруста хрящей» положительный"}]}]},{"code":"vocal_folds","uz":"Овоз бойламлари","ru":"Голосовые складки","fields":[{"code":"color","type":"radio","options":[{"code":"whitish","uz":"Оқартирилган","ru":"Белесоватые","is_norm":true},{"code":"hyperemic","uz":"Гиперемияланган","ru":"Гиперемированы"}]},{"code":"state","type":"radio","options":[{"code":"clean","uz":"Тоза","ru":"Чистые","is_norm":true},{"code":"plaques","uz":"Карашлар мавжуд","ru":"Налеты"},{"code":"tumor","uz":"Ўсма","ru":"Новообразование"},{"code":"hypertrophy","uz":"Гипертрофия","ru":"Гипертрофия"}]},{"code":"closure","type":"radio","options":[{"code":"full","uz":"Фонацияда тўлиқ ёпилади","ru":"Полностью смыкаются","is_norm":true},{"code":"not_full","uz":"Фонацияда тўлиқ ёпилмайди","ru":"Полностью не смыкаются"}]},{"code":"movement","type":"radio","options":[{"code":"free","uz":"Эркин","ru":"Свободные","is_norm":true},{"code":"limited","uz":"Ҳаракати чекланган","ru":"Ограничены в движении"},{"code":"immobile","uz":"Ҳаракатсиз","ru":"Неподвижны"}]},{"code":"side","type":"side","when":{"state":["plaques","tumor","hypertrophy"]}}]},{"code":"voice","uz":"Овоз","ru":"Голос","fields":[{"code":"state","type":"radio","options":[{"code":"sonorous","uz":"Жарангдор","ru":"Звучный","is_norm":true},{"code":"hoarse","uz":"Хириллаган","ru":"Хриплый"},{"code":"aphonia","uz":"Афония","ru":"Афония"}]}]},{"code":"dyspnea","uz":"Ҳансираш","ru":"Одышка","fields":[{"code":"state","type":"radio","options":[{"code":"none","uz":"Йўқ","ru":"Нет","is_norm":true},{"code":"present","uz":"Бор","ru":"Есть"}]},{"code":"type","type":"radio","when":{"state":"present"},"options":[{"code":"inspiratory","uz":"Инспиратор","ru":"Инспираторная"},{"code":"expiratory","uz":"Экспиратор","ru":"Экспираторная"},{"code":"mixed","uz":"Аралаш","ru":"Смешанная"}]},{"code":"when","type":"radio","when":{"state":"present"},"options":[{"code":"rest","uz":"Тинч ҳолатда","ru":"В покое"},{"code":"exertion","uz":"Юкламада","ru":"При нагрузке"}]}]},{"code":"stenosis","uz":"Ҳиқилдоқ стенози","ru":"Стеноз гортани","fields":[{"code":"degree","type":"degree"}]}]}]};
  const { complaints: COMPLAINTS, discharge: DISCHARGE, sides: SIDES, degrees: DEGREES } = BASE;
  const LEGACY_METHODS = BASE.legacy.map((m) => ({ ...m, legacy: true }));

  /* Shikoyatlar kimning so'zidan yozilgan (bola yoki og'ir bemor uchun): tugma va hujjatdagi matn */
  const REL = (code, uz, ru, from_uz, from_ru) => ({ code, uz, ru, from: { uz: from_uz, ru: from_ru } });
  const RELATIVES = [
    REL('mother', 'Онаси', 'Мать', 'онасининг сўзидан', 'со слов матери'),
    REL('father', 'Отаси', 'Отец', 'отасининг сўзидан', 'со слов отца'),
    REL('sister', 'Опаси', 'Старшая сестра', 'опасининг сўзидан', 'со слов старшей сестры'),
    REL('brother', 'Акаси', 'Старший брат', 'акасининг сўзидан', 'со слов старшего брата'),
    REL('grandfather', 'Бобоси', 'Дедушка', 'бобосининг сўзидан', 'со слов дедушки'),
    REL('grandmother', 'Бувиси', 'Бабушка', 'бувисининг сўзидан', 'со слов бабушки'),
    REL('uncle', 'Амакиси', 'Дядя', 'амакисининг сўзидан', 'со слов дяди'),
    REL('aunt_maternal', 'Холаси', 'Тётя (по матери)', 'холасининг сўзидан', 'со слов тёти (по матери)'),
    REL('aunt_paternal', 'Аммаси', 'Тётя (по отцу)', 'аммасининг сўзидан', 'со слов тёти (по отцу)'),
  ];
  const relative = (code) => RELATIVES.find((r) => r.code === code) || null;

  /* ================= LOR STATUS shabloni (8 bo'lim) ================= */
  const o = (code, uz, ru) => ({ code, uz, ru });
  const n = (code, uz, ru) => ({ code, uz, ru, is_norm: true });
  const R = (code, uz, ru, options, x = {}) => ({ code, type: 'radio', uz, ru, options, ...x });
  const M = (code, uz, ru, options, x = {}) => ({ code, type: 'checkbox_multi', uz, ru, options, ...x });
  const T = (code, uz, ru, x = {}) => ({ code, type: 'text', uz, ru, ...x });
  const SIDE = (when) => ({ code: 'side', type: 'side', uz: 'Томони', ru: 'Сторона', when });
  const P = (code, uz, ru, fields, x = {}) => ({ code, uz, ru, fields, ...x });
  const w = (field, ...values) => ({ [field]: values });
  const ph = (uz, ru) => ({ ph: { uz, ru } });

  const PAINLESS = n('painless', 'Оғриқсиз', 'Безболезненны');
  const PAINFUL = o('painful', 'Оғриқли', 'Болезненны');
  const NO = n('no', 'Йўқ', 'Нет');
  const YES = o('yes', 'Бор', 'Есть');
  const POS = n('pos', 'Мусбат (+)', 'Положительный (+)');
  const NEG = o('neg', 'Манфий (−)', 'Отрицательный (−)');
  const DEG3 = [o('I', 'I даража', 'I степени'), o('II', 'II даража', 'II степени'), o('III', 'III даража', 'III степени')];
  const OK_MISS = [n('ok', 'Аниқ бажаради', 'Выполняет точно'), o('miss', 'Мўлжалдан адашади', 'Промахивание')];

  /** Regionar limfa tugunlari (har bir bo'limda o'z guruhlari) */
  const lymph = (uz, ru) => P('lymph', `Регионар лимфа тугунлари (${uz})`, `Регионарные лимфоузлы (${ru})`, [
    R('state', 'Ҳолати', 'Состояние', [n('not_palp', 'Пайпасланмайди', 'Не пальпируются'), o('palp', 'Пайпасланади', 'Пальпируются')]),
    T('size', 'Ўлчами (см)', 'Размер (см)', { when: w('state', 'palp') }),
    R('consistency', 'Консистенцияси', 'Консистенция', [o('soft', 'Юмшоқ', 'Мягкая'), o('elastic', 'Эластик', 'Эластичная'), o('dense', 'Зич', 'Плотная')], { when: w('state', 'palp') }),
    R('pain', 'Оғриқ', 'Болезненность', [o('painless', 'Оғриқсиз', 'Безболезненны'), o('painful', 'Оғриқли', 'Болезненны')], { when: w('state', 'palp') }),
    R('mobility', 'Ҳаракатчанлиги', 'Подвижность', [o('mobile', 'Ҳаракатчан', 'Подвижны'), o('fixed', 'Атрофга ёпишган', 'Спаяны')], { when: w('state', 'palp') }),
  ]);

  const DISCH_NASAL = ['mucous', 'mucopurulent', 'purulent', 'serous', 'bloody'];

  const RAW_METHODS = [
    /* ---------- 1. Бурун ва бурун ёндош бўшлиқлари ---------- */
    {
      code: 'nose', uz: 'Риноскопия (бурун ва бурун ёндош бўшлиқлари)', ru: 'Риноскопия (нос и околоносовые пазухи)', print: { uz: 'Риноскопия', ru: 'Риноскопия' },
      parts: [
        P('ext_shape', 'Ташқи бурун шакли', 'Форма наружного носа', [
          R('state', 'Ҳолати', 'Состояние', [n('regular', 'Тўғри', 'Правильная'), o('changed', 'Ўзгарган', 'Изменена')]),
          M('deform', 'Ўзгариш', 'Изменение', [o('dev_r', 'Бурун қирраси ўнгга қийшайган', 'Искривление спинки вправо'),
            o('dev_l', 'Бурун қирраси чапга қийшайган', 'Искривление спинки влево'), o('saddle', 'Эгарсимон деформация', 'Седловидная деформация'),
            o('wide', 'Кенг бурун қирраси', 'Широкая спинка'), o('edema', 'Юмшоқ тўқималар шиши', 'Отёк мягких тканей')], { when: w('state', 'changed'), bare: true }),
        ]),
        P('ext_skin', 'Бурун ва бўшлиқлар проекцияси териси', 'Кожные покровы носа и области проекции пазух', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Одатий рангда', 'Обычной окраски'), o('hyperemic', 'Гиперемияланган, шишган', 'Гиперемированы, отёчны')]),
          T('area', 'Соҳа', 'В области', { when: w('state', 'hyperemic') }),
        ]),
        P('palp_nose', 'Ташқи бурун пальпацияси', 'Пальпация наружного носа', [
          R('state', 'Ҳолати', 'Состояние', [n('painless', 'Оғриқсиз, крепитация ва суяк бўлакларининг силжиши йўқ', 'Безболезненна, крепитации и смещения костных отломков нет'),
            o('painful', 'Оғриқли', 'Болезненна'), o('crepitus', 'Оғриқли, крепитация бор', 'Болезненна, крепитация')]),
        ]),
        P('palp_sinus', 'Бўшлиқлар пальпацияси ва перкуссияси (пешона, юқори жағ, ғалвирсимон лабиринт)', 'Пальпация и перкуссия пазух (лобные, верхнечелюстные, решётчатый лабиринт)', [
          R('state', 'Ҳолати', 'Состояние', [PAINLESS, PAINFUL]),
          SIDE(w('state', 'painful')),
          M('area', 'Соҳа', 'В области', [o('frontal', 'Пешона бўшлиғи', 'Лобной пазухи'), o('maxillary', 'Юқори жағ бўшлиғи', 'Верхнечелюстной пазухи'),
            o('ethmoid', 'Ғалвирсимон лабиринт', 'Решётчатого лабиринта')], { when: w('state', 'painful') }),
        ]),
        P('trigeminal', 'Уч шохли нерв I ва II шохлари чиқиш нуқталари', 'Точки выхода I и II ветвей тройничного нерва', [
          R('state', 'Ҳолати', 'Состояние', [PAINLESS, PAINFUL]), SIDE(w('state', 'painful')),
        ]),
        P('breathing', 'Бурун орқали нафас (пахта синамаси)', 'Носовое дыхание (проба с ваткой)', [
          ...[['r', 'Ўнгда', 'Справа'], ['l', 'Чапда', 'Слева']].map(([s, uz, ru]) => R(`breath_${s}`, uz, ru, [n('free', 'Эркин', 'Свободное'),
            o('moderate', 'Ўртача қийинлашган', 'Умеренно затруднено'), o('severe', 'Кескин қийинлашган', 'Резко затруднено'), o('absent', 'Йўқ', 'Отсутствует')])),
          R('position', 'Тана ҳолатига боғлиқлик', 'Зависимость от положения тела', [n('no', 'Йўқ', 'Нет'),
            o('yes', 'Бемор ётган томонда битиш кучаяди', 'Заложенность усиливается на стороне, на которой лежит больной')]),
        ]),
        P('olfaction', 'Ҳид билиш', 'Обоняние', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Сақланган (нормосмия)', 'Сохранено (нормосмия)'),
            o('hypo', 'Пасайган (гипосмия)', 'Снижено (гипосмия)'), o('anosmia', 'Йўқ (аносмия)', 'Отсутствует (аносмия)')]),
          SIDE(w('state', 'hypo', 'anosmia')),
        ]),
        P('vestibule', 'Бурун даҳлизи', 'Преддверие носа', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин, териси ўзгармаган, туклар билан қопланган', 'Свободное, кожа не изменена, покрыта волосами'), o('changed', 'Ўзгарган', 'Изменено')]),
          M('changes', 'Ўзгаришлар', 'Изменения', [o('infiltrate', 'Инфильтрат', 'Инфильтрат'), o('furuncle', 'Фурункул', 'Фурункул'),
            o('cracks', 'Ёриқлар', 'Трещины'), o('crusts', 'Қобиқлар', 'Корки')], { when: w('state', 'changed'), bare: true }),
          SIDE(w('state', 'changed')),
          T('size', 'Ўлчами (см)', 'Размер (см)', { when: w('state', 'changed') }),
        ]),
        P('septum', 'Бурун тўсиғи', 'Носовая перегородка', [
          R('state', 'Ҳолати', 'Состояние', [n('midline', 'Ўрта чизиқда', 'По средней линии'), o('curved', 'Қийшайган', 'Искривлена')]),
          SIDE(w('state', 'curved')),
          R('shape', 'Шакли', 'Форма', [o('simple', 'Оддий', 'Простое'), o('s_shaped', 'S-симон', 'S-образно')], { when: w('state', 'curved') }),
          R('part', 'Бўлими', 'Отдел', [o('cartilage', 'Олдинги (тоғай) бўлимида', 'В переднем (хрящевом) отделе'),
            o('bone', 'Орқа (суяк) бўлимида', 'В заднем (костном) отделе')], { when: w('state', 'curved'), bare: true }),
          M('features', 'Хусусиятлари', 'Особенности', [o('crest', 'Қирра', 'Гребень'), o('spur', 'Тиканча', 'Шип'),
            o('subluxation', 'Тўрт бурчакли тоғай чиқиши', 'Подвывих четырёхугольного хряща')], { when: w('state', 'curved'), bare: true }),
          T('size', 'Ўлчами (см)', 'Размер (см)', { when: w('state', 'curved') }),
        ]),
        P('mucosa', 'Шиллиқ қават', 'Слизистая оболочка', [
          R('color', 'Ранги', 'Цвет', [n('pink', 'Пушти', 'Розовая'), o('hyperemic', 'Гиперемияланган', 'Гиперемирована'),
            o('pale', 'Оқиш', 'Бледная'), o('cyanotic', 'Кўкимтир (цианотик)', 'Синюшная (цианотичная)')], { bare: true }),
          M('state', 'Ҳолати', 'Состояние', [n('moist', 'Нам, силлиқ', 'Влажная, гладкая'), o('dry', 'Қуруқ, юпқалашган, қобиқли', 'Сухая, истончена, с корками'),
            o('edema', 'Шишган', 'Отёчна')]),
          R('voyachek', 'Воячек доғлари', 'Пятна Воячека', [NO, YES]),
        ]),
        P('turbinates', 'Бурун чиғаноқлари (пастки, ўрта)', 'Носовые раковины (нижние, средние)', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Катталашмаган', 'Не увеличены'), o('edema', 'Шиш ҳисобига катталашган', 'Увеличены за счёт отёка'),
            o('hypertrophy', 'Гипертрофияланган', 'Гипертрофированы')]),
          SIDE(w('state', 'edema', 'hypertrophy')),
          R('anemization', 'Анемизация синамаси (томирни торайтирувчи томчилар)', 'Проба с анемизацией (сосудосуживающие капли)', [
            o('good', 'Яхши қисқаради, ўтказувчанлик тикланади', 'Хорошо сокращаются, проходимость восстанавливается'),
            o('slight', 'Бироз қисқаради', 'Сокращаются незначительно'), o('none', 'Қисқармайди', 'Не сокращаются')]),
        ]),
        P('passages', 'Бурун йўллари (умумий, пастки, ўрта)', 'Носовые ходы (общий, нижний, средний)', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин', 'Свободны'), o('narrowed', 'Торайган', 'Сужены')]), SIDE(w('state', 'narrowed')),
        ]),
        P('discharge', 'Ажралма', 'Отделяемое', [
          R('state', 'Тури', 'Характер', [n('none', 'Йўқ', 'Нет'), o('mucous', 'Шиллиқ', 'Слизистое'), o('mucopurulent', 'Шиллиқ-йирингли', 'Слизисто-гнойное'),
            o('purulent', 'Йирингли', 'Гнойное'), o('serous', 'Сероз', 'Серозное'), o('bloody', 'Қон аралаш', 'Кровянистое')]),
          M('where', 'Жойи', 'Локализация', [o('common', 'Умумий бурун йўлида', 'В общем носовом ходе'), o('middle', 'Ўрта бурун йўлида', 'В среднем носовом ходе'),
            o('lower', 'Пастки бурун йўлида', 'В нижнем носовом ходе')], { when: w('state', ...DISCH_NASAL), bare: true }),
          SIDE(w('state', ...DISCH_NASAL)),
          { code: 'stripe', type: 'checkbox', uz: 'Ўрта чиғаноқ остидан йиринг йўлакчаси', ru: 'Полоска гноя из-под средней носовой раковины', when: w('state', ...DISCH_NASAL) },
        ]),
        P('neoplasm', 'Ҳосилалар', 'Новообразования', [
          R('state', 'Ҳолати', 'Состояние', [n('none', 'Йўқ', 'Нет'),
            o('polyps', 'Кулранг, силлиқ, эластик, ҳаракатчан, зондлашда оғриқсиз полиплар ўрта бурун йўлида', 'Полипы серого цвета, гладкие, эластичные, подвижные, безболезненные при зондировании, в среднем носовом ходе'),
            o('other', 'Бошқа ҳосила', 'Иное образование')]),
          SIDE(w('state', 'polyps', 'other')),
          T('desc', 'Тавсифи (ўлчами, ранги, қонаши)', 'Описание (размер, цвет, кровоточивость)', { when: w('state', 'other') }),
        ]),
        lymph('жағ ости, қулоқ олди', 'поднижнечелюстные, предушные'),
      ],
    },

    /* ---------- 2. Бурун-ҳалқум ---------- */
    {
      code: 'nasopharynx', uz: 'Эпифарингоскопия (бурун-ҳалқум, орқа риноскопия)', ru: 'Эпифарингоскопия (носоглотка, задняя риноскопия)', print: { uz: 'Эпифарингоскопия', ru: 'Эпифарингоскопия' },
      parts: [
        P('vault', 'Бурун-ҳалқум гумбази', 'Свод носоглотки', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин', 'Свободен'), o('adenoids', 'Лимфоид тўқима (аденоид вегетациялар) бор', 'Содержит лимфоидную ткань (аденоидные вегетации)')]),
          R('degree', 'Даражаси', 'Степень', [o('I', 'I даража (сошникнинг 1/3 қисмини ёпади)', 'I степени (прикрывают сошник на 1/3)'),
            o('II', 'II даража (сошникнинг 2/3 қисмини ёпади)', 'II степени (прикрывают сошник на 2/3)'), o('III', 'III даража (сошникни тўлиқ ёпади)', 'III степени (прикрывают сошник полностью)')],
          { when: w('state', 'adenoids'), bare: true }),
        ]),
        P('mucosa', 'Шиллиқ қават', 'Слизистая оболочка', [
          R('color', 'Ранги', 'Цвет', [n('pink', 'Пушти, нам', 'Розовая, влажная'), o('hyperemic', 'Гиперемияланган', 'Гиперемирована'), o('pale', 'Оқиш', 'Бледная')]),
        ]),
        P('choanae', 'Хоаналар', 'Хоаны', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин', 'Свободны'), o('partial', 'Қисман ёпилган', 'Частично перекрыты'), o('full', 'Тўлиқ ёпилган', 'Полностью перекрыты')]),
          M('cause', 'Сабаби', 'Чем', [o('polyp', 'Полип', 'Полипом'), o('turbinates', 'Чиғаноқларнинг гипертрофияланган орқа учлари', 'Гипертрофированными задними концами раковин'),
            o('adenoids', 'Аденоидлар', 'Аденоидами')], { when: w('state', 'partial', 'full') }),
          SIDE(w('state', 'partial', 'full')),
        ]),
        P('vomer', 'Сошник', 'Сошник', [R('state', 'Ҳолати', 'Состояние', [n('midline', 'Ўрта чизиқда', 'По средней линии'), o('deviated', 'Оғган', 'Отклонён')])]),
        P('post_ends', 'Пастки бурун чиғаноқларининг орқа учлари', 'Задние концы нижних носовых раковин', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Катталашмаган', 'Не увеличены'), o('hyper', 'Гипертрофияланган, хоаналардан чиқиб туради', 'Гипертрофированы, выступают из хоан')]),
          SIDE(w('state', 'hyper')),
        ]),
        P('tubes', 'Эшитув найларининг ҳалқум тешиклари ва най валиклари', 'Глоточные отверстия слуховых труб и трубные валики', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Ажралиб туради, эркин', 'Дифференцируются, свободны'), o('adenoid', 'Аденоид тўқима билан ёпилган', 'Прикрыты аденоидной тканью'),
            o('edema', 'Шишган', 'Отёчны')]),
          R('discharge', 'Тешик олдида ажралма', 'Отделяемое у устья', [NO, YES]),
          SIDE(w('discharge', 'yes')),
        ]),
        P('postnasal', 'Ҳалқум орқа девори бўйлаб ажралма оқиши', 'Стекание отделяемого по задней стенке глотки', [
          R('state', 'Ҳолати', 'Состояние', [n('none', 'Йўқ', 'Нет'), o('mucous', 'Шиллиқ', 'Слизистое'), o('purulent', 'Йирингли', 'Гнойное')]),
        ]),
      ],
    },

    /* ---------- 3. Оғиз бўшлиғи ва оғиз-ҳалқум ---------- */
    {
      code: 'oropharynx', uz: 'Мезофарингоскопия (оғиз бўшлиғи ва оғиз-ҳалқум)', ru: 'Мезофарингоскопия (полость рта и ротоглотка)', print: { uz: 'Мезофарингоскопия', ru: 'Мезофарингоскопия' },
      parts: [
        P('mouth', 'Оғиз очилиши', 'Рот открывается', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин', 'Свободно'), o('trismus', 'Чекланган (тризм)', 'С ограничением (тризм)')]),
          R('degree', 'Тризм даражаси', 'Степень тризма', DEG3, { when: w('state', 'trismus') }),
        ]),
        P('lips', 'Лабларнинг қизил ҳошияси', 'Красная кайма губ', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Одатий рангда, ёриқларсиз', 'Обычной окраски, без трещин'), o('changed', 'Ўзгарган', 'Изменена')]),
        ]),
        P('oral_mucosa', 'Лунж, милк, қаттиқ танглай шиллиқ қавати', 'Слизистая оболочка щёк, дёсен, твёрдого нёба', [
          M('state', 'Ҳолати', 'Состояние', [n('normal', 'Пушти, нам, тоза', 'Розовая, влажная, чистая'), o('hyperemic', 'Гиперемияланган', 'Гиперемирована'),
            o('plaque', 'Карашлар билан', 'С налётами'), o('ulcer', 'Яраланган', 'С изъязвлениями')]),
          T('desc', 'Тавсифи', 'Описание', { when: w('state', 'plaque', 'ulcer') }),
        ]),
        P('ducts', 'Сўлак безлари чиқариш йўллари оғизлари', 'Устья выводных протоков слюнных желёз', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин', 'Свободны'), o('changed', 'Ўзгарган', 'Изменены')]),
        ]),
        P('teeth', 'Тишлар', 'Зубы', [
          M('state', 'Ҳолати', 'Состояние', [n('sanitized', 'Санация қилинган', 'Санированы'), o('caries', 'Кариесли тишлар бор', 'Кариозные зубы'),
            o('missing', 'Тишлар йўқ', 'Отсутствуют зубы')]),
          T('caries_list', 'Кариесли тишлар', 'Кариозные', { when: w('state', 'caries') }),
          T('missing_list', 'Йўқ тишлар', 'Отсутствуют', { when: w('state', 'missing') }),
          T('formula', 'Тиш формуласи', 'Зубная формула', ph('87654321 | 12345678', '87654321 | 12345678')),
        ]),
        P('tongue', 'Тил', 'Язык', [
          M('state', 'Ҳолати', 'Состояние', [n('normal', 'Одатий ўлчамда, нам, тоза, сўрғичлари ифодаланган', 'Обычных размеров, влажный, чистый, сосочки выражены'),
            o('coated', 'Оқ караш билан қопланган', 'Обложен белым налётом'), o('dry', 'Қуруқ', 'Сухой')]),
        ]),
        P('soft_palate', 'Юмшоқ танглай', 'Мягкое нёбо', [
          R('state', 'Ҳолати', 'Состояние', [n('symmetric', 'Симметрик, фонацияда ҳаракатчан', 'Симметрично, подвижно при фонации'), o('asym', 'Асимметрик', 'Асимметрично')]),
          M('changes', 'Ўзгаришлар', 'Изменения', [o('bulging', 'Бўртиб чиқиш', 'Выбухание'), o('infiltration', 'Инфильтрация', 'Инфильтрация')], { when: w('state', 'asym'), bare: true }),
          SIDE(w('state', 'asym')),
        ]),
        P('uvula', 'Тилча', 'Язычок', [
          R('state', 'Ҳолати', 'Состояние', [n('midline', 'Ўрта чизиқда', 'По средней линии'), o('shifted', 'Сурилган', 'Смещён')]),
          SIDE(w('state', 'shifted')),
          { code: 'edema', type: 'checkbox', uz: 'Шишган', ru: 'Отёчен' },
        ]),
        P('arches', 'Танглай ёйлари', 'Нёбные дужки', [
          M('state', 'Ҳолати', 'Состояние', [n('normal', 'Контурланади, пушти', 'Контурируются, розовые'), o('hyperemic', 'Гиперемияланган, шишган', 'Гиперемированы, отёчны'),
            o('thickened', 'Олдинги ёйларнинг эркин қирраси қалинлашган', 'Утолщены по свободному краю передних дужек'), o('scar', 'Чандиқли ўзгарган', 'Рубцово изменены')]),
        ]),
        P('tonsils', 'Танглай бодомча безлари', 'Нёбные миндалины', [
          R('state', 'Ҳолати', 'Состояние', [n('behind', 'Ёйлар орқасида', 'За дужками'), o('hyper', 'Гипертрофия', 'Гипертрофия'),
            o('removed', 'Олиб ташланган (тонзиллэктомия)', 'Удалены (тонзиллэктомия)')]),
          R('degree_r', 'Ўнгда', 'Справа', DEG3, { when: w('state', 'hyper') }),
          R('degree_l', 'Чапда', 'Слева', DEG3, { when: w('state', 'hyper') }),
          T('year', 'Операция йили', 'Год операции', { when: w('state', 'removed') }),
          R('surface', 'Юзаси', 'Поверхность', [n('smooth', 'Силлиқ', 'Гладкая'), o('loose', 'Ғовак', 'Рыхлая')], { when: w('state', 'behind', 'hyper') }),
          R('color', 'Ранги', 'Цвет', [n('pink', 'Пушти', 'Розовый'), o('hyperemic', 'Гиперемияланган', 'Гиперемирован'), o('starry', '«Юлдузли осмон»', '«Звёздное небо»')],
            { when: w('state', 'behind', 'hyper') }),
          R('adhesions', 'Ёйлар билан битишмалар', 'Спайки с дужками', [NO, YES], { when: w('state', 'behind', 'hyper') }),
          R('lacunae', 'Лакуналар', 'Лакуны', [n('normal', 'Кенгаймаган', 'Не расширены'), o('wide', 'Кенгайган', 'Расширены')], { when: w('state', 'behind', 'hyper') }),
          R('contents', 'Олдинги ёйга шпатель билан босилганда лакуналар таркиби', 'Содержимое лакун при надавливании шпателем на переднюю дужку', [
            n('none', 'Йўқ', 'Нет'), o('pus', 'Суюқ йиринг', 'Жидкий гной'), o('caseous', 'Казеоз массалар', 'Казеозные массы'), o('mucous', 'Шиллиқ', 'Слизистое')],
          { when: w('state', 'behind', 'hyper') }),
          R('plaque', 'Карашлар', 'Налёты', [NO, YES], { when: w('state', 'behind', 'hyper') }),
          T('plaque_desc', 'Карашлар тавсифи (ранги, кўчадими, кўчирилгандан сўнг қонаши)', 'Описание налётов (цвет, снимаются ли, кровоточивость после снятия)',
            { when: w('plaque', 'yes') }),
        ]),
        P('post_wall', 'Ҳалқум орқа девори', 'Задняя стенка глотки', [
          M('state', 'Ҳолати', 'Состояние', [n('normal', 'Пушти, нам, силлиқ', 'Розовая, влажная, гладкая'), o('hyperemic', 'Гиперемияланган', 'Гиперемирована'),
            o('atrophic', 'Қуруқ, оқиш, юпқалашган', 'Сухая, бледная, истончена'), o('granules', 'Гипертрофияланган лимфоид гранулалар билан', 'С гипертрофированными лимфоидными гранулами'),
            o('mucus', 'Шиллиқ оқиб тушади', 'Стекает слизь')]),
        ]),
        P('reflex', 'Ҳалқум рефлекси', 'Глоточный рефлекс', [
          R('state', 'Ҳолати', 'Состояние', [n('preserved', 'Сақланган', 'Сохранён'), o('reduced', 'Пасайган', 'Снижен'), o('increased', 'Ошган', 'Повышен')]),
        ]),
        lymph('жағ орқаси, жағ ости, бўйиннинг чуқур', 'позадичелюстные, поднижнечелюстные, глубокие шейные'),
      ],
    },

    /* ---------- 4. Ҳиқилдоқ-ҳалқум ---------- */
    {
      code: 'hypopharynx', uz: 'Гипофарингоскопия (ҳиқилдоқ-ҳалқум)', ru: 'Гипофарингоскопия (гортаноглотка)', print: { uz: 'Гипофарингоскопия', ru: 'Гипофарингоскопия' },
      parts: [
        P('lingual', 'Тил илдизи, тил бодомча бези', 'Корень языка, язычная миндалина', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Катталашмаган', 'Не увеличена'), o('hyper', 'Гипертрофияланган', 'Гипертрофирована')]),
          T('size', 'Ўлчами (мм)', 'Размер (мм)', { when: w('state', 'hyper') }),
        ]),
        P('valleculae', 'Валлекулалар', 'Валлекулы', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин', 'Свободны'), o('contents', 'Таркиби бор', 'Содержат')]),
          T('desc', 'Таркиби', 'Содержимое', { when: w('state', 'contents') }),
        ]),
        P('piriform', 'Нок симон синуслар', 'Грушевидные синусы', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин, фонацияда очилади', 'Свободны, раскрываются при фонации'), o('changed', 'Ўзгарган', 'Изменены')]),
          M('changes', 'Ўзгаришлар', 'Изменения', [o('saliva', 'Сўлак «кўллари»', 'Слюнные «озёра»'), o('foreign', 'Ёт жисм', 'Инородное тело'), o('mass', 'Ҳосила', 'Образование')],
            { when: w('state', 'changed'), bare: true }),
          SIDE(w('state', 'changed')),
        ]),
        P('walls', 'Орқа ва ён деворлар шиллиқ қавати', 'Слизистая оболочка задней и боковых стенок', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Пушти, силлиқ', 'Розовая, гладкая'), o('changed', 'Ўзгарган', 'Изменена')]),
          T('desc', 'Ўзгаришлар', 'Изменения', { when: w('state', 'changed') }),
        ]),
      ],
    },

    /* ---------- 5. Ҳиқилдоқ ---------- */
    {
      code: 'larynx', uz: 'Ларингоскопия (ҳиқилдоқ)', ru: 'Ларингоскопия (гортань)', print: { uz: 'Ларингоскопия', ru: 'Ларингоскопия' },
      parts: [
        P('voice', 'Овоз', 'Голос', [
          R('state', 'Ҳолати', 'Состояние', [n('clear', 'Жарангдор', 'Звучный'), o('hoarse', 'Хириллаган', 'Охриплый'), o('husky', 'Бўғиқ', 'Осиплый'),
            o('dull', 'Хира', 'Глухой'), o('aphonia', 'Афония', 'Афония')]),
        ]),
        P('breathing', 'Нафас', 'Дыхание', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин', 'Свободное'), o('difficult', 'Қийинлашган', 'Затруднено')]),
          M('signs', 'Белгилари', 'Признаки', [o('stridor', 'Стридор', 'Стридор'), o('insp', 'Инспиратор ҳансираш', 'Инспираторная одышка')], { when: w('state', 'difficult'), bare: true }),
        ]),
        P('neck', 'Бўйин', 'Шея', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Кўринарли ўзгаришларсиз', 'Без видимых изменений'), o('scar', 'Операциядан кейинги чандиқ', 'Послеоперационный рубец')]),
          T('scar_desc', 'Узунлиги (см), жойи', 'Длина (см), область', { when: w('state', 'scar') }),
        ]),
        P('external', 'Ҳиқилдоқ (ташқи кўрик ва пальпация)', 'Гортань (наружный осмотр и пальпация)', [
          R('config', 'Конфигурацияси', 'Конфигурация', [n('normal', 'Ўзгармаган', 'Не изменена'), o('changed', 'Ўзгарган', 'Изменена')]),
          R('mobility', 'Ҳаракатчанлиги', 'Подвижность', [n('mobile', 'Пассив ҳаракатчан, оғриқсиз', 'Пассивно подвижна, безболезненна'),
            o('painful', 'Оғриқли', 'Болезненна'), o('immobile', 'Ҳаракатсиз', 'Неподвижна')]),
          R('crepitus', 'Тоғайлар крепитацияси (хруст) симптоми', 'Симптом крепитации (хруста) хрящей', [n('pos', 'Мусбат', 'Положительный'), o('neg', 'Манфий', 'Отрицательный')]),
        ]),
        lymph('ҳиқилдоқ олди, трахея олди, трахея ёни, бўйиннинг чуқур', 'преларингеальные, претрахеальные, паратрахеальные, глубокие шейные'),
        P('epiglottis', 'Ҳиқилдоқ усти тоғайи (билвосита ларингоскопия)', 'Надгортанник (непрямая ларингоскопия)', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Очилган япроқ шаклида, шиллиғи пушти', 'В виде развёрнутого лепестка, слизистая розовая'),
            o('hyperemic', 'Гиперемияланган, инфильтрацияланган', 'Гиперемирован, инфильтрирован'), o('folded', 'Буралган', 'Свёрнут')]),
        ]),
        P('aryepi', 'Чўмичсимон-ҳиқилдоқ усти бурмалари, чўмичсимон тоғайлар, улар оралиғи', 'Черпалонадгортанные складки, черпаловидные хрящи, межчерпаловидное пространство', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Пушти, силлиқ, инфильтрацияланмаган', 'Розовые, гладкие, не инфильтрированы'), o('changed', 'Ўзгарган', 'Изменены')]),
          T('desc', 'Ўзгаришлар', 'Изменения', { when: w('state', 'changed') }),
        ]),
        P('vestibular', 'Вестибуляр (сохта) бурмалар', 'Вестибулярные (ложные) складки', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Пушти, ўзгармаган', 'Розовые, не изменены'), o('changed', 'Гиперемияланган, гипертрофияланган', 'Гиперемированы, гипертрофированы')]),
        ]),
        P('vocal', 'Овоз (чин) бурмалари', 'Голосовые (истинные) складки', [
          R('color', 'Ранги', 'Цвет', [n('white', 'Садафсимон-оқ', 'Перламутрово-белые'), o('hyperemic', 'Гиперемияланган', 'Гиперемированы'), o('grey', 'Кулранг', 'Серые')]),
          R('edges', 'Қирралари', 'Края', [n('even', 'Текис', 'Ровные'), o('thick', 'Қалинлашган', 'Утолщены'), o('nodules', 'Тугунчалар', 'Узелки'),
            o('polyp', 'Полип', 'Полип'), o('mass', 'Ҳосила', 'Образование')]),
          T('edge_loc', 'Жойи (учдан бир қисм, томон)', 'Локализация (треть, сторона)', { when: w('edges', 'nodules', 'polyp', 'mass') }),
          R('mobility', 'Ҳаракатчанлиги', 'Подвижность', [n('full', 'Симметрик, тўлиқ ҳажмда', 'Симметричная, в полном объёме'), o('limited', 'Чекланган', 'Ограничена'),
            o('absent', 'Йўқ', 'Отсутствует')]),
          SIDE(w('mobility', 'limited', 'absent')),
          R('position', 'Бурма ҳолати', 'Положение складки', [o('median', 'Ўрта', 'Срединное'), o('paramedian', 'Парамедиан', 'Парамедианное'),
            o('intermediate', 'Оралиқ', 'Промежуточное')], { when: w('mobility', 'absent') }),
          R('closure', 'Фонацияда ёпилиши', 'Смыкание при фонации', [n('full', 'Тўлиқ', 'Полное'), o('incomplete', 'Тўлиқ эмас', 'Неполное')]),
          T('gap', 'Ёриқ шакли', 'Форма щели', { when: w('closure', 'incomplete') }),
        ]),
        P('glottis', 'Нафас олишда овоз ёриғи', 'Голосовая щель при вдохе', [
          R('state', 'Ҳолати', 'Состояние', [n('wide', 'Кенг, учбурчак шаклида', 'Широкая, треугольной формы'), o('narrow', 'Торайган', 'Сужена')]),
          T('mm', 'Кенглиги (мм)', 'Ширина (мм)'),
        ]),
        P('subglottic', 'Бурма ости бўшлиғи ва кўринадиган трахея ҳалқалари', 'Подскладочное пространство и видимые кольца трахеи', [
          R('state', 'Ҳолати', 'Состояние', [n('free', 'Эркин, ўзгаришсиз', 'Свободны, без изменений'), o('changed', 'Ўзгарган', 'Изменены')]),
          T('desc', 'Ўзгаришлар', 'Изменения', { when: w('state', 'changed') }),
        ]),
      ],
    },

    /* ---------- 6. Қулоқлар (AD / AS) ---------- */
    {
      code: 'ears', uz: 'Отоскопия (қулоқлар)', ru: 'Отоскопия (уши)', print: { uz: 'Отоскопия', ru: 'Отоскопия' },
      ears: [{ code: 'AD', uz: 'AD (ўнг қулоқ)', ru: 'AD (правое ухо)', short: { uz: 'AD', ru: 'AD' } },
        { code: 'AS', uz: 'AS (чап қулоқ)', ru: 'AS (левое ухо)', short: { uz: 'AS', ru: 'AS' } }],
      same_toggle: true,
      same_label: { uz: 'AD = AS (иккала қулоқ бир хил, битта қулоқ тавсифланади)', ru: 'AD = AS (уши одинаковы, описывается одно ухо)' },
      same_print: { uz: 'AD = AS', ru: 'AD = AS' },
      parts: [
        P('auricle', 'Қулоқ супраси', 'Ушная раковина', [
          M('state', 'Ҳолати', 'Состояние', [n('normal', 'Тўғри шаклда, териси ўзгармаган', 'Правильной формы, кожа не изменена'), o('deformed', 'Деформацияланган', 'Деформирована'),
            o('hyperemic', 'Гиперемияланган', 'Гиперемирована'), o('edema', 'Шишган', 'Отёчна')]),
        ]),
        P('mastoid', 'Қулоқ орқаси соҳаси, сўрғичсимон ўсиқ', 'Заушная область, сосцевидный отросток', [
          R('state', 'Ҳолати', 'Состояние', [n('normal', 'Ўзгармаган, пальпация ва перкуссия оғриқсиз', 'Не изменены, пальпация и перкуссия безболезненны'),
            o('painful', 'Оғриқли', 'Болезненность'), o('postop', 'Операциядан кейинги чандиқ, операциядан кейинги бўшлиққа кириш', 'Послеоперационный рубец, вход в послеоперационную полость')]),
          M('area', 'Соҳа', 'В области', [o('antrum', 'Антрум майдончаси', 'Площадки антрума'), o('sigmoid', 'Сигмасимон синус соҳаси', 'Области сигмовидного синуса'),
            o('apex', 'Учи', 'Верхушки'), o('pastose', 'Пастозлик, қулоқ орқаси бурмаси текисланган', 'Пастозность, сглаженность заушной складки')], { when: w('state', 'painful') }),
        ]),
        P('tragus', 'Козелок', 'Козелок', [
          R('state', 'Ҳолати', 'Состояние', [n('painless', 'Босилганда оғриқсиз', 'Надавливание безболезненно'), o('painful', 'Босилганда оғриқли', 'Надавливание болезненно')]),
        ]),
        P('canal', 'Ташқи эшитув йўли', 'Наружный слуховой проход', [
          R('width', 'Кенглиги', 'Ширина', [n('wide', 'Кенг', 'Широкий'), o('narrowed', 'Торайган', 'Сужен')], { bare: true }),
          R('narrow_part', 'Бўлими', 'Отдел', [o('cart', 'Тоғай бўлимида', 'В хрящевом отделе'), o('bone', 'Суяк бўлимида', 'В костном отделе')], { when: w('width', 'narrowed'), bare: true }),
          T('narrow_cause', 'Сабаби', 'За счёт', { when: w('width', 'narrowed') }),
          R('skin', 'Териси', 'Кожа', [n('normal', 'Ўзгармаган', 'Не изменена'), o('infiltrated', 'Инфильтрацияланган', 'Инфильтрирована'), o('macerated', 'Мацерацияланган', 'Мацерирована')]),
          R('contents', 'Таркиби', 'Содержимое', [n('wax', 'Оз миқдорда олтингугурт', 'Небольшое количество серы'), o('plug', 'Олтингугурт тиқини', 'Серная пробка'),
            o('mucopurulent', 'Шиллиқ-йирингли ажралма', 'Слизисто-гнойное отделяемое'), o('purulent', 'Йирингли ажралма', 'Гнойное отделяемое'),
            o('epidermal', 'Эпидермал массалар', 'Эпидермальные массы'), o('mass', 'Ҳосила', 'Образование')]),
          R('smell', 'Ҳиди', 'Запах', [o('no', 'Ҳидсиз', 'Без запаха'), o('yes', 'Ҳидли', 'С запахом')], { when: w('contents', 'mucopurulent', 'purulent'), bare: true }),
        ]),
        P('tm', 'Ноғора парда (эшитув йўли тозалангандан сўнг)', 'Барабанная перепонка (после туалета слухового прохода)', [
          R('color', 'Ранги', 'Цвет', [n('grey', 'Садафсимон тусли кулранг', 'Серая с перламутровым оттенком'), o('hyperemic', 'Гиперемияланган', 'Гиперемирована'),
            o('dull', 'Хира', 'Мутная'), o('yellow', 'Сарғиш', 'Желтоватая'), o('cyanotic', 'Кўкимтир', 'Синюшная')]),
          R('position', 'Ҳолати', 'Положение', [n('neutral', 'Нейтрал', 'Нейтральное'), o('retracted', 'Ичкарига тортилган', 'Втянута'), o('bulging', 'Бўртиб чиққан', 'Выбухает')]),
          R('landmarks', 'Таниб олиш белгилари (болғачанинг калта ўсиғи ва дастаси, бурмалар, киндик, ёруғлик конуси)',
            'Опознавательные пункты (короткий отросток и рукоятка молоточка, складки, пупок, световой конус)', [
              n('clear', 'Аниқ кўринади', 'Чётко определяются'), o('smoothed', 'Текисланган', 'Сглажены'), o('cone', 'Ёруғлик конуси калталашган ёки йўқ', 'Световой конус укорочен, отсутствует')]),
          R('perforation', 'Перфорация', 'Перфорация', [n('none', 'Йўқ', 'Нет'), o('central', 'Марказий', 'Центральная'), o('marginal', 'Чекка', 'Краевая'), o('total', 'Тотал', 'Тотальная')]),
          R('perf_part', 'Қисми', 'Часть', [o('tensa', 'Таранг қисм (pars tensa)', 'Натянутая часть (pars tensa)'), o('flaccida', 'Таранг бўлмаган қисм (pars flaccida)', 'Ненатянутая часть (pars flaccida)')],
            { when: w('perforation', 'central', 'marginal', 'total') }),
          T('perf_size', 'Ўлчами (мм), квадранти', 'Размер (мм), квадрант', { when: w('perforation', 'central', 'marginal', 'total') }),
          M('cavity', 'Перфорация орқали кўринади', 'Через перфорацию видно', [o('pink', 'Ноғора бўшлиғи шиллиғи пушти', 'Слизистая барабанной полости розовая'),
            o('thick', 'Шиллиқ қалинлашган', 'Слизистая утолщена'), o('gran', 'Грануляциялар', 'Грануляции'), o('polyps', 'Полиплар', 'Полипы'),
            o('chol', 'Холестеатома массалари', 'Холестеатомные массы')], { when: w('perforation', 'central', 'marginal', 'total') }),
          R('scars', 'Чандиқлар, петрификатлар', 'Рубцы, петрификаты', [NO, YES]),
        ]),
        P('mobility', 'Ноғора парда ҳаракатчанлиги (Зигле воронкаси) ва эшитув найи ўтказувчанлиги (Вальсальва, Политцер)',
          'Подвижность барабанной перепонки (воронка Зигле) и проходимость слуховой трубы (Вальсальва, Политцер)', [
            R('state', 'Ҳолати', 'Состояние', [n('preserved', 'Сақланган', 'Сохранена'), o('I', 'I даража', 'I степень'), o('II', 'II даража', 'II степень'),
              o('III', 'III даража', 'III степень'), o('IV', 'IV даража', 'IV степень')]),
          ]),
        lymph('қулоқ олди, қулоқ орқаси', 'предушные, заушные'),
      ],
    },

    /* ---------- 7. Эшитиш паспорти ---------- */
    {
      code: 'hearing', uz: 'Акуметрия (эшитиш паспорти)', ru: 'Акуметрия (слуховой паспорт)', print: { uz: 'Акуметрия', ru: 'Акуметрия' },
      ears: [{ code: 'AD', uz: 'AD (ўнг қулоқ)', ru: 'AD (правое ухо)', short: { uz: 'AD', ru: 'AD' } },
        { code: 'AS', uz: 'AS (чап қулоқ)', ru: 'AS (левое ухо)', short: { uz: 'AS', ru: 'AS' } }],
      print_table: true,
      parts: [
        P('noise', 'Субъектив шовқин (СШ)', 'Субъективный шум (СШ)', [R('state', 'Ҳолати', 'Состояние', [NO, YES])]),
        P('whisper', 'Шивирли нутқ (ШН), норма ≥ 6 м', 'Шёпотная речь (ШР), норма ≥ 6 м', [T('m', 'м', 'м', ph('6 м', '6 м'))]),
        P('speech', 'Сўзлашув нутқи (СН), норма ≥ 20 м', 'Разговорная речь (РР), норма ≥ 20 м', [T('m', 'м', 'м', ph('20 м', '20 м'))]),
        P('barany', 'Барани шақилдоғи билан бўғилган қичқириқ', 'Крик с заглушением трещоткой Барани', [T('v', 'Натижа', 'Результат')]),
        P('c128_air', 'C128, ҳаво ўтказувчанлиги (Ҳ), с', 'C128, воздушная проводимость (В), с', [T('s', 'с', 'с')]),
        P('c128_bone', 'C128, суяк ўтказувчанлиги (С), с', 'C128, костная проводимость (К), с', [T('s', 'с', 'с')]),
        P('c2048', 'C2048, ҳаво ўтказувчанлиги, с', 'C2048, воздушная проводимость, с', [T('s', 'с', 'с')]),
        P('rinne', 'Ринне тажрибаси (R)', 'Опыт Ринне (R)', [R('state', 'Натижа', 'Результат', [POS, NEG])]),
        P('schwabach', 'Швабах тажрибаси (Sch)', 'Опыт Швабаха (Sch)', [R('state', 'Натижа', 'Результат', [n('norm', 'Норма', 'Норма'), o('longer', 'Узайган', 'Удлинён'), o('shorter', 'Қисқарган', 'Укорочен')])]),
        P('gelle', 'Желле тажрибаси (G)', 'Опыт Желле (G)', [R('state', 'Натижа', 'Результат', [POS, NEG])]),
        P('bing', 'Бинг тажрибаси (B)', 'Опыт Бинга (B)', [R('state', 'Натижа', 'Результат', [POS, NEG])]),
        P('federici', 'Федеричи тажрибаси (F)', 'Опыт Федеричи (F)', [R('state', 'Натижа', 'Результат', [POS, NEG])]),
        P('tymp', 'Тимпанометрия тури', 'Тимпанометрия, тип', [R('state', 'Тури', 'Тип', [o('A', 'A', 'A'), o('B', 'B', 'B'), o('C', 'C', 'C')])]),
        P('weber', 'Вебер тажрибаси (W)', 'Опыт Вебера (W)', [R('state', 'Натижа', 'Результат', [o('to_ad', 'AD томонга латерализация (←)', 'Латерализация в AD (←)'),
          n('none', 'Латерализациясиз (=)', 'Без латерализации (=)'), o('to_as', 'AS томонга латерализация (→)', 'Латерализация в AS (→)')])], { common: 'after' }),
        P('forks_norm', 'Камертонлар паспорт нормаси', 'Паспортная норма камертонов', [T('v', 'Норма', 'Норма', ph('C128 Ҳ: N = __ с; С: N = __ с; C2048: N = __ с', 'C128 В: N = __ с; К: N = __ с; C2048: N = __ с'))], { common: 'after' }),
        P('conclusion', 'Хулоса', 'Заключение', [
          R('state', 'Хулоса', 'Заключение', [n('normal', 'Эшитиш функцияси нормада', 'Слуховая функция в норме'),
            o('conductive', 'Товуш ўтказиш бузилиши (кондуктив эшитиш пасайиши)', 'Нарушение звукопроведения (кондуктивная тугоухость)'),
            o('sensorineural', 'Товуш қабул қилиш бузилиши (нейросенсор эшитиш пасайиши)', 'Нарушение звуковосприятия (нейросенсорная тугоухость)'),
            o('mixed', 'Аралаш эшитиш пасайиши', 'Смешанная тугоухость')]),
          SIDE(w('state', 'conductive', 'sensorineural', 'mixed')),
        ], { common: 'after' }),
        P('audiometry', 'Тонал бўсаға аудиометрияси', 'Тональная пороговая аудиометрия', [T('v', 'Натижа', 'Результат',
          ph('эгри чизиқлар тури, суяк-ҳаво интервали, 500–4000 Гц ўртача бўсаға', 'тип кривых, костно-воздушный интервал, средний порог 500–4000 Гц'))], { common: 'after' }),
        P('reflex', 'Акустик рефлекс', 'Акустический рефлекс', [T('v', 'Натижа', 'Результат')], { common: 'after' }),
      ],
    },

    /* ---------- 8. Вестибуляр паспорт ---------- */
    {
      code: 'vestibular', uz: 'Вестибулометрия (вестибуляр паспорт)', ru: 'Вестибулометрия (вестибулярный паспорт)', print: { uz: 'Вестибулометрия', ru: 'Вестибулометрия' },
      ears: [{ code: 'r', uz: 'Ўнгда', ru: 'Справа', short: { uz: 'Ўнгда', ru: 'Справа' } }, { code: 'l', uz: 'Чапда', ru: 'Слева', short: { uz: 'Чапда', ru: 'Слева' } }],
      print_table: true,
      parts: [
        P('subjective', 'Бош айланиши, кўнгил айниши, қусиш (субъектив)', 'Головокружение, тошнота, рвота (субъективно)', [
          M('state', 'Ҳолати', 'Состояние', [n('none', 'Йўқ', 'Нет'), o('vertigo', 'Бош айланиши', 'Головокружение'), o('nausea', 'Кўнгил айниши', 'Тошнота'), o('vomit', 'Қусиш', 'Рвота')]),
        ], { common: 'before' }),
        P('nystagmus', 'Спонтан нистагм (йўналиши, текислиги, даражаси, амплитудаси)', 'Спонтанный нистагм (направление, плоскость, степень, амплитуда)', [
          R('state', 'Ҳолати', 'Состояние', [NO, YES]), T('desc', 'Тавсифи', 'Описание', { when: w('state', 'yes') }),
        ]),
        P('arms', 'Қўлларнинг спонтан оғиши', 'Спонтанное отклонение рук', [R('state', 'Ҳолати', 'Состояние', [NO, YES])]),
        P('barany', 'Барани кўрсатиш синамаси', 'Указательная проба Барани', [R('state', 'Натижа', 'Результат', OK_MISS)]),
        P('finger_nose', 'Бармоқ-бурун синамаси', 'Пальценосовая проба', [R('state', 'Натижа', 'Результат', OK_MISS)]),
        P('finger_finger', 'Бармоқ-бармоқ синамаси', 'Пальце-пальцевая проба', [R('state', 'Натижа', 'Результат', OK_MISS)]),
        P('heel_knee', 'Товон-тизза синамаси', 'Пяточно-коленная проба', [R('state', 'Натижа', 'Результат', OK_MISS)]),
        P('adiadoch', 'Адиадохокинез', 'Адиадохокинез', [R('state', 'Ҳолати', 'Состояние', [NO, YES])]),
        P('fistula', 'Прессор (фистула) синамаси', 'Прессорная (фистульная) проба', [R('state', 'Натижа', 'Результат', [n('neg', 'Манфий', 'Отрицательная'), o('pos', 'Мусбат', 'Положительная')])]),
        P('caloric', 'Калорик синама: нистагм, с; хусусияти', 'Калорическая проба: нистагм, с; характер', [T('v', 'Натижа', 'Результат')]),
        P('romberg', 'Ромберг ҳолати (оддий / сенсибилизацияланган)', 'Поза Ромберга (простая / сенсибилизированная)', [
          R('state', 'Натижа', 'Результат', [n('stable', 'Барқарор', 'Устойчив'), o('unstable', 'Беқарор', 'Неустойчив')]), SIDE(w('state', 'unstable')),
        ], { common: 'after' }),
        P('gait', 'Кўзлар очиқ / ёпиқ ҳолда тўғри юриш', 'Прямая походка с открытыми / закрытыми глазами', [
          R('state', 'Натижа', 'Результат', [n('straight', 'Оғмайди', 'Не отклоняется'), o('deviates', 'Оғади', 'Отклоняется')]), SIDE(w('state', 'deviates')),
        ], { common: 'after' }),
        P('flank', 'Флангли юриш', 'Фланговая походка', [
          R('state', 'Натижа', 'Результат', [n('ok', 'Бажаради', 'Выполняет'), o('impaired', 'Бузилган', 'Нарушена')]), SIDE(w('state', 'impaired')),
        ], { common: 'after' }),
        P('rotation', 'Айлантириш синамаси: нистагм давомийлиги, с (норма 25–35 с)', 'Вращательная проба: длительность нистагма, с (норма 25–35 с)', [T('v', 'с', 'с')], { common: 'after' }),
        P('otolith', 'Отолит реакцияси (Воячек синамаси): соматик, вегетатив', 'Отолитовая реакция (проба Воячека): соматическая, вегетативная', [T('v', 'Натижа', 'Результат')], { common: 'after' }),
        P('conclusion', 'Хулоса', 'Заключение', [
          R('state', 'Хулоса', 'Заключение', [n('normal', 'Вестибуляр бузилишлар аниқланмади, қўзғалувчанлик нормал, симметрик', 'Вестибулярных расстройств не выявлено, возбудимость нормальная, симметричная'),
            o('changed', 'Вестибуляр бузилишлар аниқланди', 'Выявлены вестибулярные нарушения')]),
          T('desc', 'Тавсифи', 'Описание', { when: w('state', 'changed') }),
        ], { common: 'after' }),
      ],
    },
  ];

  /* LOR STATUS bo'limlari (formadagi tablar). Ma'lumot metod kodlari bo'yicha saqlanadi, guruhlar faqat
     ko'rinish va tartib uchun: Фарингоскопия → Риноскопия → Отоскопия → Ларингоскопия → Акуметрия → Вестибулометрия */
  const GROUPS = [
    { code: 'g_pharyngoscopy', uz: 'Фарингоскопия', ru: 'Фарингоскопия', methods: ['nasopharynx', 'oropharynx', 'hypopharynx'] },
    { code: 'g_rhinoscopy', uz: 'Риноскопия', ru: 'Риноскопия', methods: ['nose'] },
    { code: 'g_otoscopy', uz: 'Отоскопия', ru: 'Отоскопия', methods: ['ears'] },
    { code: 'g_laryngoscopy', uz: 'Ларингоскопия', ru: 'Ларингоскопия', methods: ['larynx'] },
    { code: 'g_acumetry', uz: 'Акуметрия', ru: 'Акуметрия', methods: ['hearing'] },
    { code: 'g_vestibulometry', uz: 'Вестибулометрия', ru: 'Вестибулометрия', methods: ['vestibular'] },
  ];
  const METHODS = GROUPS.flatMap((g) => g.methods.map((c) => RAW_METHODS.find((m) => m.code === c)));
  if (METHODS.length !== RAW_METHODS.length || METHODS.some((m) => !m)) throw new Error('LOR GROUPS mismatch');

  const ALL_METHODS = [...METHODS, ...LEGACY_METHODS];
  const LEGACY_CODES = new Set(LEGACY_METHODS.map((m) => m.code));
  const TEST_LABEL = { uz: 'Синама', ru: 'Тест' };

  // Eski shablon maydonlari uchun sarlavhalar (yangi shablonda har bir maydonning o'z sarlavhasi bor)
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

  // Tez tanlash uchun tashxislar (XKT-10). To'liq ro'yxat: icd10-lor.js
  const o_ = (code, uz, ru) => ({ code, uz, ru });
  const DIAGNOSES = [
    o_('J00', 'Ўткир назофарингит', 'Острый назофарингит'),
    o_('J01', 'Ўткир синусит', 'Острый синусит'),
    o_('J02', 'Ўткир фарингит', 'Острый фарингит'),
    o_('J03', 'Ўткир тонзиллит', 'Острый тонзиллит'),
    o_('J04.0', 'Ўткир ларингит', 'Острый ларингит'),
    o_('J30', 'Вазомотор ва аллергик ринит', 'Вазомоторный и аллергический ринит'),
    o_('J31.0', 'Сурункали ринит', 'Хронический ринит'),
    o_('J31.2', 'Сурункали фарингит', 'Хронический фарингит'),
    o_('J32', 'Сурункали синусит', 'Хронический синусит'),
    o_('J33', 'Бурун полипи', 'Полип носа'),
    o_('J34.2', 'Бурун тўсиғи қийшиқлиги', 'Искривление носовой перегородки'),
    o_('J35.0', 'Сурункали тонзиллит', 'Хронический тонзиллит'),
    o_('J35.2', 'Аденоидлар гипертрофияси', 'Гипертрофия аденоидов'),
    o_('J37.0', 'Сурункали ларингит', 'Хронический ларингит'),
    o_('J38.1', 'Овоз бойлами полипи', 'Полип голосовой складки'),
    o_('H60', 'Ташқи отит', 'Наружный отит'),
    o_('H61.2', 'Олтингугурт тиқини', 'Серная пробка'),
    o_('H65', 'Йирингсиз ўрта отит', 'Негнойный средний отит'),
    o_('H66', 'Йирингли ўрта отит', 'Гнойный средний отит'),
    o_('H68', 'Евстахиит', 'Евстахиит'),
    o_('H72', 'Ноғора парда перфорацияси', 'Перфорация барабанной перепонки'),
    o_('H90', 'Эшитиш пасайиши', 'Тугоухость'),
    o_('H93.1', 'Қулоқда шовқин (тиннитус)', 'Шум в ушах'),
    o_('R04.0', 'Бурундан қон кетиши', 'Носовое кровотечение'),
  ];

  /* ---------------- Yordamchilar ---------------- */
  const L = (x, lang) => (x ? x[lang] || x.uz || '' : '');
  const text = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : '');

  const COMPLAINT_INDEX = {};
  COMPLAINTS.forEach((g) => g.items.forEach((i) => { COMPLAINT_INDEX[i.code] = i; }));
  // Takrorlangani uchun olib tashlangan shikoyatlar: eski yozuvlar asosiy kodga o'tkaziladi
  const COMPLAINT_ALIASES = {
    pharynx_cough: 'larynx_cough',
    larynx_foreign_body: 'pharynx_foreign_body',
    larynx_swallowing: 'pharynx_swallowing',
  };
  const complaintCode = (code) => COMPLAINT_ALIASES[code] || code;
  const DISCHARGE_CODES = new Set(DISCHARGE.map((d) => d.code));

  function choicesOf(field) {
    if (field.type === 'side') return SIDES;
    if (field.type === 'degree') return DEGREES;
    return field.options || [];
  }

  /** Metodning umumiy qismlari (ears bo'lmasa — barcha qismlar) va tomonlarga bo'linadigan qismlari */
  const commonParts = (m) => (m.ears ? m.parts.filter((p) => p.common) : m.parts);
  const sideParts = (m) => (m.ears ? m.parts.filter((p) => !p.common) : []);
  /** Formada va tekshiruvda ishlatiladigan to'plamlar: [{ ear: '' | 'AD' | ..., parts }] */
  function partSets(m) {
    const sets = [{ ear: '', parts: commonParts(m) }];
    if (m.ears) m.ears.forEach((e) => sets.push({ ear: e.code, parts: sideParts(m) }));
    return sets.filter((s) => s.parts.length);
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

  /** Qism ko‘rinadimi (eski shablon: baraban bo‘shlig‘i faqat perforatsiya bo‘lsa) */
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
      case 'text': {
        const t = text(v, 300);
        return t || undefined;
      }
      default:
        return undefined;
    }
  }

  function sanitizeParts(raw, list) {
    const src = raw && typeof raw === 'object' ? raw : {};
    const out = {};
    for (const part of list) {
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
    for (const m of ALL_METHODS) {
      const mIn = src[m.code] && typeof src[m.code] === 'object' ? src[m.code] : {};
      const res = {};
      const common = sanitizeParts(mIn.parts, commonParts(m));
      if (Object.keys(common).length) res.parts = common;
      if (m.ears) {
        const same = !!m.same_toggle && mIn.same === true;
        const earsIn = mIn.ears && typeof mIn.ears === 'object' ? mIn.ears : {};
        const ears = {};
        m.ears.forEach((e, i) => {
          if (same && i > 0) return;
          const p = sanitizeParts(earsIn[e.code], sideParts(m));
          if (Object.keys(p).length) ears[e.code] = p;
        });
        if (Object.keys(ears).length) res.ears = ears;
        if (same) res.same = true;
      }
      const note = text(mIn.note, 2000);
      if (note) res.note = note;
      if (Object.keys(res).length && !(Object.keys(res).length === 1 && res.same)) out[m.code] = res;
    }
    return out;
  }

  function sanitizeComplaints(arr) {
    if (!Array.isArray(arr)) return [];
    const out = [];
    const seen = new Set();
    for (const raw of arr) {
      const item = typeof raw === 'string' ? { code: raw } : raw && typeof raw === 'object' ? raw : null;
      if (!item || typeof item.code !== 'string') continue;
      const code = complaintCode(item.code);
      if (!COMPLAINT_INDEX[code] || seen.has(code)) continue;
      seen.add(code);
      const c = { code };
      if (COMPLAINT_INDEX[code].has_discharge_type && DISCHARGE_CODES.has(item.discharge)) {
        c.discharge = item.discharge;
        const t = text(item.discharge_text, 200);
        if (item.discharge === 'other' && t) c.discharge_text = t;
      }
      out.push(c);
    }
    return out;
  }

  /* ---------------- Hujjat matni ---------------- */
  const lowerFirst = (s) => (/^\p{Lu}\p{Ll}/u.test(s) ? s[0].toLowerCase() + s.slice(1) : s);
  // Eski shablon: faqat qiymatning o‘zi tushunarsiz bo‘ladigan maydonlarda sarlavha chop etiladi
  const PRINT_WITH_LABEL = new Set(['perforation', 'lacunae_contents', 'contents', 'cause', 'location', 'branch', 'pain_part']);

  function fieldText(field, v, lang, multi) {
    if (field.type === 'checkbox') return L(field, lang);
    let value;
    if (field.type === 'text') value = String(v);
    else {
      const ch = choicesOf(field);
      const label = (code) => L(ch.find((x) => x.code === code), lang) || code;
      value = Array.isArray(v) ? v.map((c, i) => (i ? lowerFirst(label(c)) : label(c))).join(', ') : label(v);
    }
    if (field.type === 'side' || field.bare) return value;
    let title = null;
    if (field.uz) { if (multi && field.code !== 'state') title = L(field, lang); }
    else if (PRINT_WITH_LABEL.has(field.code) && FIELD_LABELS[field.code]) title = L(FIELD_LABELS[field.code], lang);
    return title ? `${title}: ${lowerFirst(value)}` : value;
  }

  /** Bitta qismning matni: "Ўзгарган, ўзгариш: бурун қирраси ўнгга қийшайган" */
  function partText(part, pv, lang) {
    const multi = part.fields.length > 1;
    const pieces = [];
    for (const f of part.fields) if (pv[f.code] !== undefined) pieces.push(fieldText(f, pv[f.code], lang, multi));
    if (pv._text) pieces.push(pv._text);
    return pieces.map((p, i) => (i ? lowerFirst(p) : p)).join(', ');
  }

  function partsLines(parts, lang, list) {
    const lines = [];
    for (const part of list) {
      const pv = parts && parts[part.code];
      if (pv) lines.push({ label: L(part, lang), text: partText(part, pv, lang) });
    }
    return lines;
  }

  /**
   * Hujjat uchun: [{ title, groups, note }]. Guruh: { sub, lines: [{label, text}] }
   * yoki jadval: { table: { head: [chap, o'ng], test, rows: [{ label, vals: [a, b] }] } }. Faqat qayd etilganlar.
   */
  function lorStatusText(lor, lang) {
    const out = [];
    const src = lor && typeof lor === 'object' ? lor : {};
    for (const m of ALL_METHODS) {
      const mv = src[m.code];
      if (!mv) continue;
      const groups = [];
      const push = (sub, lines) => { if (lines.length) groups.push({ sub, lines }); };
      if (!m.ears) push('', partsLines(mv.parts, lang, m.parts));
      else {
        const common = commonParts(m);
        push('', partsLines(mv.parts, lang, common.filter((p) => p.common === 'before')));
        const ears = mv.ears || {};
        if (m.print_table) {
          const rows = [];
          for (const p of sideParts(m)) {
            const vals = m.ears.map((e) => (ears[e.code] && ears[e.code][p.code] ? partText(p, ears[e.code][p.code], lang) : ''));
            if (vals.some(Boolean)) rows.push({ label: L(p, lang), vals });
          }
          if (rows.length) groups.push({ table: { head: m.ears.map((e) => L(e.short || e, lang)), test: L(TEST_LABEL, lang), rows } });
        } else if (mv.same) {
          push(L(m.same_print, lang) || 'AD = AS', partsLines(ears[m.ears[0].code], lang, sideParts(m)));
        } else {
          for (const e of m.ears) push(L(e, lang), partsLines(ears[e.code], lang, sideParts(m)));
        }
        push('', partsLines(mv.parts, lang, common.filter((p) => p.common !== 'before')));
      }
      if (groups.length || mv.note) out.push({ title: L(m.print || m, lang), groups, note: mv.note || '' });
    }
    return out;
  }

  function complaintLabel(code, lang) {
    const c = complaintCode(code);
    return COMPLAINT_INDEX[c] ? L(COMPLAINT_INDEX[c], lang) : code;
  }

  /** "Бурун битиши, қулоқдан ажралма келиши (йирингли)" */
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
    COMPLAINTS, DISCHARGE, SIDES, DEGREES, METHODS, GROUPS, LEGACY_METHODS, LEGACY_CODES, FIELD_LABELS, DIAGNOSES, RELATIVES, relative,
    choicesOf, fieldVisible, partVisible, commonParts, sideParts, partSets,
    sanitizeLor, sanitizeComplaints, lorStatusText, complaintLabel, complaintsText, complaintCode,
  };
});
