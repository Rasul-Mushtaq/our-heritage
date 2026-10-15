"""
Offline bilingual mock review corpus for Iraqi heritage sites.

Used when no Google Places API key is available so the entire prototype runs
end-to-end. Reviews are realistic, written in Modern Standard Arabic / Iraqi
dialect and English, and intentionally contain the pain-point issues the AI
engine must detect (cleanliness, parking, safety, guides, pricing, services...).
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

POSITIVE_AR = [
    "موقع رائع وتاريخي بامتياز، تجربة لا تُنسى والمنظر خلاب. أنصح بزيارته.",
    "أجمل ما في العراق هذا المكان، نظيف نسبياً والمرشدون كانوا متعاونين.",
    "تجربة مذهلة، استمتعنا كثيراً بالزيارة والتصوير. يستحق الزيارة فعلاً.",
    "مكان تاريخي عظيم، الأسعار معقولة والموظفون محترمون ومتعاونون.",
    "زيارة أكثر من رائعة، شعرت بالفخر والحضارة العراقية العريقة.",
    "الموقع منظم وجيد والمواقف متوفرة. تجربة جميلة مع العائلة.",
]
NEUTRAL_AR = [
    "الموقع جيد لكن يحتاج إلى صيانة أكبر، والطريق المؤدي إليه سيء.",
    "تجربة عادية، المكان يستحق الزيارة لكن الزحام كان شديداً.",
    "لا بأس به، لكن غياب المرشدين السياحيين أفقدنا الكثير من المعلومات.",
    "المكان جميل لكن لا توجد خدمات كافية مثل الماء والمقاعد والظل.",
]
NEGATIVE_AR = [
    "للأسف المكان مهمل وغير نظيف والقمامة في كل مكان، وضعف الأمان ملاحظ.",
    "لا يوجد مواقف كافية للسيارات والزحام المروري مزعج جداً.",
    "غياب المرشدين السياحيين واللوحات الإرشادية جعل الزيارة مملة.",
    "الأسعار غالية جداً مقابل الخدمات المحدودة المتوفرة.",
    "لا توجد دورات مياه ولا ماء بارد ولا مقهى، خدمات شبه معدومة.",
    "الموقع بعيد والطريق وعر ويصعب الوصول إليه بدون مواصلات مناسبة.",
    "شعرت بعدم الأمان لقلة الحراسة، وهناك مخاوف من السرقة.",
    "المكان قذر والريحة كريهة والحاويات ممتلئة، إهمال واضح.",
]

POSITIVE_EN = [
    "Absolutely breathtaking! A must-visit for anyone interested in history.",
    "Amazing site, well preserved and the views are stunning. Highly recommend.",
    "Fantastic experience. The staff were friendly and the place was clean.",
    "Incredible place full of history. Reasonable ticket price and worth every cent.",
    "Loved every minute. Great parking and easy to reach from the city.",
    "One of the most impressive historical sites I have ever seen!",
]
NEUTRAL_EN = [
    "Interesting site but needs better maintenance and signage.",
    "Worth a visit, though it was very crowded on the weekend.",
    "Nice place but the lack of tour guides meant we missed a lot of context.",
    "Good overall, but limited facilities - no shade, water or seating.",
]
NEGATIVE_EN = [
    "Very disappointed. The site was dirty and full of trash, no one was cleaning.",
    "Terrible parking situation and heavy traffic to get here.",
    "No tour guides or information boards, so the visit felt incomplete.",
    "Ticket was overpriced for what you get, very few services.",
    "No restrooms, no water, no cafe - basically no services at all.",
    "Hard to reach, rough road and no public transport options.",
    "Felt unsafe due to lack of security presence near the ruins.",
    "The place is neglected and smelly, overflowing bins everywhere.",
]

AUTHORS_AR = ["أحمد", "زينب", "علي", "فاطمة", "حسن", "مريم", "عمر", "نور", "كرار", "رند", "سجاد", "هدى"]
AUTHORS_EN = ["Sarah M.", "James T.", "Layla A.", "Omar K.", "Emily R.", "Youssef D.",
              "Anna P.", "David L.", "Huda S.", "Mark W.", "Noor H.", "Tom B."]


def _weighted_rating(profile: str) -> int:
    """Return a rating consistent with a site's overall quality profile."""
    if profile == "high":   # mostly happy visitors
        return random.choices([5, 4, 3, 2, 1], weights=[45, 35, 12, 5, 3])[0]
    if profile == "medium":
        return random.choices([5, 4, 3, 2, 1], weights=[25, 30, 25, 12, 8])[0]
    return random.choices([5, 4, 3, 2, 1], weights=[15, 20, 25, 25, 15])[0]  # low


def _sentiment_for_rating(rating: int) -> str:
    if rating >= 4:
        return "positive"
    if rating == 3:
        return "neutral"
    return "negative"


SITE_PROFILES = {
    "hatra": "medium",
    "babylon": "medium",
    "ur": "low",
    "erbil_citadel": "high",
    "samarra": "low",
    "nimrud": "low",
    "ctesiphon": "medium",
    "lagash": "low",
}


def generate_mock_reviews(sites: list[dict], per_site: int = 14,
                          seed: int = 42) -> list[dict]:
    """Generate a realistic bilingual review set for each site."""
    rng = random.Random(seed)
    reviews: list[dict] = []
    end_date = datetime.utcnow()

    for site in sites:
        profile = SITE_PROFILES.get(site["id"], "medium")
        for i in range(per_site):
            rating = _weighted_rating(profile)
            lang = "ar" if rng.random() < 0.55 else "en"
            pools = {
                "positive": (POSITIVE_AR if lang == "ar" else POSITIVE_EN),
                "neutral": (NEUTRAL_AR if lang == "ar" else NEUTRAL_EN),
                "negative": (NEGATIVE_AR if lang == "ar" else NEGATIVE_EN),
            }
            sent = _sentiment_for_rating(rating)
            text = rng.choice(pools[sent])
            author = rng.choice(AUTHORS_AR if lang == "ar" else AUTHORS_EN)
            days_ago = rng.randint(0, 240)
            date = (end_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            reviews.append({
                "review_id": f"{site['id']}_m{i}",
                "site_id": site["id"],
                "site_name_en": site["name_en"],
                "site_name_ar": site["name_ar"],
                "author": author,
                "rating": rating,
                "language": lang,
                "text": text,
                "timestamp": date,
                "source": "mock",
                "lat": site["lat"],
                "lon": site["lon"],
            })
    return reviews
