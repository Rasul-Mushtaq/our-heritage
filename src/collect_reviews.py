"""
Data collection: fetches Google Maps reviews via the Places API, or generates
a bilingual mock dataset when no API key is configured. Outputs to
data/reviews_raw.json and data/reviews_raw.csv.
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as C  # noqa: E402
import requests  # noqa: E402


# Utilities
def load_sites(path: str | None = None) -> list[dict]:
    """Load the site registry (name, coordinates, etc.)."""
    path = path or C.SITES_FILE
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)["sites"]


def detect_language(text: str) -> str:
    """Very light heuristic: presence of Arabic letters => 'ar' else 'en'."""
    for ch in text:
        if "\u0600" <= ch <= "\u06ff" or "\u0750" <= ch <= "\u077f":
            return "ar"
    return "en"


def _norm_google_review(raw: dict, site: dict, idx: int) -> dict:
    text = raw.get("text", "").strip()
    ts = raw.get("time")
    date = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d") if ts else datetime.utcnow().strftime("%Y-%m-%d")
    return {
        "review_id": f"{site['id']}_g{idx}",
        "site_id": site["id"],
        "site_name_en": site["name_en"],
        "site_name_ar": site["name_ar"],
        "author": raw.get("author_name", "Anonymous"),
        "rating": int(raw.get("rating", 0) or 0),
        "language": detect_language(text),
        "text": text,
        "timestamp": date,
        "source": "google_places",
        "lat": site["lat"],
        "lon": site["lon"],
    }


# Google Places API integration (live data)
def google_find_place(query: str, api_key: str) -> str:
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {"input": query, "inputtype": "textquery", "fields": "place_id", "key": api_key}
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  ! Find Place request failed for '{query}': {exc}")
        return ""
    data = resp.json()
    cands = data.get("candidates", [])
    return cands[0]["place_id"] if cands else ""


def google_place_details(place_id: str, api_key: str) -> dict:
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,rating,reviews,user_ratings_total,geometry",
        "reviews_sort": C.GOOGLE_REVIEW_SORT,
        "key": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  ! Place Details request failed for {place_id}: {exc}")
        return {}
    return resp.json().get("result", {})


def collect_from_google(sites: list[dict], api_key: str | None = None) -> list[dict]:
    """Collect reviews for every site via the Google Places API."""
    api_key = api_key or C.GOOGLE_PLACES_API_KEY
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is not set")

    reviews: list[dict] = []
    for site in sites:
        place_id = site.get("place_id") or google_find_place(site["google_query"], api_key)
        if not place_id:
            print(f"  ! no place_id found for {site['name_en']}")
            continue
        details = google_place_details(place_id, api_key)
        raw_reviews = details.get("reviews", [])
        for idx, raw in enumerate(raw_reviews):
            reviews.append(_norm_google_review(raw, site, idx))
        print(f"  ✓ {site['name_en']}: {len(raw_reviews)} reviews")
    return reviews


# Persistence
CSV_FIELDS = [
    "review_id", "site_id", "site_name_en", "site_name_ar", "author",
    "rating", "language", "text", "timestamp", "source", "lat", "lon",
]


def save_reviews(reviews: list[dict], json_path: str | None = None,
                 csv_path: str | None = None) -> None:
    """Persist reviews to JSON (primary) and CSV (export)."""
    json_path = json_path or C.RAW_REVIEWS_FILE
    csv_path = csv_path or C.RAW_REVIEWS_CSV
    with io.open(json_path, "w", encoding="utf-8") as fh:
        json.dump(reviews, fh, ensure_ascii=False, indent=2)
    with io.open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in reviews:
            writer.writerow({k: r.get(k, "") for k in CSV_FIELDS})


def load_reviews(path: str | None = None) -> list[dict]:
    path = path or C.RAW_REVIEWS_FILE
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def run(per_site: int = 14, force_mock: bool = False, seed: int = 42) -> list[dict]:
    C.force_utf8_output()
    sites = load_sites()
    print("=" * 70)
    print("Step 1: Data Collection")
    print("=" * 70)

    reviews: list[dict] = []
    api_key = C.GOOGLE_PLACES_API_KEY
    if api_key and not force_mock:
        print("[source] Google Places API")
        try:
            reviews = collect_from_google(sites, api_key)
        except requests.RequestException as exc:
            print(f"  ! Google Places network error ({exc}); using mock corpus.")
            reviews = []
        except Exception as exc:
            print(f"  ! Google Places failed ({exc}); using mock corpus.")
            reviews = []
    else:
        print("[source] Offline mock corpus (no API key provided).")

    if not reviews:
        from mock_data import generate_mock_reviews
        print(f"[source] Generating {per_site} mock reviews per site ...")
        reviews = generate_mock_reviews(sites, per_site=per_site, seed=seed)

    save_reviews(reviews)
    langs: dict[str, int] = {}
    for r in reviews:
        langs[r["language"]] = langs.get(r["language"], 0) + 1
    print(f"\n✓ Collected {len(reviews)} reviews across {len(sites)} sites.")
    print(f"  Language split: {langs}")
    print(f"  Saved -> {C.RAW_REVIEWS_FILE}")
    print(f"  Saved -> {C.RAW_REVIEWS_CSV}")
    return reviews


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collect reviews (Google or mock).")
    parser.add_argument("--per-site", type=int, default=14)
    parser.add_argument("--force-mock", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(per_site=args.per_site, force_mock=args.force_mock, seed=args.seed)
