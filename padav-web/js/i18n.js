const STRINGS = {
  en: {
    appName: 'Padav',
    tagline: 'Prepare anywhere. Improve every day.',
    nav_home: 'Home', nav_practice: 'Practice', nav_material: 'Material', nav_progress: 'Progress', nav_profile: 'Profile',
    attempted: 'Questions attempted', accuracy: 'Accuracy', quizzes: 'Quizzes taken',
    emptyHome: 'Take your first quiz to see your progress here.',
    startQuiz: 'Start quiz', chooseSubject: 'Choose a subject',
    questions: '{n} questions', minutes: '{n} min',
    next: 'Next', previous: 'Previous', submit: 'Submit', markReview: 'Mark for review',
    timeLeft: 'Time left',
    resultTitle: 'Result', score: 'Score', correct: 'Correct', incorrect: 'Incorrect', unanswered: 'Unanswered',
    backPractice: 'Back to practice', explanation: 'Explanation',
    comingSoon: 'Coming soon', language: 'Language', recent: 'Recent attempts',
    confirmSubmit: 'Submit quiz?', unansweredWarning: '{n} unanswered', cancel: 'Cancel',
    resume: 'Quiz in progress', resumeQuiz: 'Resume', discard: 'Discard',
    discardOther: 'Another quiz is in progress. Discard it and start this one?',
    yourAnswer: 'Your answer', correctAnswer: 'Correct answer',
    install: 'Install app', installHint: 'Add Padav to your home screen to use it like an app.',
    offlineReady: 'Ready to use offline', offlineNotYet: 'Offline mode is getting ready…',
    progressTitle: 'Your progress', bySubject: 'By subject', avgTime: 'Average time per question', seconds: '{n}s',
    recommend: 'Practice more {subject}: your accuracy is {pct}%.', practiceNow: 'Practice now',
    noData: 'No data yet', loadError: 'Could not load questions. Connect to the internet once, then reload.',
    notFound: 'Not found', materialNote: 'Study notes will appear here.',
    unansweredShort: 'Not answered',
  },
  hi: {
    appName: 'पड़ाव',
    tagline: 'कहीं भी तैयारी करो, रोज़ बेहतर बनो।',
    nav_home: 'होम', nav_practice: 'अभ्यास', nav_material: 'सामग्री', nav_progress: 'प्रगति', nav_profile: 'प्रोफ़ाइल',
    attempted: 'हल किए गए प्रश्न', accuracy: 'सटीकता', quizzes: 'क्विज़ दिए',
    emptyHome: 'अपनी प्रगति देखने के लिए पहला क्विज़ दें।',
    startQuiz: 'क्विज़ शुरू करें', chooseSubject: 'विषय चुनें',
    questions: '{n} प्रश्न', minutes: '{n} मिनट',
    next: 'अगला', previous: 'पिछला', submit: 'जमा करें', markReview: 'समीक्षा के लिए चिह्नित करें',
    timeLeft: 'शेष समय',
    resultTitle: 'परिणाम', score: 'अंक', correct: 'सही', incorrect: 'गलत', unanswered: 'अनुत्तरित',
    backPractice: 'अभ्यास पर वापस', explanation: 'व्याख्या',
    comingSoon: 'जल्द आ रहा है', language: 'भाषा', recent: 'हाल के प्रयास',
    confirmSubmit: 'क्विज़ जमा करें?', unansweredWarning: '{n} अनुत्तरित', cancel: 'रद्द करें',
    resume: 'क्विज़ जारी है', resumeQuiz: 'जारी रखें', discard: 'छोड़ दें',
    discardOther: 'एक और क्विज़ जारी है। उसे छोड़कर यह शुरू करें?',
    yourAnswer: 'आपका उत्तर', correctAnswer: 'सही उत्तर',
    install: 'ऐप इंस्टॉल करें', installHint: 'पड़ाव को होम स्क्रीन पर जोड़ें और ऐप की तरह इस्तेमाल करें।',
    offlineReady: 'ऑफ़लाइन उपयोग के लिए तैयार', offlineNotYet: 'ऑफ़लाइन मोड तैयार हो रहा है…',
    progressTitle: 'आपकी प्रगति', bySubject: 'विषयवार', avgTime: 'प्रति प्रश्न औसत समय', seconds: '{n} सेकंड',
    recommend: '{subject} का और अभ्यास करें: आपकी सटीकता {pct}% है।', practiceNow: 'अभी अभ्यास करें',
    noData: 'अभी कोई डेटा नहीं', loadError: 'प्रश्न लोड नहीं हो सके। एक बार इंटरनेट से जुड़कर पेज रीलोड करें।',
    notFound: 'नहीं मिला', materialNote: 'अध्ययन सामग्री यहाँ दिखाई देगी।',
    unansweredShort: 'उत्तर नहीं दिया',
  },
};

const LANG_KEY = 'padav.lang';
let lang = 'en';

function detect() {
  try {
    const saved = localStorage.getItem(LANG_KEY);
    if (saved === 'en' || saved === 'hi') return saved;
  } catch { /* storage blocked */ }
  return (navigator.language || 'en').toLowerCase().startsWith('hi') ? 'hi' : 'en';
}

export function initLang() {
  lang = detect();
  document.documentElement.lang = lang;
}

export function getLang() { return lang; }

export function setLang(next) {
  lang = next === 'hi' ? 'hi' : 'en';
  try { localStorage.setItem(LANG_KEY, lang); } catch { /* ignore */ }
  document.documentElement.lang = lang;
}

/** t('questions', {n: 5}) */
export function t(key, vars = {}) {
  const s = STRINGS[lang][key] ?? STRINGS.en[key] ?? key;
  return s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? `{${k}}`));
}

/** Pick the current language from a {en, hi} object, falling back to English. */
export function pick(obj) {
  if (!obj) return '';
  return (lang === 'hi' && obj.hi && obj.hi.trim()) ? obj.hi : obj.en;
}
