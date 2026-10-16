"""
Streamlit dashboard: map of Iraq with site metrics, issue breakdowns, and a
filterable review feed.

Run:
    streamlit run src/dashboard.py
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config as C
import insights as I

st.set_page_config(
    page_title=f"{C.APP_TITLE_AR} | {C.APP_TITLE_EN}",
    page_icon="🇮🇶",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .main-title { font-size: 2.4rem; font-weight: 800; color:#0b3d2e;
        background: linear-gradient(90deg,#0b3d2e,#1b9e4b);
        -webkit-background-clip:text; -webkit-text-fill-color: transparent;
        margin-bottom:0; }
      .subtitle { color:#4a5568; font-size:1.05rem; margin-top:.25rem; }
      .metric-card { background:#fff; border:1px solid #e6e6e6; border-radius:14px;
        padding:16px 18px; box-shadow:0 2px 10px rgba(0,0,0,0.05); }
      .insight-card { border-radius:12px; padding:14px 16px; margin-bottom:10px;
        border:1px solid rgba(0,0,0,0.06); }
      .pill { display:inline-block; padding:2px 10px; border-radius:999px;
        font-size:.78rem; font-weight:600; margin-right:6px; }
      .arabic { direction: rtl; text-align: right; font-size:1.02rem; }
      .review-card { background:#fbfbfb; border:1px dashed #ddd; border-radius:10px;
        padding:10px 12px; margin-bottom:8px; }
      .stApp { background: #f6f8f7; }
      h1,h2,h3 { color:#0b3d2e; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_all():
    with io.open(C.SITES_FILE, encoding="utf-8") as fh:
        sites = json.load(fh)["sites"]

    if not os.path.exists(C.ANALYZED_FILE):
        import collect_reviews
        import analyze_reviews
        collect_reviews.run(per_site=14, force_mock=True)
        analyze_reviews.run(raw_path=C.RAW_REVIEWS_FILE, out_path=C.ANALYZED_FILE)

    with io.open(C.ANALYZED_FILE, encoding="utf-8") as fh:
        reviews = json.load(fh)
    return sites, reviews


def build_df(reviews):
    return pd.DataFrame(reviews)


def issue_label(key, lang="en"):
    return C.ISSUE_CATEGORIES[key].get(lang, C.ISSUE_CATEGORIES[key]["en"])


def sentiment_badge(sentiment, lang="en"):
    return C.SENTIMENT_LABELS[sentiment]


def make_iraq_map(sites, reviews):
    """Interactive map of Iraq with clickable, color-coded site markers."""
    rows = []
    for s in sites:
        m = I.site_metrics(reviews, s["id"])
        sat = m["satisfaction"]
        rows.append({
            "name_en": s["name_en"],
            "name_ar": s["name_ar"],
            "lat": s["lat"],
            "lon": s["lon"],
            "satisfaction": sat,
            "total": m["total"],
            "avg_rating": m["avg_rating"],
            "city_en": s["city_en"],
            "city_ar": s["city_ar"],
        })
    df = pd.DataFrame(rows)

    fig = go.Figure(go.Scattergeo(
        lon=df["lon"],
        lat=df["lat"],
        text=df.apply(
            lambda r: f"<b>{r['name_en']}</b> / {r['name_ar']}<br>"
                      f"Satisfaction: {r['satisfaction']}%<br>"
                      f"Avg rating: {r['avg_rating']}★<br>"
                      f"Reviews: {r['total']}", axis=1),
        mode="markers+text",
        marker=dict(
            size=(df["total"] / df["total"].max() * 22 + 12) if df["total"].max() else 14,
            color=df["satisfaction"],
            colorscale="RdYlGn",
            cmin=0, cmax=100,
            colorbar=dict(title=dict(text="Satisfaction %", side="right")),
            line=dict(width=1, color="#333"),
            symbol="circle",
        ),
        textposition="bottom center",
        textfont=dict(size=11, color="#0b3d2e"),
        hovertemplate="%{text}<extra></extra>",
        customdata=df["name_en"],
    ))
    fig.update_geos(
        visible=True, resolution=50, scope="asia",
        showcountries=True, countrycolor="#9aa0a6",
        showsubunits=True, subunitcolor="#c8ccd0",
        showland=True, landcolor="#eef1ee",
        lataxis=dict(range=[28.5, 37.8]),
        lonaxis=dict(range=[38.5, 48.8]),
        center=dict(lat=33.0, lon=43.5),
        projection=dict(type="mercator"),
    )
    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)",
        clickmode="event+select",
    )
    return fig, df


def make_gauge(value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        number={"suffix": "%", "font": {"size": 40}},
        delta={"reference": 70, "increasing": {"color": "#1b9e4b"},
               "decreasing": {"color": "#d93025"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": "#0b3d2e"},
            "bgcolor": "white",
            "steps": [
                {"range": [0, 35], "color": "#f8d7da"},
                {"range": [35, 60], "color": "#fff3cd"},
                {"range": [60, 85], "color": "#d1e7dd"},
                {"range": [85, 100], "color": "#a3e4b8"},
            ],
            "threshold": {"line": {"color": "red", "width": 4},
                          "thickness": 0.75, "value": 70},
        },
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=10),
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig



def make_issue_bars(prioritized, lang="en"):
    """Horizontal progress-style bars for prioritized issues."""
    if not prioritized:
        return None
    df = pd.DataFrame(prioritized).sort_values("score")
    label_col = df["ar"] if lang == "ar" else df["en"]
    colors = [I.SEVERITY_STYLE[s]["color"] for s in df["severity"]]
    fig = go.Figure(go.Bar(
        x=df["score"], y=label_col, orientation="h",
        marker=dict(color=colors),
        text=[f"{v}%  ({c} mentions)" for v, c in zip(df["frequency_pct"], df["count"])],
        textposition="auto",
        hovertemplate="<b>%{y}</b><br>Priority score: %{x}<extra></extra>",
    ))
    fig.update_layout(
        height=max(240, 60 * len(df)),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(range=[0, 100], title="Priority score"),
        yaxis=dict(title=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def make_sentiment_donut(counts, lang="en"):
    labels = [C.SENTIMENT_LABELS[k][lang] for k in ("positive", "neutral", "negative")]
    values = [counts[k] for k in ("positive", "neutral", "negative")]
    colors = [C.SENTIMENT_LABELS[k]["color"] for k in ("positive", "neutral", "negative")]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors),
        textinfo="label+percent",
        hovertemplate="%{label}: %{value} reviews<extra></extra>",
    ))
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                      showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
    return fig


def _top_issue_label(scope, lang):
    counts = I.issue_counts(scope)
    if not counts:
        return "-"
    top = max(counts.items(), key=lambda x: x[1])[0]
    return issue_label(top, lang)


# Main app
def main():
    lang = st.session_state.get("lang", "ar")

    # Header
    col_l, col_r = st.columns([4, 1])
    with col_l:
        st.markdown(f"<h1 class='main-title'>🇮🇶 {C.APP_TITLE_AR}</h1>", unsafe_allow_html=True)
        st.markdown(f"<div class='subtitle'>{C.APP_SUBTITLE_AR}<br>"
                    f"<span style='font-size:.9rem;color:#7a869a'>{C.APP_SUBTITLE_EN}</span></div>",
                    unsafe_allow_html=True)
    with col_r:
        st.write("")
        st.write("")
        if st.button("English / العربية", key="langbtn"):
            st.session_state["lang"] = "en" if lang == "ar" else "ar"
            st.rerun()
    lang = st.session_state.get("lang", "ar")

    sites, reviews = load_all()

    # Sidebar filters
    st.sidebar.markdown(f"## {'لوحة التحكم' if lang=='ar' else 'Dashboard'}")
    st.sidebar.markdown("---")

    site_options = [("__all__", "🇮🇶 كل المواقع" if lang == "ar" else "All sites")]
    for s in sites:
        nm = s["name_ar"] if lang == "ar" else s["name_en"]
        site_options.append((s["id"], f"{nm}"))
    site_choice = st.sidebar.selectbox(
        "الموقع / Site", site_options, format_func=lambda x: x[1])[0]

    lang_filter = st.sidebar.multiselect(
        "اللغة / Language", options=["ar", "en"],
        default=["ar", "en"],
        format_func=lambda x: "العربية" if x == "ar" else "English")

    sent_filter = st.sidebar.multiselect(
        "المشاعر / Sentiment", options=["positive", "neutral", "negative"],
        default=["positive", "neutral", "negative"],
        format_func=lambda x: C.SENTIMENT_LABELS[x]["ar"] if lang == "ar"
        else C.SENTIMENT_LABELS[x]["en"])

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"{'إجمالي المراجعات' if lang=='ar' else 'Total reviews'}: {len(reviews)}")

    # Filter reviews for the feed
    feed = reviews
    if site_choice != "__all__":
        feed = [r for r in feed if r["site_id"] == site_choice]
    if lang_filter:
        feed = [r for r in feed if r["language"] in lang_filter]
    if sent_filter:
        feed = [r for r in feed if r["sentiment"] in sent_filter]


    # KPI row
    scope = reviews if site_choice == "__all__" else [r for r in reviews if r["site_id"] == site_choice]
    overall_sat = I.satisfaction_pct(scope)
    total_reviews = len(scope)
    avg_rt = I.avg_rating(scope)
    sent_counts = I.sentiment_counts(scope)

    k1, k2, k3, k4 = st.columns(4)

    def kpi(col, label_ar, label_en, value, suffix="", color="#0b3d2e"):
        with col:
            st.markdown(
                f"<div class='metric-card'>"
                f"<div style='font-size:.85rem;color:#6b7280'>{label_ar}<br>"
                f"<span style='font-size:.72rem;color:#9ca3af'>{label_en}</span></div>"
                f"<div style='font-size:1.9rem;font-weight:800;color:{color}'>{value}{suffix}</div>"
                f"</div>", unsafe_allow_html=True)

    kpi(k1, "رضا الزوار العام", "Overall satisfaction", f"{overall_sat}", "%",
        "#1b9e4b" if overall_sat >= 60 else "#d93025")
    kpi(k2, "عدد المراجعات", "Total reviews", f"{total_reviews}")
    kpi(k3, "متوسط التقييم", "Average rating", f"{avg_rt}", "★", "#f0a30a")
    kpi(k4, "أكثر شكوى تكراراً", "Top recurring issue", _top_issue_label(scope, lang))

    st.markdown("")

    # Map + gauge
    st.markdown(f"### {'خريطة المواقع الأثرية في العراق' if lang=='ar' else 'Interactive Map of Iraqi Heritage Sites'}")
    st.caption("انقر على علامة الموقع لعرض تفاصيله / Click a marker (or use the sidebar) to inspect a site.")

    map_col, gauge_col = st.columns([2.4, 1])
    with map_col:
        fig, map_df = make_iraq_map(sites, reviews)
        st.plotly_chart(fig, width="stretch", key="iraq_map")
    with gauge_col:
        st.markdown(f"#### {'مؤشر الرضا' if lang=='ar' else 'Satisfaction gauge'}")
        st.plotly_chart(make_gauge(overall_sat), width="stretch")
        st.markdown(f"#### {'توزيع المشاعر' if lang=='ar' else 'Sentiment split'}")
        st.plotly_chart(make_sentiment_donut(sent_counts, lang), width="stretch")

    # Selected site detail: issue breakdown
    st.markdown("---")
    detail_id = site_choice if site_choice != "__all__" else "babylon"
    detail_site = next(s for s in sites if s["id"] == detail_id)
    name = detail_site["name_ar"] if lang == "ar" else detail_site["name_en"]
    st.markdown(f"### {'تحليل الموقع: ' if lang=='ar' else 'Site analysis: '}{name}")
    st.caption(detail_site["description_ar"] if lang == "ar" else detail_site["description_en"])

    prioritized = I.prioritized_issues(reviews, detail_id)
    bar_col, info_col = st.columns([2, 1])
    with bar_col:
        st.markdown(f"##### {'الشكاوى الأكثر تكراراً (حسب الأولوية)' if lang=='ar' else 'Top recurring complaints (by priority)'}")
        fig_bars = make_issue_bars(prioritized, lang)
        if fig_bars:
            st.plotly_chart(fig_bars, width="stretch")
        else:
            st.info("لا توجد شكاوى مصنّفة لهذا الموقع." if lang == "ar"
                    else "No tagged complaints for this site.")
    with info_col:
        m = I.site_metrics(reviews, detail_id)
        st.markdown(f"##### {'معلومات الموقع' if lang=='ar' else 'Site info'}")
        st.metric("الرضا / Satisfaction", f"{m['satisfaction']}%")
        st.metric("متوسط التقييم / Avg rating", f"{m['avg_rating']}★")
        st.metric("المراجعات / Reviews", m["total"])
        langc = m["languages"]
        st.caption(f"العربية: {langc['ar']} | English: {langc['en']}")
        # severity progress bars as text
        for it in prioritized[:5]:
            bar = "█" * int(round(it["score"] / 10)) + "░" * (10 - int(round(it["score"] / 10)))
            lbl = it["ar"] if lang == "ar" else it["en"]
            sev = I.SEVERITY_STYLE[it["severity"]]
            st.markdown(
                f"<div style='margin-top:6px'>{sev['emoji']} <b>{lbl}</b><br>"
                f"<span style='color:{sev['color']};font-family:monospace'>{bar}</span> "
                f"<span style='font-size:.8rem;color:#666'>{it['score']} · {it['severity']}</span></div>",
                unsafe_allow_html=True)


    # Actionable insights panel
    st.markdown("---")
    st.markdown(f"### {'توصيات للإدارة' if lang=='ar' else 'Site Recommendations'}")
    st.caption("توصيات لمعالجة المشكلات الأكثر تكراراً في المراجعات / "
               "Recommendations based on the most common review issues.")

    top_insights = I.generate_insights(reviews, detail_id, top_n=3)
    if not top_insights:
        st.success("لا توجد مشكلات مسجلة لهذا الموقع." if lang == "ar"
                   else "No issues detected for this site.")
    else:
        for rank, it in enumerate(top_insights, 1):
            sev = I.SEVERITY_STYLE[it["severity"]]
            lbl = it["ar"] if lang == "ar" else it["en"]
            rec = it["recommendation_ar"] if lang == "ar" else it["recommendation_en"]
            title_txt = ("أولوية #" if lang == "ar" else "Priority #")
            sev_txt = sev["ar"] if lang == "ar" else sev["en"]
            freq_txt = "ذُكر في" if lang == "ar" else "mentioned in"
            rev_txt = "مراجعة" if lang == "ar" else "reviews"
            color = sev["color"]
            emoji = sev["emoji"]
            stars_rating = it["count"]
            st.markdown(
                "<div class='insight-card' style='background:" + color + "15;border-left:5px solid " + color + "'>"
                "<div style='font-weight:800;color:" + color + "'>" + emoji + " " + title_txt + str(rank) + ": " + lbl + " "
                "<span class='pill' style='background:" + color + "22;color:" + color + "'>" + sev_txt + "</span></div>"
                "<div style='margin-top:4px'>" + rec + "</div>"
                "<div style='margin-top:6px;font-size:.82rem;color:#555'>" + freq_txt + " " + str(stars_rating) + " " + rev_txt +
                " (" + str(it["frequency_pct"]) + "%) · priority score " + str(it["score"]) + "</div></div>",
                unsafe_allow_html=True)
    # Filterable review feed
    st.markdown("---")
    st.markdown(f"### {'آخر مراجعات الزوار' if lang=='ar' else 'Recent Visitor Reviews'}")
    st.caption("مراجعات حديثة بالعربية والإنجليزية مع وسوم المشاعر / "
               "Recent Arabic & English comments with sentiment tags.")

    if not feed:
        st.warning("لا توجد مراجعات مطابقة للفلاتر." if lang == "ar"
                   else "No reviews match the current filters.")
    else:
        # sort by timestamp desc
        feed_sorted = sorted(feed, key=lambda r: r.get("timestamp", ""), reverse=True)
        show_n = st.slider("عدد المراجعات المعروضة / Reviews to show",
                           min_value=5, max_value=min(50, len(feed_sorted)),
                           value=min(10, len(feed_sorted)))
        for r in feed_sorted[:show_n]:
            sent = C.SENTIMENT_LABELS[r["sentiment"]]
            tags = " ".join(
                f"<span class='pill' style='background:#eef;color:#334'>{issue_label(k, 'en')}</span>"
                for k in r["extracted_issues"]) or "<span style='color:#999;font-size:.8rem'>-</span>"
            txt_cls = "arabic" if r["language"] == "ar" else ""
            site_lbl = r["site_name_ar"] if lang == "ar" else r["site_name"]
            lang_badge = "🇮🇶 AR" if r["language"] == "ar" else "🇬🇧 EN"
            st.markdown(
                f"<div class='review-card'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center'>"
                f"<span><b>{site_lbl}</b> · {lang_badge} · {'★'*r['rating']}{'☆'*(5-r['rating'])}</span>"
                f"<span style='color:{sent['color']};font-weight:700'>{sent['emoji']} {sent[lang]}</span>"
                f"</div>"
                f"<div class='{txt_cls}' style='margin:6px 0'>{r['review_text']}</div>"
                f"<div>{tags} <span style='float:right;font-size:.75rem;color:#999'>{r.get('timestamp','')}</span></div>"
                f"</div>",
                unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"{C.APP_TITLE_AR} · {C.APP_TITLE_EN} - heritage-site management.")


if __name__ == "__main__":
    main()

