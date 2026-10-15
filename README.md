# تراثنا بعيون زواره - Our Heritage

An **AI-powered tourism analytics platform** for Iraqi historical and
archaeological sites. It transforms heritage-site management from slow,
reactive methods into **real-time, data-driven decision-making**
by turning visitor reviews (Arabic + English) into actionable insights on an
interactive map of Iraq.

> **الهدف:** تحويل إدارة المواقع الأثرية من أساليب تقليدية بطيئة إلى قرارات
> فورية واستباقية مبنية على البيانات، عبر تحليل آراء الزوار (بالعربية
> والإنجليزية) وعرضها على خريطة تفاعلية للعراق.

---

## What it does (3 core steps)

| Step                         | File                     | Description                                                                                                                                                                                                                                                      |
| ---------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Data Collection**       | `src/collect_reviews.py` | Gathers Google Maps reviews (AR/EN) via the **Google Places API**, or a built-in **bilingual mock corpus** offline. Stores clean structured data (JSON + CSV).                                                                                                   |
| **2. AI Sentiment Analysis** | `src/analyze_reviews.py` | Classifies each review's **sentiment** (Positive / Neutral / Negative) and **tags issues** (Cleanliness, Parking, Safety, Tour Guides, Pricing, Services, Crowding, Accessibility). Supports **Gemini / OpenAI** LLM or a built-in offline bilingual classifier. |
| **3. Interactive Dashboard** | `src/dashboard.py`       | A Streamlit app centered on an **interactive map of Iraq** with clickable site markers, satisfaction gauges, priority-ranked complaint bars, a filterable bilingual review feed, and an **automated Actionable Insights** panel.                                 |

---

## Project structure

```
culture_hackathon/
├── run_pipeline.py            # run this file to start
├── requirements.txt
├── .env.example               # Copy to .env and add API keys (all optional)
├── README.md
├── src/
│   ├── config.py              # Paths, bilingual issue taxonomy, API settings
│   ├── collect_reviews.py     # STEP 1 - data collection (Google Places / mock)
│   ├── mock_data.py           # Offline bilingual review corpus
│   ├── analyze_reviews.py     # STEP 2 - sentiment + issue classification (LLM/offline)
│   ├── insights.py            # Metrics + prioritized recommendations engine
│   └── dashboard.py           # STEP 3 - interactive Streamlit dashboard
└── data/
    ├── sites.json             # Heritage-site registry (names, AR/EN, coordinates)
    ├── reviews_raw.json       # STEP 1 output (collected reviews)
    ├── reviews_raw.csv        # CSV export of the same
    └── reviews_analyzed.json  # STEP 2 output (enriched with sentiment + issues)
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

That's it - with no API keys configured, the app automatically uses a rich
bilingual mock dataset so you can explore every feature immediately. The
dashboard opens in your browser (default http://localhost:8501).

### Run the steps individually

```bash
# STEP 1 - collect reviews (mock data when no key is set)
python src/collect_reviews.py --per-site 14

# STEP 2 - analyze sentiment + classify issues
python src/analyze_reviews.py

# STEP 3 - launch the dashboard
streamlit run src/dashboard.py
```

---

## Optional: enabling live data & LLM analysis

Everything works offline by default. To upgrade to **real data** and **LLM
reasoning**, copy `.env.example` to `.env` and fill in keys:

```bash
cp .env.example .env
```

| Variable                | Purpose                                     | Notes                                                             |
| ----------------------- | ------------------------------------------- | ----------------------------------------------------------------- |
| `GOOGLE_PLACES_API_KEY` | Fetch **live** Google Maps reviews (STEP 1) | Enables the Places Details API path.                              |
| `LLM_PROVIDER`          | `auto` \| `gemini` \| `openai`              | `auto` picks whichever key is present.                            |
| `GEMINI_API_KEY`        | Use **Gemini** for classification (STEP 2)  | `pip install google-generativeai` not required - called via REST. |
| `OPENAI_API_KEY`        | Use **OpenAI** for classification (STEP 2)  | Called via REST.                                                  |

> **Graceful fallback:** if a key is missing, an LLM call fails, or the network
> is unavailable, the pipeline automatically falls back to the built-in
> **bilingual rule-based classifier** - the app never breaks.

> **Google Places note:** the Place Details endpoint returns a maximum of
> **5 reviews per place**. For a production-scale scraper, integrate a service
> such as **Apify's Google Maps scraper** or a **Playwright/Selenium** pipeline
> and write results using the same normalized schema (see below).

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

## Dashboard features (STEP 3)

- **Interactive Map of Iraq**: color-coded, size-scaled markers for each
  heritage site (Hatra الحضر, Babylon بابل, Ur أور, Erbil Citadel قلعة أربيل,
  Samarra سامراء, Nimrud نمرود, Ctesiphon المدائن, Lagash لكش). Marker color
  = satisfaction %, size = review volume. Select a site from the sidebar.
- **Overall satisfaction gauge**: a big 0–100% indicator with a 70% target
  threshold line.
- **Sentiment split donut**: Positive / Neutral / Negative distribution.
- **Top recurring complaints**: priority-ranked horizontal bars per site
  (Cleanliness, Parking, Safety, Tour Guides, Pricing, Services, Crowding,
  Accessibility) colored by severity.
- **Filterable bilingual review feed**: recent Arabic & English comments with
  AI-assigned sentiment badges, star ratings, and issue tags; filter by site,
  language, and sentiment.
- **Actionable Insights panel**: automated, bilingual recommendations
  (العربية / English) highlighting the most critical issues requiring
  **immediate intervention**, each with a severity level and priority score.
- **Bilingual UI**: full Arabic (RTL-aware) and English toggle.

### Issue taxonomy

| Key             | English          | العربية          |
| --------------- | ---------------- | ---------------- |
| `cleanliness`   | Cleanliness      | النظافة          |
| `parking`       | Parking          | مواقف السيارات   |
| `safety`        | Safety           | الأمان           |
| `tour_guides`   | Tour Guides      | غياب المرشدين    |
| `pricing`       | Ticket Pricing   | التذاكر والأسعار |
| `services`      | Lack of Services | قلة الخدمات      |
| `crowding`      | Crowding         | الزحام           |
| `accessibility` | Accessibility    | سهولة الوصول     |

Add or edit categories and their bilingual keywords in `src/config.py`
(`ISSUE_CATEGORIES`); the classifier, dashboard, and insights update
automatically.

---

## Deployment

### Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) -> **New app**.
3. Set **Main file path** = `src/dashboard.py`.
4. Add any secrets (`GOOGLE_PLACES_API_KEY`, etc.) under **Settings -> Secrets**.
5. Deploy. (Commit the `data/reviews_analyzed.json` if you want live demo data
   to load without re-running the pipeline.)

### Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "src/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Other hosts

Works on Render, Railway, Heroku, Azure, or any host that can run a Python web
process. Use `streamlit run src/dashboard.py --server.port=$PORT`.
