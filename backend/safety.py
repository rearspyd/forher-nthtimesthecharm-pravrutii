import re

SOURCES_VERSION = "2026-06"

SOURCES = [
    {"id": "acog-menstruation", "title": "ACOG — Your Menstrual Cycle", "org": "American College of Obstetricians and Gynecologists",
     "url": "https://www.acog.org/womens-health/faqs/your-first-period-especially-for-teens", "topics": ["cycle", "period", "general"]},
    {"id": "nhs-periods", "title": "NHS — Periods", "org": "NHS (UK)", "url": "https://www.nhs.uk/conditions/periods/", "topics": ["cycle", "period", "general", "pain"]},
    {"id": "nhs-irregular", "title": "NHS — Irregular periods", "org": "NHS (UK)", "url": "https://www.nhs.uk/conditions/irregular-periods/", "topics": ["irregular"]},
    {"id": "nhs-heavy", "title": "NHS — Heavy periods", "org": "NHS (UK)", "url": "https://www.nhs.uk/conditions/heavy-periods/", "topics": ["heavy", "flow"]},
    {"id": "owh-pcos", "title": "Office on Women's Health — PCOS", "org": "U.S. Department of Health & Human Services",
     "url": "https://www.womenshealth.gov/a-z-topics/polycystic-ovary-syndrome", "topics": ["pcos"]},
    {"id": "owh-pms", "title": "Office on Women's Health — PMS", "org": "U.S. Department of Health & Human Services",
     "url": "https://www.womenshealth.gov/menstrual-cycle/premenstrual-syndrome", "topics": ["mood", "pms", "symptoms"]},
    {"id": "nhs-endometriosis", "title": "NHS — Endometriosis", "org": "NHS (UK)", "url": "https://www.nhs.uk/conditions/endometriosis/", "topics": ["pain", "endometriosis"]},
    {"id": "nhs-menopause", "title": "NHS — Menopause", "org": "NHS (UK)", "url": "https://www.nhs.uk/conditions/menopause/", "topics": ["menopause", "perimenopause"]},
    {"id": "who-sexual-health", "title": "WHO — Sexual and reproductive health", "org": "World Health Organization",
     "url": "https://www.who.int/health-topics/sexual-and-reproductive-health-and-research", "topics": ["general"]},
]

TOPIC_KEYWORDS = {
    "pcos": ["pcos", "polycystic"],
    "irregular": ["irregular", "late period", "missed", "skipped", "unpredictable"],
    "heavy": ["heavy", "clots", "soaking", "flooding"],
    "pain": ["pain", "cramp", "ache", "hurts"],
    "mood": ["mood", "anxious", "sad", "irritable", "pms", "depress"],
    "menopause": ["menopause", "perimenopause", "hot flash", "hot flush"],
    "endometriosis": ["endometriosis"],
}

URGENT_PATTERNS = [
    r"soak(ing|ed)? (a|one|1|through) (pad|tampon)s? (every|an|per) (hour|hr)",
    r"faint", r"passed out", r"dizzy and bleeding", r"can'?t stand", r"severe pain",
    r"worst pain", r"pregnan\w* and bleed", r"bleeding .*pregnan", r"fever .*(period|cramp)",
    r"suicid", r"kill myself", r"end my life", r"self[- ]harm", r"hurt myself",
]

DIAGNOSTIC_PHRASES = [
    r"\byou have (pcos|endometriosis|fibroids|an infection|cancer|pid)\b",
    r"\bthis is (definitely|certainly) (pcos|endometriosis)\b",
    r"\bi diagnose\b", r"\bmy diagnosis\b",
    r"\byou should take \d+\s?mg\b", r"\btake \d+\s?(mg|tablets?)\b",
]

SYSTEM_PROMPT = """You are ForHer, a calm, empathetic cycle-awareness companion. You are NOT a doctor and ForHer is NOT a medical device.

Hard rules — never break them:
1. Never diagnose any condition (e.g., PCOS, endometriosis, pregnancy, infection, cancer). If asked "could this be X?", explain what X generally is in plain words, which patterns clinicians usually look at, and clearly say only a qualified clinician can evaluate this after examination and tests.
2. Never prescribe or recommend specific medications or doses. You may mention that over-the-counter options exist and should be discussed with a pharmacist or clinician.
3. Never imply certainty. Use language like "may", "some people", "it can help to", "a clinician can check".
4. Lead with empathy in one short sentence, then give practical, educational information in short paragraphs or a brief list. Keep responses under ~180 words unless asked for more.
5. Point to credible educational sources (NHS, ACOG, WHO, Office on Women's Health) by name; do not invent URLs or statistics.
6. Escalate kindly: for heavy bleeding soaking a pad or tampon every hour for 2+ hours, fainting, severe or sudden pain, fever with pelvic pain, bleeding during pregnancy, or thoughts of self-harm — say clearly to seek urgent/emergency care or a crisis line now.
7. Respect the user's context: cycle patterns differ widely; irregular cycles, postpartum, breastfeeding, perimenopause, contraception and stress all change what is "typical". Estimates in the app are estimates.
8. Respond in the language given in the Language instruction below. If the user writes in another language that is not yet supported, respond in English and gently say more languages are coming.
9. Do not ask for or repeat sensitive identifiers. Keep a warm, plain, non-judgemental tone. No emojis.
"""


