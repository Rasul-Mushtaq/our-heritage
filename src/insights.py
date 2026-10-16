"""
Metrics and recommendations for heritage sites based on analyzed reviews.
"""
from __future__ import annotations

from collections import Counter, defaultdict

import config as C


def satisfaction_pct(reviews: list[dict]) -> float:
    """Share of positive reviews (%)."""
    if not reviews:
        return 0.0
    pos = sum(1 for r in reviews if r["sentiment"] == "positive")
    return round(100.0 * pos / len(reviews), 1)


def avg_rating(reviews: list[dict]) -> float:
    if not reviews:
        return 0.0
    return round(sum(r["rating"] for r in reviews) / len(reviews), 2)


def sentiment_counts(reviews: list[dict]) -> dict:
    c = Counter(r["sentiment"] for r in reviews)
    return {k: c.get(k, 0) for k in ("positive", "neutral", "negative")}


def issue_counts(reviews: list[dict]) -> dict:
    """Count reviews mentioning each issue."""
    c = Counter()
    for r in reviews:
        for k in r.get("extracted_issues", []):
            c[k] += 1
    return dict(c)


def language_counts(reviews: list[dict]) -> dict:
    c = Counter(r["language"] for r in reviews)
    return {"ar": c.get("ar", 0), "en": c.get("en", 0)}


def site_metrics(reviews: list[dict], site_id: str) -> dict:
    rs = [r for r in reviews if r["site_id"] == site_id]
    return {
        "site_id": site_id,
        "total": len(rs),
        "satisfaction": satisfaction_pct(rs),
        "avg_rating": avg_rating(rs),
        "sentiment": sentiment_counts(rs),
        "issues": issue_counts(rs),
        "languages": language_counts(rs),
    }


# Corrective action recommendations per issue (bilingual).
ISSUE_RECOMMENDATIONS = {
    "cleanliness": {
        "en": "Increase cleaning frequency, add more bins and schedule daily waste collection.",
        "ar": "زيادة وتيرة التنظيف وإضافة المزيد من حاويات النفايات وجدولة جمع النفايات يومياً.",
    },
    "parking": {
        "en": "Expand/formalize parking areas and improve traffic flow & signage at the entrance.",
        "ar": "توسيع وتنظيم المواقف وتحسين انسيابية المرور واللافتات عند المدخل.",
    },
    "safety": {
        "en": "Deploy security personnel, improve lighting and install CCTV around sensitive areas.",
        "ar": "نشر عناصر أمنية وتحسين الإضاءة وتركيب كاميرات مراقبة حول المناطق الحساسة.",
    },
    "tour_guides": {
        "en": "Hire/train certified tour guides and add multilingual information panels & QR audio guides.",
        "ar": "توظيف وتدوير مرشدين سياحيين معتمدين وإضافة لوحات معلومات ولافتات صوتية متعددة اللغات.",
    },
    "pricing": {
        "en": "Review ticket pricing, introduce tiered/discounted tickets and publish prices clearly.",
        "ar": "مراجعة أسعار التذاكر وإدخال تسعيرة متدرجة وتخفيضات وعرض الأسعار بوضوح.",
    },
    "services": {
        "en": "Provide restrooms, drinking water, shaded seating and a small visitor cafe/kiosk.",
        "ar": "توفير دورات مياه وماء شرب ومقاعد مظللة ومقهى أو كشك صغير للزوار.",
    },
    "crowding": {
        "en": "Introduce timed-entry tickets and manage visitor flow during peak hours/weekends.",
        "ar": "إدخال تذاكر بمواعيد محددة وإدارة تدفق الزوار في أوقات الذروة ونهايات الأسبوع.",
    },
    "accessibility": {
        "en": "Improve access roads, add shuttle services and clear directional signage from the highway.",
        "ar": "تحسين طرق الوصول وإضافة خدمات النقل الصغير ولافتات اتجاه واضحة من الطريق السريع.",
    },
}


def severity_level(score: float) -> str:
    """Map a 0..100 priority score to a severity label."""
    if score >= 60:
        return "critical"
    if score >= 35:
        return "high"
    if score >= 15:
        return "moderate"
    return "low"


SEVERITY_STYLE = {
    "critical": {"en": "Critical", "ar": "حرجة", "emoji": "🔴", "color": "#d93025"},
    "high": {"en": "High", "ar": "عالية", "emoji": "🟠", "color": "#f0932b"},
    "moderate": {"en": "Moderate", "ar": "متوسطة", "emoji": "🟡", "color": "#f0c419"},
    "low": {"en": "Low", "ar": "منخفضة", "emoji": "🟢", "color": "#1b9e4b"},
}


def prioritized_issues(reviews: list[dict], site_id: str) -> list[dict]:
    """Issues for a site ranked by priority score (mention frequency + negativity)."""
    rs = [r for r in reviews if r["site_id"] == site_id]
    total = len(rs) or 1
    raw = issue_counts(rs)
    if not raw:
        return []

    # weight: mention in negative reviews counts double
    weighted = defaultdict(float)
    for r in rs:
        for k in r.get("extracted_issues", []):
            weighted[k] += 2.0 if r["sentiment"] == "negative" else 1.0

    max_w = max(weighted.values()) or 1.0
    ranked = []
    for k, w in raw.items():
        freq_pct = 100.0 * w / total
        norm = 100.0 * weighted[k] / max_w
        score = round(0.6 * norm + 0.4 * freq_pct, 1)
        ranked.append({
            "key": k,
            "en": C.ISSUE_CATEGORIES[k]["en"],
            "ar": C.ISSUE_CATEGORIES[k]["ar"],
            "count": w,
            "frequency_pct": round(freq_pct, 1),
            "score": score,
            "severity": severity_level(score),
            "recommendation_en": ISSUE_RECOMMENDATIONS[k]["en"],
            "recommendation_ar": ISSUE_RECOMMENDATIONS[k]["ar"],
        })
    ranked.sort(key=lambda x: -x["score"])
    return ranked


def generate_insights(reviews: list[dict], site_id: str, top_n: int = 3) -> list[dict]:
    """Top N recommendations for a site (most critical first)."""
    return prioritized_issues(reviews, site_id)[:top_n]

