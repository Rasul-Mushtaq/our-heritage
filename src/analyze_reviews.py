"""
STEP 2 - AI Sentiment Analysis & Issue Classification Engine.

Processes raw review texts (Arabic + English) to:
  1. Classify satisfaction/sentiment  -> positive | neutral | negative
  2. Tag specific complaint issues    -> cleanliness, parking, safety,
                                         tour_guides, pricing, services,
                                         crowding, accessibility (multi-label)

Two engines are supported:
  * LLM engine   (Gemini / OpenAI) - used when an API key is available.
                  Returns strict JSON: {sentiment, extracted_issues}.
  * Offline engine- a deterministic, bilingual keyword/scoring classifier
                  used as fallback so the prototype always runs.

The final output enriches every review and is saved to
data/reviews_analyzed.json with the required schema:
  site_name, review_text, rating, language, sentiment, extracted_issues
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as C  # noqa: E402


# Text normalization helpers
def normalize_arabic(text: str) -> str:
    """Light Arabic normalization to improve keyword matching."""
    repl = {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ى": "ي", "ة": "ه",
        "ؤ": "و", "ئ": "ي",
    }
    for a, b in repl.items():
        text = text.replace(a, b)
    # remove tatweel and diacritics
    text = re.sub("[\u0640]", "", text)
    text = re.sub("[\u064b-\u0652]", "", text)
    return text


def _prep(text: str) -> str:
    return normalize_arabic(text.lower())



# Offline rule-based engine (bilingual, deterministic)
def detect_issues_offline(text: str) -> list[str]:
    """Return the list of issue keys detected in the review text."""
    t = _prep(text)
    found: list[str] = []
    for key, spec in C.ISSUE_CATEGORIES.items():
        kws = spec["keywords_en"] + [normalize_arabic(k) for k in spec["keywords_ar"]]
        for kw in kws:
            kw_n = normalize_arabic(kw.lower())
            if kw_n and kw_n in t:
                found.append(key)
                break
    return found


def detect_sentiment_offline(text: str, rating: int) -> str:
    """Combine keyword polarity with the numeric rating for a robust label."""
    t = _prep(text)
    pos = sum(1 for k in C.POSITIVE_KEYWORDS_EN if k in t)
    pos += sum(1 for k in C.POSITIVE_KEYWORDS_AR if normalize_arabic(k) in t)
    neg = sum(1 for k in C.NEGATIVE_KEYWORDS_EN if k in t)
    neg += sum(1 for k in C.NEGATIVE_KEYWORDS_AR if normalize_arabic(k) in t)

    # Rating is a strong prior; keywords refine it.
    if rating >= 4:
        base = "positive"
    elif rating == 3:
        base = "neutral"
    else:
        base = "negative"

    # If keywords strongly disagree with the rating, trust the keywords a bit.
    if pos >= neg + 2 and base == "negative":
        return "neutral"
    if neg >= pos + 2 and base == "positive":
        return "neutral"
    return base


# LLM engine (Gemini / OpenAI) - used when API keys are available
ISSUE_KEYS_STR = ", ".join(C.ISSUE_KEYS)


def _build_prompt(text: str, language: str) -> str:
    return (
        "You are an expert tourism analyst for Iraqi heritage sites.\n"
        f"Analyze the following visitor review (language: {language}).\n\n"
        "Return ONLY a valid JSON object (no markdown, no extra text) with:\n"
        '  "sentiment": one of "positive", "neutral", "negative"\n'
        '  "extracted_issues": an array of applicable issue tags from this exact set: '
        f"[{ISSUE_KEYS_STR}] (empty array if none).\n\n"
        "Only include issues that are actually complained about. "
        "Do not invent issues.\n\n"
        f'Review: """{text}"""'
    )


def _parse_llm_json(raw: str) -> dict | None:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw).strip()
    try:
        data = json.loads(raw)
        sent = str(data.get("sentiment", "neutral")).lower()
        if sent not in ("positive", "neutral", "negative"):
            sent = "neutral"
        issues = [i for i in data.get("extracted_issues", []) if i in C.ISSUE_KEYS]
        return {"sentiment": sent, "extracted_issues": issues}
    except Exception:
        return None


def classify_with_gemini(text: str, language: str) -> dict | None:
    import requests
    key = C.GEMINI_API_KEY
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {"contents": [{"parts": [{"text": _build_prompt(text, language)}]}],
            "generationConfig": {"temperature": 0.1}}
    resp = requests.post(url, params={"key": key}, json=body, timeout=40)
    resp.raise_for_status()
    data = resp.json()
    txt = data["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_llm_json(txt)


def classify_with_openai(text: str, language: str) -> dict | None:
    import requests
    key = C.OPENAI_API_KEY
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}"}
    body = {"model": model, "temperature": 0.1,
            "messages": [{"role": "user", "content": _build_prompt(text, language)}]}
    resp = requests.post(url, headers=headers, json=body, timeout=40)
    resp.raise_for_status()
    data = resp.json()
    txt = data["choices"][0]["message"]["content"]
    return _parse_llm_json(txt)


def pick_llm_provider() -> str | None:
    if C.LLM_PROVIDER == "gemini" and C.GEMINI_API_KEY:
        return "gemini"
    if C.LLM_PROVIDER == "openai" and C.OPENAI_API_KEY:
        return "openai"
    if C.LLM_PROVIDER == "auto":
        if C.GEMINI_API_KEY:
            return "gemini"
        if C.OPENAI_API_KEY:
            return "openai"
    return None



# Unified classification
def analyze_review(review: dict, provider: str | None = None) -> dict:
    """Classify a single review, returning the full enriched record.

    Output schema (as required by the platform spec):
      site_name, review_text, rating, language, sentiment, extracted_issues
    """
    text = review["text"]
    rating = int(review.get("rating", 0) or 0)
    language = review.get("language") or ("ar" if _has_arabic(text) else "en")

    result = None
    provider = provider or pick_llm_provider()
    if provider == "gemini":
        try:
            result = classify_with_gemini(text, language)
        except Exception as exc:
            print(f"    ! Gemini failed: {exc}; using offline engine.")
    elif provider == "openai":
        try:
            result = classify_with_openai(text, language)
        except Exception as exc:
            print(f"    ! OpenAI failed: {exc}; using offline engine.")

    if result is None:
        result = {
            "sentiment": detect_sentiment_offline(text, rating),
            "extracted_issues": detect_issues_offline(text),
        }

    issues = result["extracted_issues"]
    enriched = {
        "review_id": review.get("review_id"),
        "site_id": review.get("site_id"),
        "site_name": review.get("site_name_en"),
        "site_name_ar": review.get("site_name_ar"),
        "review_text": text,
        "author": review.get("author", "Anonymous"),
        "rating": rating,
        "language": language,
        "sentiment": result["sentiment"],
        "extracted_issues": issues,
        "issues_labeled": [
            {"key": k, "en": C.ISSUE_CATEGORIES[k]["en"], "ar": C.ISSUE_CATEGORIES[k]["ar"]}
            for k in issues
        ],
        "timestamp": review.get("timestamp"),
        "source": review.get("source", "mock"),
        "lat": review.get("lat"),
        "lon": review.get("lon"),
        "engine": "llm" if provider else "offline",
    }
    return enriched


def _has_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06ff" for ch in text)

    return base



# Batch arrangement
def load_raw_reviews(path: str | None = None) -> list[dict]:
    path = path or C.RAW_REVIEWS_FILE
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def run(raw_path: str | None = None, out_path: str | None = None,
        limit: int | None = None) -> list[dict]:
    """Analyze all raw reviews and persist the enriched output."""
    C.force_utf8_output()
    out_path = out_path or C.ANALYZED_FILE
    provider = pick_llm_provider()
    print("=" * 70)
    print("STEP 2: AI Sentiment & Issue Classification")
    print("=" * 70)
    print(f"[engine] {'LLM: ' + provider if provider else 'Offline bilingual classifier'}")

    reviews = load_raw_reviews(raw_path)
    if limit:
        reviews = reviews[:limit]

    analyzed: list[dict] = []
    for i, r in enumerate(reviews, 1):
        analyzed.append(analyze_review(r, provider))
        if i % 20 == 0 or i == len(reviews):
            print(f"  processed {i}/{len(reviews)} reviews ...")

    with io.open(out_path, "w", encoding="utf-8") as fh:
        json.dump(analyzed, fh, ensure_ascii=False, indent=2)

    # quick summary
    sent_counts: dict[str, int] = {}
    issue_counts: dict[str, int] = {}
    for a in analyzed:
        sent_counts[a["sentiment"]] = sent_counts.get(a["sentiment"], 0) + 1
        for k in a["extracted_issues"]:
            issue_counts[k] = issue_counts.get(k, 0) + 1

    print(f"\n✓ Analyzed {len(analyzed)} reviews.")
    print(f"  Sentiment: {sent_counts}")
    top = sorted(issue_counts.items(), key=lambda x: -x[1])[:6]
    print(f"  Top issues: {top}")
    print(f"  Saved -> {out_path}")
    return analyzed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze reviews (LLM or offline).")
    parser.add_argument("--raw", default=None, help="Path to raw reviews JSON")
    parser.add_argument("--out", default=None, help="Path to output JSON")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run(raw_path=args.raw, out_path=args.out, limit=args.limit)