def detect_topics(text: str) -> list[str]:
    t = text.lower()
    return [topic for topic, kws in TOPIC_KEYWORDS.items() if any(k in t for k in kws)]


def sources_for(text: str) -> list[dict]:
    topics = set(detect_topics(text)) or {"general"}
    picked = [s for s in SOURCES if topics & set(s["topics"])]
    return picked[:3] or SOURCES[:2]


def is_urgent(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in URGENT_PATTERNS)


def is_self_harm(text: str) -> bool:
    return bool(re.search(r"suicid|kill myself|end my life|self[- ]harm|hurt myself", text.lower()))


URGENT_NOTE = (
    "If you are bleeding through a pad or tampon every hour for two hours or more, feel faint, "
    "have severe or sudden pain, or are bleeding while pregnant, please seek urgent medical care now "
    "or call your local emergency number."
)
SELF_HARM_NOTE = (
    "You deserve support right now. If you are thinking about harming yourself, please contact a crisis line "
    "or emergency services immediately (in India: Tele-MANAS 14416 or KIRAN 1800-599-0019; elsewhere, your local emergency number)."
)
FALLBACK_TEXT = (
    "I'm having trouble responding right now, so here is a text alternative. Cycle experiences vary widely from person to person. "
    "If something feels new, severe, or worrying, a qualified clinician can look into it properly. "
    "You can also read trusted educational sources listed below while you wait."
)

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi"}

LOCALIZED = {
    "hi": {
        "urgent": "यदि आप दो घंटे या उससे अधिक समय तक हर घंटे एक पैड या टैम्पोन पूरी तरह भिगो रही हैं, बेहोशी जैसा महसूस हो रहा है, तेज़ या अचानक दर्द है, या गर्भावस्था के दौरान रक्तस्राव हो रहा है, तो कृपया अभी तुरंत चिकित्सा सहायता लें या अपने स्थानीय आपातकालीन नंबर पर कॉल करें।",
        "self_harm": "आप अभी सहारे की हक़दार हैं। यदि आपके मन में खुद को नुकसान पहुँचाने के विचार आ रहे हैं, तो कृपया तुरंत किसी हेल्पलाइन या आपातकालीन सेवा से संपर्क करें (भारत में: टेली-मानस 14416 या किरण 1800-599-0019)।",
        "fallback": "मुझे अभी जवाब देने में कठिनाई हो रही है, इसलिए यह एक टेक्स्ट विकल्प है। मासिक चक्र के अनुभव हर व्यक्ति में बहुत अलग होते हैं। यदि कुछ नया, गंभीर या चिंताजनक लगे, तो एक योग्य चिकित्सक इसे ठीक से देख सकते हैं। नीचे दिए गए विश्वसनीय स्रोत भी पढ़ सकती हैं।",
        "reminder": "\n\nएक विनम्र याद दिलाना: यह केवल सामान्य जानकारी है। ForHer निदान या दवा नहीं लिख सकता; केवल एक योग्य चिकित्सक ही आपकी स्थिति का मूल्यांकन कर सकते हैं।",
    }
}


def localized(key: str, lang: str) -> str:
    defaults = {"urgent": URGENT_NOTE, "self_harm": SELF_HARM_NOTE, "fallback": FALLBACK_TEXT,
                "reminder": "\n\nA gentle reminder: this is general information only. ForHer cannot diagnose or prescribe; only a qualified clinician can evaluate your situation."}
    return LOCALIZED.get(lang, {}).get(key) or defaults[key]


def language_instruction(lang: str) -> str:
    if lang == "hi":
        return ("\nLanguage: Respond in simple, warm Hindi written in Devanagari script. Keep medical terms understandable (you may add the English term in brackets). "
                "If you cannot answer well in Hindi, answer in English instead and begin with one short Hindi sentence apologising for that.")
    return "\nLanguage: Respond in English."


def post_check(text: str, lang: str = "en") -> tuple[str, list[str]]:
    flags = []
    for pattern in DIAGNOSTIC_PHRASES:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append(pattern)
    if flags:
        text += localized("reminder", lang)
    return text, flags
