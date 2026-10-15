"""
End-to-end pipeline runner for "تراثنا بعيون زواره".

Runs the full pipeline in order:
    STEP 1  Collect reviews (Google Places API or offline mock corpus)
    STEP 2  Analyze sentiment + classify issues (LLM or offline bilingual engine)
    STEP 3  Launch the interactive Streamlit dashboard

Usage:
    python run_pipeline.py            # run STEP 1 + STEP 2, then start dashboard
    python run_pipeline.py --no-dash  # run STEP 1 + STEP 2 only
    python run_pipeline.py --dash-only  # skip pipeline, just start dashboard
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, SRC)

import config as C  # noqa: E402


def load_dotenv():
    """Minimal .env loader so keys set in a local .env file are picked up."""
    env_path = os.path.join(C.BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


def run_pipeline(per_site: int, force_mock: bool):
    load_dotenv()
    import analyze_reviews
    import collect_reviews
    collect_reviews.run(per_site=per_site, force_mock=force_mock)
    print()
    analyze_reviews.run()


def run_dashboard():
    print("\n" + "=" * 70)
    print("STEP 3: launching interactive dashboard...")
    print("=" * 70)
    app = os.path.join(SRC, "dashboard.py")
    subprocess.call([sys.executable, "-m", "streamlit", "run", app])


def main():
    C.force_utf8_output()
    parser = argparse.ArgumentParser(description="Run the heritage analytics pipeline.")
    parser.add_argument("--per-site", type=int, default=14)
    parser.add_argument("--force-mock", action="store_true",
                        help="Force the offline mock corpus (ignore API keys)")
    parser.add_argument("--dash-only", action="store_true", help="Only start the dashboard")
    parser.add_argument("--no-dash", action="store_true", help="Run pipeline without dashboard")
    args = parser.parse_args()

    if not args.dash_only:
        run_pipeline(args.per_site, args.force_mock)

    if not args.no_dash:
        run_dashboard()


if __name__ == "__main__":
    main()
