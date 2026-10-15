import { useCallback } from "react";
import dayjs from "dayjs";
import "dayjs/locale/hi";
import { useAuth } from "@/context/AuthContext";

export const SUPPORTED_LANGS = ["en", "hi"];

const en = {
  // nav / shell
  "nav.calendar": "Calendar", "nav.medications": "Medications", "nav.reminders": "Reminders", "nav.reports": "Reports", "nav.chat": "Chat", "nav.resources": "Resources", "nav.settings": "Settings",
  "shell.hello": "Hello, {name}", "shell.lock": "Lock", "shell.signout": "Sign out", "shell.skip": "Skip to content",
  "shell.privacy": "Private by design. Awareness tool, not medical advice.",
  "shell.footer": "ForHer helps you notice patterns. It does not diagnose, treat, or replace a clinician. Your records are encrypted in transit, stored under your account only, and can be exported or permanently deleted at any time in Settings.",
  "sync.offline": "Offline — changes saved on this device", "sync.saving": "Saving…", "sync.error": "Sync problem", "sync.pending": "{n} unsynced draft(s)", "sync.synced": "Synced",
  // dashboard
  "dash.title": "How are you today?", "dash.logToday": "Log today", "dash.remindersTitle": "Today's reminders", "dash.toGo": "{n} to go", "dash.allClear": "All clear",
  "dash.noReminders": "No reminders scheduled for today. Reminders stay private inside the app.", "dash.done": "Done", "dash.undo": "Undo",
  "dash.loadError": "Couldn't load your calendar. Showing what we have; try again shortly.",
  // check-in
  "checkin.eyebrow": "Gentle check-in · estimate only", "checkin.title": "Your estimated window has begun. Has your period started?",
  "checkin.body": "No pressure — cycles shift. Answer only if it's useful; we'll ask again tomorrow if the window is still open.",
  "checkin.yes": "Yes, log today", "checkin.notYet": "Not yet", "checkin.context": "Estimates don't fit me",
  // estimate
  "est.eyebrow": "Cycle estimate · estimate only", "est.nextAround": "Next period may start around", "est.window": "Window", "est.cycleDay": "Cycle day", "est.avgCycle": "Avg cycle", "est.avgPeriod": "Avg period",
  "est.none": "No estimate right now", "est.lastPeriod": "Last period logged", "est.basedOn": "Based on {n} logged cycle(s).",
  "conf.moderate": "Moderate confidence", "conf.low": "Low confidence", "conf.very_low": "Very low confidence",
  // calendar
  "cal.today": "Today", "cal.prev": "Previous month", "cal.next": "Next month", "cal.legend.period": "Period logged", "cal.legend.est": "Estimated window (estimate only)",
  "cal.legend.symptoms": "Symptoms", "cal.legend.meds": "Medication taken", "cal.legend.note": "Note", "cal.est": "est.",
  // day log
  "log.subtitle": "Log only what feels useful. Everything is optional.", "log.draft": "Unsaved draft restored from this device.", "log.discard": "Discard",
  "log.period": "Period today", "log.flow": "Flow", "log.mood": "Mood", "log.symptoms": "Symptoms", "log.meds": "Medications taken", "log.notes": "Notes (private)", "log.notesPlaceholder": "Anything you want to remember…",
  "log.clear": "Clear day", "log.save": "Save day", "log.saving": "Saving…",
  // chat
  "chat.new": "New conversation", "chat.disclaimer": "AI suggestions are for cycle awareness, not medical diagnosis. ForHer never diagnoses or prescribes; for urgent symptoms contact a clinician or emergency services.",
  "chat.title": "Ask anything about your cycle", "chat.intro": "I'll explain gently, point to trusted sources, and tell you when a clinician should take a look.",
  "chat.langNote": "Replies are in English. Hindi is available in Settings.", "chat.langNoteHi": "Replies are in Hindi; if that isn't possible, you'll get English instead.",
  "chat.urgent": "This sounds like it may need prompt care. Please consider contacting a clinician or emergency services now.",
  "chat.fallbackNote": "The AI service was unavailable, so a text alternative was shown.", "chat.failed": "Couldn't reach ForHer right now. Your message wasn't lost.", "chat.retry": "Retry",
  "chat.placeholder": "Type your question… (Enter to send, Shift+Enter for a new line)", "chat.send": "Send message", "chat.thinking": "Thinking…", "chat.sources": "Educational sources (English)",
  // reports
  "rep.eyebrow": "Reports", "rep.title": "Your patterns, summarised",
  "rep.history": "Cycle history", "rep.historyEmpty": "Log at least two periods to see how your cycle length changes over time.",
  "rep.shortest": "Shortest", "rep.longest": "Longest", "rep.variation": "Variation", "rep.completed": "Completed cycles",
  "rep.moodTrends": "Moods across cycle phases", "rep.symptomTrends": "Symptoms across cycle phases",
  // options
  "opt.none": "No bleeding", "opt.spotting": "Spotting", "opt.light": "Light", "opt.medium": "Medium", "opt.heavy": "Heavy",
  "opt.Cramps": "Cramps", "opt.Headache": "Headache", "opt.Bloating": "Bloating", "opt.Fatigue": "Fatigue", "opt.Back pain": "Back pain", "opt.Breast tenderness": "Breast tenderness", "opt.Acne": "Acne", "opt.Nausea": "Nausea",
  "opt.Cravings": "Cravings", "opt.Trouble sleeping": "Trouble sleeping", "opt.Spotting": "Spotting", "opt.Discharge change": "Discharge change", "opt.Dizziness": "Dizziness", "opt.Hot flashes": "Hot flashes", "opt.Constipation": "Constipation", "opt.Diarrhoea": "Diarrhoea",
  "opt.Calm": "Calm", "opt.Content": "Content", "opt.Anxious": "Anxious", "opt.Irritable": "Irritable", "opt.Low": "Low", "opt.Tired": "Tired", "opt.Focused": "Focused", "opt.Sensitive": "Sensitive",
  // settings
  "set.language": "Language", "set.langDesc": "English and Hindi are available now. Kannada, Tamil and Malayalam unlock after translation and speech quality review.",
};

