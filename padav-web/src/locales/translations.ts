import type { Language } from '../store/preferences'

export const translations: Record<Language, Record<string, string>> = {
  en: {
    home: 'Overview', learn: 'Learn', planner: 'Planner', tests: 'Tests', analytics: 'Analytics', bookmarks: 'Bookmarks', profile: 'Profile', settings: 'Settings',
    search: 'Search courses, tests, topics…', greeting: 'Good morning', welcome: 'Your next milestone is closer than you think.',
    mission: 'Daily mission', streak: 'Study streak', continue: 'Continue learning', challenge: 'Daily challenge', upcoming: 'Upcoming tests',
    accuracy: 'Accuracy', questions: 'Questions solved', hours: 'Study hours', courses: 'Recommended for you',
    getStarted: 'Get started', signIn: 'Sign in', continueBtn: 'Continue', skip: 'Skip',
    plannerTitle: 'Your study plan', plannerSubtitle: 'Build a steady weekly rhythm, one focused session at a time.', thisWeek: 'This week', previousWeek: 'Previous week', nextWeek: 'Next week', addSession: 'Add session', sessionTitle: 'What will you study?', subject: 'Subject', date: 'Date', startTime: 'Start time', endTime: 'End time', saveSession: 'Add to timetable', cancel: 'Cancel', noSessions: 'A clear day to make your own', noSessionsHint: 'Add a study session to give this day a plan.', planned: 'planned', complete: 'Complete', completed: 'Completed', delete: 'Delete session', sessionAdded: 'Study session added', overlap: 'That time overlaps another session.',
  },
  hi: {
    home: 'होम', learn: 'सीखें', planner: 'समय-सारणी', tests: 'टेस्ट', analytics: 'विश्लेषण', bookmarks: 'बुकमार्क', profile: 'प्रोफ़ाइल', settings: 'सेटिंग्स',
    search: 'कोर्स, टेस्ट और विषय खोजें…', greeting: 'सुप्रभात', welcome: 'आपका अगला लक्ष्य पहले से करीब है।',
    mission: 'आज का लक्ष्य', streak: 'पढ़ाई का क्रम', continue: 'पढ़ाई जारी रखें', challenge: 'आज की चुनौती', upcoming: 'आगामी टेस्ट',
    accuracy: 'सटीकता', questions: 'हल किए प्रश्न', hours: 'पढ़ाई के घंटे', courses: 'आपके लिए सुझाव',
    getStarted: 'शुरू करें', signIn: 'साइन इन', continueBtn: 'जारी रखें', skip: 'छोड़ें',
    plannerTitle: 'आपकी पढ़ाई की योजना', plannerSubtitle: 'हर सत्र के साथ अपनी साप्ताहिक पढ़ाई की लय बनाएँ।', thisWeek: 'इस सप्ताह', previousWeek: 'पिछला सप्ताह', nextWeek: 'अगला सप्ताह', addSession: 'सत्र जोड़ें', sessionTitle: 'क्या पढ़ेंगे?', subject: 'विषय', date: 'तारीख', startTime: 'शुरू होने का समय', endTime: 'समाप्ति का समय', saveSession: 'समय-सारणी में जोड़ें', cancel: 'रद्द करें', noSessions: 'आज की योजना आप बना सकते हैं', noSessionsHint: 'इस दिन की पढ़ाई तय करने के लिए सत्र जोड़ें।', planned: 'नियोजित', complete: 'पूरा करें', completed: 'पूरा हुआ', delete: 'सत्र हटाएँ', sessionAdded: 'पढ़ाई का सत्र जुड़ गया', overlap: 'यह समय किसी दूसरे सत्र से टकराता है।',
  },
}
