import { h, icon, confirmDialog } from './dom.js';
import { t, initLang, getLang, setLang, pick } from './i18n.js';
import { evaluate } from './scoring.js';
import { loadPack } from './pack.js';
import * as store from './store.js';

const root = document.getElementById('app');
const navEl = document.getElementById('nav');
const SESSION_KEY = 'padav.session';

let pack = null;
let cleanup = null; // teardown for the current view (timers etc.)
let installPrompt = null;

const TABS = [
  ['home', 'nav_home', 'M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z'],
  ['practice', 'nav_practice', 'M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z'],
  ['material', 'nav_material', 'M18 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2zM6 4h5v8l-2.5-1.5L6 12V4z'],
  ['progress', 'nav_progress', 'M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z'],
  ['profile', 'nav_profile', 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'],
];

/* ---------- session persistence (unfinished quiz survives refresh/close) ---------- */

function readSession() {
  try { return JSON.parse(localStorage.getItem(SESSION_KEY)); } catch { return null; }
}
function writeSession(s) {
  try { localStorage.setItem(SESSION_KEY, JSON.stringify(s)); } catch { /* storage blocked: quiz still works */ }
}
function clearSession() {
  try { localStorage.removeItem(SESSION_KEY); } catch { /* ignore */ }
}

/* ---------- helpers ---------- */

const fmtTime = (sec) => `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`;
const pct = (x) => `${Math.round(x * 100)}%`;
const subjectName = (id) => pick(pack.subjects.find((s) => s.id === id)?.name) || id;

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function mount(...nodes) {
  root.replaceChildren(...nodes.flat(Infinity).filter((n) => n != null && n !== false));
  root.scrollTop = 0;
  window.scrollTo(0, 0);
}

function renderNav(active) {
  navEl.hidden = !active;
  if (!active) return;
  navEl.replaceChildren(...TABS.map(([route, label, path]) =>
    h('a', { href: `#/${route}`, class: route === active ? 'tab active' : 'tab', 'aria-current': route === active ? 'page' : null },
      icon(path), h('span', {}, t(label)))));
}

function stat(label, value) {
  return h('div', { class: 'card stat' }, h('div', { class: 'stat-value' }, value), h('div', { class: 'stat-label' }, label));
}

function heading(text) {
  return h('h1', { class: 'page-title' }, text);
}

/* ---------- views ---------- */

async function homeView() {
  renderNav('home');
  const attempts = await store.listAttempts();
  let correct = 0; let incorrect = 0;
  attempts.forEach((a) => { correct += a.correct; incorrect += a.incorrect; });
  const attempted = correct + incorrect;

  mount(
    h('header', { class: 'hero' }, h('h1', {}, t('appName')), h('p', {}, t('tagline'))),
    h('div', { class: 'grid3' },
      stat(t('attempted'), attempted),
      stat(t('accuracy'), attempted ? pct(correct / attempted) : '0%'),
      stat(t('quizzes'), attempts.length)),
    attempts.length === 0 ? h('p', { class: 'muted' }, t('emptyHome')) : null,
    h('a', { class: 'btn primary block', href: '#/practice' }, t('startQuiz')),
    attempts.length ? h('h2', { class: 'section' }, t('recent')) : null,
    attempts.slice(0, 5).map((a) =>
      h('a', { class: 'card link', href: `#/result/${a.id}` },
        h('div', { class: 'card-title' }, pick(a.title)),
        h('div', { class: 'muted' }, `${t('score')}: ${a.score.toFixed(2)} / ${a.maxScore.toFixed(0)}`))),
  );
}

function practiceView() {
  renderNav('practice');
  const session = readSession();
  const resumeDef = session && pack.quizzes.find((q) => q.id === session.quizId);

  mount(
    heading(t('chooseSubject')),
    resumeDef ? h('div', { class: 'card resume' },
      h('div', { class: 'card-title' }, t('resume')),
      h('div', { class: 'muted' }, pick(resumeDef.title)),
      h('div', { class: 'row' },
        h('a', { class: 'btn primary', href: `#/quiz/${resumeDef.id}` }, t('resumeQuiz')),
        h('button', { class: 'btn text', onclick: () => { clearSession(); practiceView(); } }, t('discard')))) : null,
    pack.quizzes.map((q) =>
      h('a', { class: 'card link', href: `#/quiz/${q.id}` },
        h('div', { class: 'eyebrow' }, subjectName(q.subjectId)),
        h('div', { class: 'card-title' }, pick(q.title)),
        h('div', { class: 'muted' }, `${t('questions', { n: q.questionCount })} · ${t('minutes', { n: Math.round(q.durationSeconds / 60) })}`))),
  );
}

async function quizView(id) {
  const def = pack.quizzes.find((q) => q.id === id);
  if (!def) { renderNav(null); mount(h('p', { class: 'muted' }, t('notFound'))); return; }

  let s = readSession();
  if (s && s.quizId !== id) {
    const ok = await confirmDialog({ title: t('discardOther'), ok: t('startQuiz'), cancel: t('cancel') });
    if (!ok) { location.replace('#/practice'); return; }
    s = null;
  }
  if (s && !s.qids.every((qid) => pack.byId.has(qid))) s = null; // pack changed under a saved session
  if (!s) {
    const now = Date.now();
    const pool = pack.questions.filter((q) => q.subjectId === def.subjectId);
    s = {
      quizId: id,
      qids: shuffle(pool).slice(0, def.questionCount).map((q) => q.id),
      selected: {}, marked: [], index: 0,
      startedAt: now, deadline: now + def.durationSeconds * 1000,
      timeMs: {}, enteredAt: now,
    };
  }
  s.enteredAt = Date.now(); // time spent away from the quiz is not charged to a question
  writeSession(s);

  const qs = s.qids.map((qid) => pack.byId.get(qid));
  renderNav(null);

  let submitting = false;
  const timerEl = h('span', { class: 'timer' });

  const commitTime = () => {
    const q = qs[s.index];
    const now = Date.now();
    s.timeMs[q.id] = (s.timeMs[q.id] || 0) + (now - s.enteredAt);
    s.enteredAt = now;
  };

  const submit = async () => {
    if (submitting) return; // guards timer + button double submit
    submitting = true;
    clearInterval(interval);
    commitTime();
    const inputs = qs.map((q) => ({ selectedKey: s.selected[q.id] ?? null, correctKey: q.correctKey }));
    const r = evaluate({ marksPerQuestion: def.marksPerQuestion, negativeMarks: def.negativeMarks }, inputs);
    const completedAt = Date.now();
    await store.saveAttempt({
      id: store.uuid(),
      quizId: id, subjectId: def.subjectId, title: def.title,
      startedAt: s.startedAt, completedAt,
      score: r.score, maxScore: r.maxScore, correct: r.correct, incorrect: r.incorrect, unanswered: r.unanswered,
      durationSeconds: Math.round((completedAt - s.startedAt) / 1000),
      syncStatus: 'PENDING',
      answers: qs.map((q, i) => ({
        questionId: q.id, subjectId: q.subjectId, topic: q.topic, position: i,
        selectedKey: s.selected[q.id] ?? null,
        isCorrect: s.selected[q.id] === q.correctKey,
        timeTakenSeconds: Math.round((s.timeMs[q.id] || 0) / 1000),
      })),
    });
    const attemptId = (await store.listAttempts())[0].id;
    clearSession();
    location.replace(`#/result/${attemptId}`);
  };

  const tick = () => {
    const rem = Math.max(0, Math.ceil((s.deadline - Date.now()) / 1000));
    timerEl.textContent = `${t('timeLeft')} ${fmtTime(rem)}`;
    timerEl.classList.toggle('warn', rem <= 30);
    if (rem <= 0) submit(); // automatic submission when time expires
  };
  const interval = setInterval(tick, 1000);
  cleanup = () => clearInterval(interval);

  const go = (i) => {
    if (i < 0 || i >= qs.length || submitting) return;
    commitTime();
    s.index = i;
    writeSession(s);
    draw();
  };

  const draw = () => {
    const q = qs[s.index];
    const isLast = s.index === qs.length - 1;
    const marked = s.marked.includes(q.id);
    mount(h('div', { class: 'quiz' },
      h('div', { class: 'quiz-head' }, h('strong', {}, pick(def.title)), timerEl),
      h('div', { class: 'bar', role: 'progressbar', 'aria-valuemin': 1, 'aria-valuemax': qs.length, 'aria-valuenow': s.index + 1 },
        h('div', { class: 'bar-fill', style: `width:${((s.index + 1) / qs.length) * 100}%` })),
      h('div', { class: 'palette' }, qs.map((pq, i) =>
        h('button', {
          class: ['chip', i === s.index ? 'current' : '', s.marked.includes(pq.id) ? 'marked' : s.selected[pq.id] ? 'answered' : ''].join(' ').trim(),
          'aria-label': `${i + 1}`, onclick: () => go(i),
        }, i + 1))),
      h('div', { class: 'eyebrow' }, pick(q.topic)),
      h('p', { class: 'question' }, pick(q.text)),
      h('div', { class: 'options', role: 'radiogroup' }, q.options.map((o) =>
        h('button', {
          class: s.selected[q.id] === o.key ? 'option selected' : 'option',
          role: 'radio', 'aria-checked': s.selected[q.id] === o.key ? 'true' : 'false',
          onclick: () => {
            if (s.selected[q.id] === o.key) delete s.selected[q.id]; else s.selected[q.id] = o.key;
            writeSession(s);
            draw();
          },
        }, h('span', { class: 'dot' }), h('span', {}, pick(o.text))))),
      h('div', { class: 'quiz-foot' },
        h('button', { class: 'btn outline', disabled: s.index === 0, onclick: () => go(s.index - 1) }, t('previous')),
        h('button', {
          class: marked ? 'btn flag on' : 'btn flag',
          onclick: () => {
            s.marked = marked ? s.marked.filter((x) => x !== q.id) : [...s.marked, q.id];
            writeSession(s);
            draw();
          },
        }, t('markReview')),
        isLast
          ? h('button', {
            class: 'btn primary',
            onclick: async () => {
              const left = qs.filter((x) => s.selected[x.id] == null).length;
              const ok = await confirmDialog({
                title: t('confirmSubmit'), text: left ? t('unansweredWarning', { n: left }) : '',
                ok: t('submit'), cancel: t('cancel'),
              });
              if (ok) submit();
            },
          }, t('submit'))
          : h('button', { class: 'btn primary', onclick: () => go(s.index + 1) }, t('next'))),
    ));
    tick();
  };

  draw();
}

async function resultView(id) {
  renderNav('practice');
  const a = await store.getAttempt(id);
  if (!a) { mount(h('p', { class: 'muted' }, t('notFound'))); return; }

  mount(
    heading(t('resultTitle')),
    h('div', { class: 'card score-card' },
      h('div', { class: 'score' }, `${a.score.toFixed(2)} / ${a.maxScore.toFixed(0)}`),
      h('div', { class: 'muted' }, pick(a.title)),
      h('div', { class: 'counts' },
        h('span', { class: 'good' }, `${t('correct')}: ${a.correct}`),
        h('span', { class: 'bad' }, `${t('incorrect')}: ${a.incorrect}`),
        h('span', {}, `${t('unanswered')}: ${a.unanswered}`))),
    h('a', { class: 'btn primary block', href: '#/practice' }, t('backPractice')),
    a.answers.map((ans, i) => {
      const q = pack.byId.get(ans.questionId);
      if (!q) return null;
      const yours = q.options.find((o) => o.key === ans.selectedKey);
      const right = q.options.find((o) => o.key === q.correctKey);
      return h('div', { class: 'card review' },
        h('div', { class: 'card-title' }, `${i + 1}. ${pick(q.text)}`),
        h('div', { class: ans.isCorrect ? 'good' : 'bad' }, `${t('yourAnswer')}: ${yours ? pick(yours.text) : t('unansweredShort')}`),
        ans.isCorrect ? null : h('div', {}, `${t('correctAnswer')}: ${pick(right?.text)}`),
        h('div', { class: 'muted small' }, `${t('explanation')}: ${pick(q.explanation)}`));
    }),
  );
}

async function progressView() {
  renderNav('progress');
  const attempts = await store.listAttempts();
  const by = {};
  let totalTime = 0; let totalAnswered = 0;
  for (const a of attempts) {
    for (const ans of a.answers) {
      if (ans.selectedKey == null) continue;
      const b = (by[ans.subjectId] ||= { attempted: 0, correct: 0 });
      b.attempted++;
      if (ans.isCorrect) b.correct++;
      totalTime += ans.timeTakenSeconds; totalAnswered++;
    }
  }

  // Rule-based recommendation: weakest subject with enough data and below 70%.
  const weak = pack.subjects
    .map((s) => ({ s, b: by[s.id] }))
    .filter((x) => x.b && x.b.attempted >= 3)
    .sort((x, y) => x.b.correct / x.b.attempted - y.b.correct / y.b.attempted)[0];
  const weakAcc = weak ? weak.b.correct / weak.b.attempted : 1;
  const weakQuiz = weak && pack.quizzes.find((q) => q.subjectId === weak.s.id);

  mount(
    heading(t('progressTitle')),
    totalAnswered === 0
      ? h('p', { class: 'muted' }, t('noData'))
      : [
        weak && weakAcc < 0.7 ? h('div', { class: 'card tip' },
          h('div', {}, t('recommend', { subject: pick(weak.s.name), pct: Math.round(weakAcc * 100) })),
          weakQuiz ? h('a', { class: 'btn primary', href: `#/quiz/${weakQuiz.id}` }, t('practiceNow')) : null) : null,
        h('h2', { class: 'section' }, t('bySubject')),
        pack.subjects.map((s) => {
          const b = by[s.id];
          const acc = b ? b.correct / b.attempted : 0;
          return h('div', { class: 'card' },
            h('div', { class: 'row between' }, h('strong', {}, pick(s.name)), h('span', {}, b ? pct(acc) : '—')),
            h('div', { class: 'bar' }, h('div', { class: 'bar-fill', style: `width:${acc * 100}%` })),
            h('div', { class: 'muted small' }, b ? `${b.correct}/${b.attempted}` : t('noData')));
        }),
        h('div', { class: 'card' },
          h('div', { class: 'muted' }, t('avgTime')),
          h('div', { class: 'stat-value' }, t('seconds', { n: Math.round(totalTime / totalAnswered) }))),
      ],
  );
}

function materialView() {
  renderNav('material');
  mount(heading(t('nav_material')), h('p', { class: 'muted' }, `${t('comingSoon')}. ${t('materialNote')}`));
}

function profileView() {
  renderNav('profile');
  const offline = h('p', { class: 'muted' }, t('offlineNotYet'));
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then(() => { offline.textContent = t('offlineReady'); });
  }
  const lang = getLang();
  const langBtn = (code, label) => h('button', {
    class: lang === code ? 'btn primary' : 'btn outline',
    'aria-pressed': lang === code ? 'true' : 'false',
    onclick: () => { setLang(code); route(); },
  }, label);

  mount(
    heading(t('nav_profile')),
    h('h2', { class: 'section' }, t('language')),
    h('div', { class: 'row' }, langBtn('en', 'English'), langBtn('hi', 'हिन्दी')),
    h('h2', { class: 'section' }, t('install')),
    h('p', { class: 'muted' }, t('installHint')),
    installPrompt
      ? h('button', {
        class: 'btn outline',
        onclick: async () => { installPrompt.prompt(); await installPrompt.userChoice; installPrompt = null; profileView(); },
      }, t('install'))
      : null,
    offline,
  );
}

/* ---------- router ---------- */

function route() {
  if (cleanup) { cleanup(); cleanup = null; }
  document.title = t('appName');
  const [, name = 'home', arg] = location.hash.split('/');
  const views = {
    home: homeView, practice: practiceView, material: materialView, progress: progressView,
    profile: profileView, quiz: () => quizView(arg), result: () => resultView(arg),
  };
  (views[name] || homeView)();
}

/* ---------- boot ---------- */

window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); installPrompt = e; });

async function boot() {
  initLang();
  try {
    pack = await loadPack();
  } catch {
    renderNav(null);
    mount(h('p', { class: 'muted' }, t('loadError')));
    return;
  }
  window.addEventListener('hashchange', route);
  route();
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => { /* app still works online */ });
  }
}

boot();