const hi = {
  "nav.calendar": "कैलेंडर", "nav.medications": "दवाइयाँ", "nav.reminders": "रिमाइंडर", "nav.reports": "रिपोर्ट", "nav.chat": "चैट", "nav.resources": "संसाधन", "nav.settings": "सेटिंग्स",
  "shell.hello": "नमस्ते, {name}", "shell.lock": "लॉक", "shell.signout": "साइन आउट", "shell.skip": "मुख्य सामग्री पर जाएँ",
  "shell.privacy": "निजता पहले। यह जागरूकता का साधन है, चिकित्सकीय सलाह नहीं।",
  "shell.footer": "ForHer आपको पैटर्न पहचानने में मदद करता है। यह निदान या इलाज नहीं करता और चिकित्सक का विकल्प नहीं है। आपके रिकॉर्ड ट्रांज़िट में एन्क्रिप्टेड हैं, केवल आपके खाते में रखे जाते हैं, और सेटिंग्स से कभी भी निर्यात या स्थायी रूप से हटाए जा सकते हैं।",
  "sync.offline": "ऑफ़लाइन — बदलाव इस डिवाइस पर सहेजे गए", "sync.saving": "सहेजा जा रहा है…", "sync.error": "सिंक में समस्या", "sync.pending": "{n} ड्राफ़्ट सिंक बाकी", "sync.synced": "सिंक हो गया",
  "dash.title": "आज आप कैसी हैं?", "dash.logToday": "आज का लॉग", "dash.remindersTitle": "आज के रिमाइंडर", "dash.toGo": "{n} बाकी", "dash.allClear": "सब पूरा",
  "dash.noReminders": "आज कोई रिमाइंडर नहीं है। रिमाइंडर ऐप के अंदर ही निजी रहते हैं।", "dash.done": "हो गया", "dash.undo": "पूर्ववत",
  "dash.loadError": "कैलेंडर लोड नहीं हो सका। जो उपलब्ध है वह दिखाया गया है; थोड़ी देर में फिर कोशिश करें।",
  "checkin.eyebrow": "हल्की पूछताछ · केवल अनुमान", "checkin.title": "आपकी अनुमानित अवधि शुरू हो गई है। क्या पीरियड शुरू हुआ?",
  "checkin.body": "कोई दबाव नहीं — चक्र बदलते रहते हैं। उपयोगी लगे तभी जवाब दें; अवधि खुली रही तो हम कल फिर पूछेंगे।",
  "checkin.yes": "हाँ, आज लॉग करें", "checkin.notYet": "अभी नहीं", "checkin.context": "अनुमान मुझ पर लागू नहीं",
  "est.eyebrow": "चक्र अनुमान · केवल अनुमान", "est.nextAround": "अगला पीरियड लगभग इस तारीख़ के आसपास शुरू हो सकता है:", "est.window": "अवधि", "est.cycleDay": "चक्र दिन", "est.avgCycle": "औसत चक्र", "est.avgPeriod": "औसत पीरियड",
  "est.none": "अभी कोई अनुमान नहीं", "est.lastPeriod": "अंतिम दर्ज पीरियड", "est.basedOn": "{n} दर्ज चक्र(ओं) के आधार पर।",
  "conf.moderate": "मध्यम विश्वास", "conf.low": "कम विश्वास", "conf.very_low": "बहुत कम विश्वास",
  "cal.today": "आज", "cal.prev": "पिछला महीना", "cal.next": "अगला महीना", "cal.legend.period": "पीरियड दर्ज", "cal.legend.est": "अनुमानित अवधि (केवल अनुमान)",
  "cal.legend.symptoms": "लक्षण", "cal.legend.meds": "दवा ली", "cal.legend.note": "नोट", "cal.est": "अनु.",
  "log.subtitle": "केवल वही लिखें जो उपयोगी लगे। सब कुछ वैकल्पिक है।", "log.draft": "इस डिवाइस से असहेजा ड्राफ़्ट वापस लाया गया।", "log.discard": "हटाएँ",
  "log.period": "आज पीरियड", "log.flow": "प्रवाह", "log.mood": "मनोदशा", "log.symptoms": "लक्षण", "log.meds": "ली गई दवाइयाँ", "log.notes": "नोट्स (निजी)", "log.notesPlaceholder": "जो भी याद रखना चाहें…",
  "log.clear": "दिन साफ़ करें", "log.save": "दिन सहेजें", "log.saving": "सहेजा जा रहा है…",
  "chat.new": "नई बातचीत", "chat.disclaimer": "AI सुझाव चक्र जागरूकता के लिए हैं, चिकित्सकीय निदान नहीं। ForHer कभी निदान या दवा नहीं लिखता; तत्काल लक्षणों के लिए चिकित्सक या आपातकालीन सेवा से संपर्क करें।",
  "chat.title": "अपने चक्र के बारे में कुछ भी पूछें", "chat.intro": "मैं सरल भाषा में समझाऊँगा, भरोसेमंद स्रोत बताऊँगा, और बताऊँगा कि कब चिकित्सक को दिखाना चाहिए।",
  "chat.langNote": "जवाब अंग्रेज़ी में हैं।", "chat.langNoteHi": "जवाब हिंदी में हैं; यदि संभव न हो तो अंग्रेज़ी में मिलेंगे।",
  "chat.urgent": "यह स्थिति तुरंत देखभाल की हो सकती है। कृपया अभी चिकित्सक या आपातकालीन सेवा से संपर्क करने पर विचार करें।",
  "chat.fallbackNote": "AI सेवा उपलब्ध नहीं थी, इसलिए टेक्स्ट विकल्प दिखाया गया।", "chat.failed": "अभी ForHer से संपर्क नहीं हो सका। आपका संदेश खोया नहीं है।", "chat.retry": "फिर कोशिश करें",
  "chat.placeholder": "अपना सवाल लिखें… (Enter भेजने के लिए, Shift+Enter नई पंक्ति)", "chat.send": "संदेश भेजें", "chat.thinking": "सोच रहा हूँ…", "chat.sources": "शैक्षिक स्रोत (अंग्रेज़ी में)",
  "rep.eyebrow": "रिपोर्ट", "rep.title": "आपके पैटर्न, संक्षेप में",
  "rep.history": "चक्र इतिहास", "rep.historyEmpty": "चक्र की लंबाई में बदलाव देखने के लिए कम से कम दो पीरियड दर्ज करें।",
  "rep.shortest": "सबसे छोटा", "rep.longest": "सबसे लंबा", "rep.variation": "अंतर", "rep.completed": "पूर्ण चक्र",
  "rep.moodTrends": "चक्र चरणों में मनोदशा", "rep.symptomTrends": "चक्र चरणों में लक्षण",
  "opt.none": "रक्तस्राव नहीं", "opt.spotting": "हल्के धब्बे", "opt.light": "हल्का", "opt.medium": "मध्यम", "opt.heavy": "भारी",
  "opt.Cramps": "ऐंठन", "opt.Headache": "सिरदर्द", "opt.Bloating": "पेट फूलना", "opt.Fatigue": "थकान", "opt.Back pain": "कमर दर्द", "opt.Breast tenderness": "स्तनों में कोमलता", "opt.Acne": "मुँहासे", "opt.Nausea": "मतली",
  "opt.Cravings": "खाने की तलब", "opt.Trouble sleeping": "नींद में परेशानी", "opt.Spotting": "हल्के धब्बे", "opt.Discharge change": "स्राव में बदलाव", "opt.Dizziness": "चक्कर", "opt.Hot flashes": "गर्मी के झोंके", "opt.Constipation": "कब्ज़", "opt.Diarrhoea": "दस्त",
  "opt.Calm": "शांत", "opt.Content": "संतुष्ट", "opt.Anxious": "चिंतित", "opt.Irritable": "चिड़चिड़ी", "opt.Low": "उदास", "opt.Tired": "थकी", "opt.Focused": "एकाग्र", "opt.Sensitive": "संवेदनशील",
  "set.language": "भाषा", "set.langDesc": "अंग्रेज़ी और हिंदी अभी उपलब्ध हैं। कन्नड़, तमिल और मलयालम अनुवाद और वाणी गुणवत्ता समीक्षा के बाद खुलेंगी।",
};

const STRINGS = { en, hi };

export function useT() {
  const { user } = useAuth();
  const lang = SUPPORTED_LANGS.includes(user?.settings?.language) ? user.settings.language : "en";
  const t = useCallback((key, vars = {}) => {
    const raw = STRINGS[lang]?.[key] ?? en[key] ?? key;
    return Object.entries(vars).reduce((s, [k, v]) => s.replaceAll(`{${k}}`, String(v)), raw);
  }, [lang]);
  const tOpt = useCallback((value) => STRINGS[lang]?.[`opt.${value}`] ?? value, [lang]);
  return { t, tOpt, lang, d: (x) => dayjs(x).locale(lang) };
}
