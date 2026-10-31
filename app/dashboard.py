"""Edmonton 311 dashboard.

Run from the project root:
    streamlit run app/dashboard.py

Reads the small summary files in app/data/ (built by src.build_dashboard_data).
"""

import json
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit runs this file directly, so make the project root importable (for src/)
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from src.stats_test import chance_faster, effect_size_label, epsilon_squared, kruskal_wallis  # noqa: E402

DATA_DIR = ROOT / "app" / "data"
MIN_PER_WARD = 30      # wards with fewer closed requests than this are left out of the comparison
GREEN = "#1F9D55"

st.set_page_config(page_title="Edmonton 311", page_icon="🛠️", layout="wide")


# ---------------------------------------------------------------------------
# Data (cached: read once, then reused on every interaction)
# ---------------------------------------------------------------------------

@st.cache_data
def load(name):
    return pd.read_parquet(DATA_DIR / f"{name}.parquet")


monthly = load("monthly_counts")
ward_times = load("ward_times")
neighbourhoods = load("neighbourhoods")
channels = load("channel_times")

current_year = int(monthly["year"].max())
full_years = monthly[(monthly["year"] >= 2022) & (monthly["year"] < current_year)]
since_2022 = monthly[monthly["year"] >= 2022]


# ---------------------------------------------------------------------------
# Header and headline numbers
# ---------------------------------------------------------------------------

st.title("Edmonton 311: where and how fast does the city respond?")
st.write(
    "City of Edmonton 311 service requests (potholes, snow, litter, parking and more), "
    "analysed with an ETL pipeline, SQL and statistical tests. Figures cover 2022 to today unless noted."
)

# Written by src.check_refresh after each successful weekly refresh
refresh_path = DATA_DIR / "last_refresh.json"
if refresh_path.exists():
    refreshed_on = json.loads(refresh_path.read_text(encoding="utf-8")).get("refreshed_on")
    if refreshed_on:
        st.caption(f"Data last updated: {refreshed_on} (refreshed automatically every week)")

c1, c2, c3 = st.columns(3)
c1.metric("Requests since 2022", f"{int(since_2022['requests'].sum()):,}")
c2.metric("Typical time to close", f"{statistics.median(ward_times['days_to_close']):.0f} days",
          help="Median days from opening to closing, closed requests, duplicates excluded")
app_share = channels.loc[channels["channel"] == "App", "closed_requests"].sum() / channels["closed_requests"].sum()
c3.metric("Reported through the app", f"{app_share:.0%}", help="Share of closed requests since 2022")

tab1, tab2, tab3, tab4 = st.tabs(["What gets reported", "Ward response times", "Map", "App vs phone"])


# ---------------------------------------------------------------------------
# Tab 1: what gets reported, and when
# ---------------------------------------------------------------------------

with tab1:
    top = (since_2022.groupby("category", as_index=False)["requests"].sum()
           .nlargest(10, "requests").sort_values("requests"))
    fig = px.bar(top, x="requests", y="category", orientation="h",
                 title="Top 10 request categories since 2022", color_discrete_sequence=[GREEN])
    fig.update_layout(yaxis_title=None, xaxis_title="Requests")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Seasonal pattern")
    default = ["Potholes", "Maintenance - Snow & Ice", "Encampments", "Litter"]
    options = top.sort_values("requests", ascending=False)["category"].tolist()
    picked = st.multiselect("Categories", options, default=[c for c in default if c in options])
    if picked:
        years = full_years["year"].nunique()
        seasonal = (full_years[full_years["category"].isin(picked)]
                    .groupby(["month", "category"], as_index=False)["requests"].sum())
        seasonal["requests_per_year"] = seasonal["requests"] / years
        fig = px.line(seasonal, x="month", y="requests_per_year", color="category", markers=True,
                      title=f"Average requests per month (full years {full_years['year'].min()}-{full_years['year'].max()})")
        fig.update_layout(xaxis=dict(tickmode="array", tickvals=list(range(1, 13)),
                                     ticktext=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]),
                          xaxis_title=None, yaxis_title="Requests per month")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Potholes peak in March with the freeze-thaw cycle; snow and ice requests disappear April to October.")


# ---------------------------------------------------------------------------
# Tab 2: ward response times, with the statistical test for the chosen category
# ---------------------------------------------------------------------------

