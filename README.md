# تراثنا بعيون زواره - Our Heritage

A simple analytics dashboard for Iraqi heritage sites. It reads visitor reviews (Arabic and English), tags them with sentiment and issue categories, and displays the results in a Streamlit app with a map of Iraq.

---

## What it does

1. **Collect reviews** (`src/collect_reviews.py`): Fetches Google Maps reviews via the Google Places API, or uses a built-in bilingual mock dataset when no API key is configured. Saves results to `data/reviews_raw.json` and `data/reviews_raw.csv`.

2. **Analyze reviews** (`src/analyze_reviews.py`): Classifies each review as positive, neutral, or negative, and tags issues such as cleanliness, parking, safety, pricing, etc. Uses an LLM (Gemini or OpenAI) when an API key is available, otherwise falls back to a built-in keyword-based classifier. Saves results to `data/reviews_analyzed.json`.

3. **Dashboard** (`src/dashboard.py`): Streamlit app showing a map of Iraq with site markers, satisfaction metrics, issue breakdowns, and a filterable review feed.

---

## Project structure

```
culture_hackathon/
├── run_pipeline.py            # Run the full pipeline (collect + analyze + dashboard)
├── requirements.txt
├── .env.example               # Copy to .env and add API keys
├── README.md
├── src/
│   ├── config.py              # Paths, issue categories, API settings
│   ├── collect_reviews.py     # Review collection (Google Places / mock)
│   ├── mock_data.py           # Offline bilingual review corpus
│   ├── analyze_reviews.py     # Sentiment + issue classification
│   ├── insights.py            # Metrics and recommendations
│   └── dashboard.py           # Streamlit dashboard
└── data/
    ├── sites.json             # Site registry (names, coordinates)
    ├── reviews_raw.json       # Collected reviews
    ├── reviews_raw.csv        # CSV export of collected reviews
    └── reviews_analyzed.json  # Analyzed reviews (sentiment + issues)
```

---

## Getting started

```bash
# 1. (optional) create a virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate  |  macOS/Linux: source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the pipeline and launch the dashboard
python run_pipeline.py
```

The dashboard opens at http://localhost:8501. Without API keys, the app uses the built-in mock dataset.

### Run steps individually

```bash
# Step 1: collect reviews
python src/collect_reviews.py --per-site 14

# Step 2: analyze sentiment and issues
python src/analyze_reviews.py

# Step 3: launch dashboard
streamlit run src/dashboard.py
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in values as needed:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `GOOGLE_PLACES_API_KEY` | Google Places API key for live review collection (optional) |
| `GEMINI_API_KEY` | Gemini API key for LLM-based classification (optional) |
| `OPENAI_API_KEY` | OpenAI API key for LLM-based classification (optional) |
| `LLM_PROVIDER` | `auto`, `gemini`, `openai`, or `offline` (default: `auto`) |

If no API key is set, the pipeline uses the mock dataset and the offline keyword classifier.

---

## Data schema

Each analyzed review (`data/reviews_analyzed.json`) contains the fields
required by the platform spec plus useful metadata:

```json
{
  "review_id": "babylon_m3",
  "site_id": "babylon",
  "site_name": "Babylon",
  "site_name_ar": "بابل",
  "review_text": "الأسعار غالية جداً مقابل الخدمات المحدودة المتوفرة.",
  "author": "زينب",
  "rating": 2,
  "language": "ar",
  "sentiment": "negative",
  "extracted_issues": ["pricing", "services"],
  "issues_labeled": [
    { "key": "pricing", "en": "Ticket Pricing", "ar": "التذاكر والأسعار" }
  ],
  "timestamp": "2026-03-11",
  "source": "mock",
  "lat": 32.5364,
  "lon": 44.4208,
  "engine": "offline"
}
```

**Required fields** (per spec): `site_name`, `review_text`, `rating`,
`language`, `sentiment`, `extracted_issues`.

---

## Issue categories

| Key | English | العربية |
|-----|---------|---------|
| cleanliness | Cleanliness | النظافة |
| parking | Parking | مواقف السيارات |
| safety | Safety | الأمان |
| tour_guides | Tour Guides | غياب المرشدين |
| pricing | Ticket Pricing | التذاكر والأسعار |
| services | Lack of Services | قلة الخدمات |
| crowding | Crowding | الزحام |
| accessibility | Accessibility | سهولة الوصول |

Edit categories and keywords in `src/config.py` (`ISSUE_CATEGORIES`).
