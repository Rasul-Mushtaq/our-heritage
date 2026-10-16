"""
Shared configuration: file paths, issue categories, sentiment labels, API settings.
"""
from __future__ import annotations

import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SRC_DIR = os.path.join(BASE_DIR, "src")

os.makedirs(DATA_DIR, exist_ok=True)

SITES_FILE = os.path.join(DATA_DIR, "sites.json")
RAW_REVIEWS_FILE = os.path.join(DATA_DIR, "reviews_raw.json")
RAW_REVIEWS_CSV = os.path.join(DATA_DIR, "reviews_raw.csv")
ANALYZED_FILE = os.path.join(DATA_DIR, "reviews_analyzed.json")

# Application identity (bilingual)
APP_TITLE_AR = "تراثنا بعيون زواره"
APP_TITLE_EN = "Our Heritage"
APP_SUBTITLE_AR = "تحليل آراء الزوار وإدارة المواقع الأثرية"
APP_SUBTITLE_EN = "Visitor review analytics for Iraqi heritage sites"

# API / LLM settings (read from environment; optional)
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# LLM provider: "gemini", "openai", or "offline" ("auto" picks an available key)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto")

# Review sort order for Google Place Details
GOOGLE_REVIEW_SORT = "most_relevant"


def force_utf8_output() -> None:
    """Ensure stdout/stderr use UTF-8 so Arabic prints correctly on Windows."""
    import sys
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


# Issue categories with bilingual labels and keywords for the offline classifier.
ISSUE_CATEGORIES = {
    "cleanliness": {
        "en": "Cleanliness",
        "ar": "النظافة",
        "keywords_en": [
            "dirty", "trash", "garbage", "rubbish", "litter", "smell", "stink",
            "unclean", "filthy", "waste", "bin", "not clean", "no one cleans",
        ],
        "keywords_ar": [
            "نظافة", "قذر", "قذارة", "اتساخ", "وسخ", "زبالة", "قمامة", "نفايات",
            "ريحة", "رائحة", "كريه", "منتن", "حاويات", "مهمل",
        ],
    },
    "parking": {
        "en": "Parking",
        "ar": "مواقف السيارات",
        "keywords_en": [
            "parking", "park", "car park", "no space", "could not park",
            "parked far", "traffic jam", "no parking",
        ],
        "keywords_ar": [
            "مواقف", "باركينغ", "باركنك", "وقوف", "توقف", "سيارة", "سيارات",
            "زحمة مرورية", "لا يوجد موقف", "سير",
        ],
    },
    "safety": {
        "en": "Safety",
        "ar": "الأمان",
        "keywords_en": [
            "unsafe", "danger", "dangerous", "no security", "security",
            "thief", "theft", "robbed", "police", "afraid", "scared", "risk",
        ],
        "keywords_ar": [
            "أمان", "امن", "خطير", "خطر", "لا يوجد حماية", "حماية", "حراسة",
            "سارق", "سرقة", "سرقوا", "شرطة", "خفت", "خائف", "مخاطر",
        ],
    },
    "tour_guides": {
        "en": "Tour Guides",
        "ar": "غياب المرشدين",
        "keywords_en": [
            "guide", "guides", "no guide", "tour guide", "no explanation",
            "no information", "no signage", "no sign", "audio guide",
        ],
        "keywords_ar": [
            "مرشد", "مرشدين", "المرشد", "دليل", "ادلة", "لا يوجد مرشد",
            "غياب المرشدين", "شرح", "توضيح", "لوحة", "لوحات", "لافتات",
            "ارشاد", "إرشاد", "دليل سياحي",
        ],
    },
    "pricing": {
        "en": "Ticket Pricing",
        "ar": "التذاكر والأسعار",
        "keywords_en": [
            "ticket", "tickets", "price", "pricing", "expensive", "overpriced",
            "entry fee", "admission", "cost", "too much money", "fee",
        ],
        "keywords_ar": [
            "تذكرة", "تذاكر", "سعر", "اسعار", "أسعار", "ثمن", "غالي", "غالية",
            "مبالغ", "اجور", "رسوم", "تكلفة", "مكلف",
        ],
    },
    "services": {
        "en": "Lack of Services",
        "ar": "قلة الخدمات",
        "keywords_en": [
            "service", "services", "no water", "no food", "no cafe",
            "no restroom", "restroom", "toilet", "no shade", "no seating",
            "no facilities", "closed cafe", "nothing available",
        ],
        "keywords_ar": [
            "خدمات", "خدمة", "لا يوجد ماء", "ماء", "طعام", "مطعم", "مقهى",
            "كافيتيريا", "دورات مياه", "حمام", "مرحاض", "ظل", "مقاعد",
            "مرافق", "قلة الخدمات", "لا شيء متوفر",
        ],
    },
    "crowding": {
        "en": "Crowding",
        "ar": "الزحام",
        "keywords_en": [
            "crowded", "too many people", "packed", "queue", "long line",
            "busy", "overcrowded",
        ],
        "keywords_ar": [
            "زحام", "زحم", "ازدحام", "مزدحم", "الناس كثير", "طابور", "صف طويل",
            "مزدحمة",
        ],
    },
    "accessibility": {
        "en": "Accessibility",
        "ar": "سهولة الوصول",
        "keywords_en": [
            "far", "distance", "road", "rough road", "hard to reach",
            "no transport", "difficult access", "bumpy",
        ],
        "keywords_ar": [
            "بعيد", "بعيدة", "المسافة", "الطريق", "طريق سيء", "وعر",
            "صعب الوصول", "لا يوجد مواصلات", "وصول صعب",
        ],
    },
}

ISSUE_KEYS = list(ISSUE_CATEGORIES.keys())

SENTIMENT_LABELS = {
    "positive": {"en": "Positive", "ar": "إيجابي", "emoji": "😊", "color": "#1b9e4b"},
    "neutral": {"en": "Neutral", "ar": "محايد", "emoji": "😐", "color": "#f0a30a"},
    "negative": {"en": "Negative", "ar": "سلبي", "emoji": "😞", "color": "#d93025"},
}

POSITIVE_KEYWORDS_EN = [
    "amazing", "beautiful", "great", "wonderful", "excellent", "fantastic",
    "love", "loved", "stunning", "breathtaking", "must", "worth", "recommend",
    "incredible", "historic", "magical", "best", "awesome", "impressive",
    "clean", "friendly", "well", "enjoy",
]
NEGATIVE_KEYWORDS_EN = [
    "bad", "poor", "terrible", "awful", "dirty", "disappointing",
    "disappointed", "worst", "horrible", "ruined", "sad", "boring",
    "avoid", "waste", "neglected", "not worth",
]
POSITIVE_KEYWORDS_AR = [
    "رائع", "جميل", "ممتاز", "أحببته", "أحببت", "يعجبني", "اعجبني", "خلاب",
    "مذهل", "يستحق", "أنصح", "انصح", "اكثر من رائع", "أكثر من رائع",
    "رايعة", "بديع", "متميز", "نظيف",
]
NEGATIVE_KEYWORDS_AR = [
    "سيء", "سيئة", "ضعيف", "ضعيفة", "مخيب", "مخيبة", "محزن", "محزنة",
    "كارثي", "لا أنصح", "لا انصح", "مهمل", "مهملة", "قذر", "زحمة",
    "مبالغ", "غالي", "اسوء", "أسوأ",
]