with tab2:
    counts = ward_times.groupby("category").size()
    eligible = counts[counts >= MIN_PER_WARD * 12].sort_values(ascending=False).index.tolist()
    category = st.selectbox("Category", eligible, index=eligible.index("Potholes") if "Potholes" in eligible else 0)
    st.caption("Comparing one category at a time keeps it fair: wards report different mixes of problems.")

    rows = ward_times[ward_times["category"] == category]
    groups = {ward: g["days_to_close"].tolist() for ward, g in rows.groupby("ward") if len(g) >= MIN_PER_WARD}

    summary = pd.DataFrame(
        [(ward, len(t), statistics.median(t), np.percentile(t, 90)) for ward, t in groups.items()],
        columns=["ward", "closed_requests", "median_days", "p90_days"],
    ).sort_values(["median_days", "p90_days"])

    fig = px.bar(summary.sort_values(["median_days", "p90_days"], ascending=False),
                 x="median_days", y="ward", orientation="h",
                 hover_data=["closed_requests", "p90_days"],
                 title=f"{category}: median days to close, by ward", color_discrete_sequence=[GREEN])
    fig.update_layout(yaxis_title=None, xaxis_title="Median days to close")
    st.plotly_chart(fig, use_container_width=True)

    if len(groups) >= 2:
        n = sum(len(t) for t in groups.values())
        h, p = kruskal_wallis(groups)
        eps2 = epsilon_squared(h, n)
        fastest, slowest = summary["ward"].iloc[0], summary["ward"].iloc[-1]
        _, prob = chance_faster(groups[fastest], groups[slowest])

        s1, s2, s3 = st.columns(3)
        s1.metric("Kruskal-Wallis p-value", f"{p:.1e}", help="Could the differences between wards be pure chance?")
        s2.metric("Effect size (epsilon²)", f"{eps2:.3f}", effect_size_label(eps2), delta_color="off",
                  help="Share of the variation in response time explained by ward")
        s3.metric(f"{fastest} closes first", f"{prob:.0%}", f"vs {slowest}", delta_color="off",
                  help="Chance a random request in the fastest ward is closed before one in the slowest (50% = no difference)")

        verdict = "are real, not chance" if p < 0.05 else "could be chance"
        st.info(
            f"For **{category.lower()}**, the differences between wards **{verdict}** "
            f"(p = {p:.1e}), and they are **{effect_size_label(eps2)}**: ward explains about {eps2:.0%} of the variation. "
            f"A request in **{fastest}** is closed before one in **{slowest}** {prob:.0%} of the time."
        )


# ---------------------------------------------------------------------------
# Tab 3: map by neighbourhood (one point per neighbourhood, never addresses)
# ---------------------------------------------------------------------------

with tab3:
    fig = px.scatter_map(
        neighbourhoods, lat="latitude", lon="longitude",
        size="requests", color="median_days",
        color_continuous_scale="RdYlGn_r", range_color=(0, neighbourhoods["median_days"].quantile(0.95)),
        hover_name="neighbourhood", hover_data={"requests": ":,", "median_days": True,
                                                "latitude": False, "longitude": False},
        center={"lat": float(neighbourhoods["latitude"].median()), "lon": float(neighbourhoods["longitude"].median())},
        zoom=9.5, height=600, size_max=25, map_style="open-street-map",
    )
    fig.update_layout(coloraxis_colorbar_title="Median days", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bubble size = requests since 2022 (closed, duplicates excluded). "
               "Colour = median days to close. Each bubble sits at the middle of its neighbourhood's requests.")


# ---------------------------------------------------------------------------
# Tab 4: app vs phone
# ---------------------------------------------------------------------------

with tab4:
    both = channels.groupby("category")["channel"].nunique()
    options = channels[channels["category"].isin(both[both >= 2].index)] \
        .groupby("category")["closed_requests"].sum().sort_values(ascending=False).index.tolist()
    category = st.selectbox("Category ", options, index=options.index("Potholes") if "Potholes" in options else 0)
    rows = channels[channels["category"] == category].sort_values("median_days")
    fig = px.bar(rows, x="channel", y="median_days", hover_data=["closed_requests", "p90_days"],
                 title=f"{category}: median days to close by reporting channel",
                 color_discrete_sequence=[GREEN])
    fig.update_layout(xaxis_title=None, yaxis_title="Median days to close")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(rows[["channel", "closed_requests", "median_days", "p90_days"]], hide_index=True)
    st.caption("For potholes, app reports close in a median of 4 days vs 7 by phone. A likely reason: app "
               "reports include a photo and exact location. Litter and snow show little difference.")


# ---------------------------------------------------------------------------
# Methods and caveats
# ---------------------------------------------------------------------------

with st.expander("Methods & caveats"):
    st.markdown(
        f"""
- **Data:** [311 Explorer](https://data.edmonton.ca/Indicators/311-Explorer/ukww-xkmj), City of Edmonton
  Open Data, publicly available under the
  [City of Edmonton Open Data Terms of Use](https://www.edmonton.ca/sites/default/files/public-files/assets/Web-version2.1-OpenDataAgreement.pdf).
  This project is independent and not affiliated with or endorsed by the City of Edmonton.
- **Response time** = days from a request being opened to being *closed*, which is not always the same as
  the problem being *fixed* (e.g. "Deferred - Future Work Planned" closes in about a day). Dates have no
  time of day, so the smallest unit is one day.
- **Duplicate reports are excluded** from response times: they close almost instantly and would make busy
  categories look faster (excluding them doubles the typical encampment response time).
- **Wards:** Edmonton redrew and renamed its wards in 2021, so ward comparisons use 2022 onwards only.
- **Statistics:** response times are heavily skewed, so the ward comparison uses rank-based tests
  (Kruskal-Wallis across all wards, Mann-Whitney U for fastest vs slowest) and reports effect sizes, because
  with tens of thousands of requests almost any difference is "statistically significant".
- {current_year} is a partial year and is left out of seasonal averages.

Code: [github.com/temiloluwadeboye/edmonton-311-analysis](https://github.com/temiloluwadeboye/edmonton-311-analysis)
"""
    )
