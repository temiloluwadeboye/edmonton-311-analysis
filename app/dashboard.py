"""Edmonton 311 dashboard.

Run from the project root:
    streamlit run app/dashboard.py

Reads the small summary files in app/data/ (built by src.build_dashboard_data).
The look (an Edmonton Transit line map) lives in app/transit.py.
"""

import json
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit runs this file directly, so make the project root importable (for src/ and app/)
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from app import transit as ets  # noqa: E402
from src.stats_test import chance_faster, effect_size_label, epsilon_squared, kruskal_wallis  # noqa: E402

DATA_DIR = ROOT / "app" / "data"
MIN_PER_WARD = 30      # wards with fewer closed requests than this are left out of the comparison
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

st.set_page_config(page_title="Edmonton 311", page_icon=str(ROOT / "app" / "static" / "route-bullet.png"),
                   layout="wide")
st.html(ets.CSS)


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

# Written by src.check_refresh after each successful weekly refresh
refreshed_on = None
refresh_path = DATA_DIR / "last_refresh.json"
if refresh_path.exists():
    refreshed_on = json.loads(refresh_path.read_text(encoding="utf-8")).get("refreshed_on")

st.html(ets.header(refreshed_on))
st.html(
    '<h1 class="ets-title">Where and how fast does the city respond?</h1>'
    '<p class="ets-lede">City of Edmonton 311 service requests (potholes, snow, litter, parking and more), '
    "analysed with an ETL pipeline, SQL and statistical tests. Figures cover 2022 to today unless noted.</p>"
)

app_share = channels.loc[channels["channel"] == "App", "closed_requests"].sum() / channels["closed_requests"].sum()
st.html(ets.headline_numbers([
    ("Requests since 2022", f"{int(since_2022['requests'].sum()):,}", "All 311 service requests"),
    ("Typical time to close", f"{statistics.median(ward_times['days_to_close']):.0f} days",
     "Median, closed requests, duplicates excluded"),
    ("Reported through the app", f"{app_share:.0%}", "Share of closed requests since 2022"),
]))

tab_wards, tab_reports, tab_map, tab_channels = st.tabs(
    ["Ward response times", "What gets reported", "Map", "App vs phone"])


# ---------------------------------------------------------------------------
# Tab 1: ward response times, with the statistical test for the chosen category
# ---------------------------------------------------------------------------

with tab_wards:
    counts = ward_times.groupby("category").size()
    eligible = counts[counts >= MIN_PER_WARD * 12].sort_values(ascending=False).index.tolist()
    pick_col, why_col = st.columns([2, 3], vertical_alignment="bottom")
    category = pick_col.selectbox("Category", eligible, label_visibility="collapsed",
                                  index=eligible.index("Potholes") if "Potholes" in eligible else 0)
    why_col.html('<p class="ets-note ets-note--tight">Pick a request category. Comparing one category at a time '
                 "keeps it fair: wards report different mixes of problems.</p>")

    rows = ward_times[ward_times["category"] == category]
    groups = {ward: g["days_to_close"].tolist() for ward, g in rows.groupby("ward") if len(g) >= MIN_PER_WARD}

    summary = pd.DataFrame(
        [(ward, len(t), statistics.median(t), np.percentile(t, 90)) for ward, t in groups.items()],
        columns=["ward", "closed_requests", "median_days", "p90_days"],
    ).sort_values(["median_days", "p90_days"])

    lines, st.session_state["ward_stops"], line_note = ets.transit_lines(
        summary, "ward", "median_days",
        lambda r: f"{r['ward']}: {r['closed_requests']:,} requests, 90% closed within {r['p90_days']:.0f} days",
        previous=st.session_state.get("ward_stops"),
    )
    # One block (heading, note, line) so Streamlit adds no gap between them; st.html strips inline SVG
    st.markdown(f'<div class="ets-section">{category}: median days to close</div>'
                f'<p class="ets-note">{line_note}</p>' + lines, unsafe_allow_html=True)

    if len(groups) >= 2:
        n = sum(len(t) for t in groups.values())
        h, p = kruskal_wallis(groups)
        eps2 = epsilon_squared(h, n)
        fastest, slowest = summary["ward"].iloc[0], summary["ward"].iloc[-1]
        _, prob = chance_faster(groups[fastest], groups[slowest])

        verdict = "are real, not chance" if p < 0.05 else "could be chance"
        verdict_col, figures_col = st.columns([1, 1], gap="large")
        verdict_col.html(
            '<div class="ets-section">What the test says</div>'
            f'<p class="ets-verdict">For <b>{category.lower()}</b>, the differences between wards '
            f"<b>{verdict}</b> (<span class='ets-nowrap'>p = {p:.1e}</span>), "
            f"and they are <b>{effect_size_label(eps2)}</b>: ward explains about {eps2:.0%} of the variation. "
            f"A request in <b>{fastest}</b> is closed before one in <b>{slowest}</b> {prob:.0%} of the time.</p>"
        )
        figures_col.html(
            '<div class="ets-figures ets-figures--side">'
            + ets.figure(f"{p:.1e}", "Kruskal-Wallis p-value", "Could the differences between wards be pure chance?")
            + ets.figure(f"{eps2:.3f}", f"Effect size (epsilon²): {effect_size_label(eps2)}",
                         "Share of the variation in response time explained by ward")
            + ets.figure(f"{prob:.0%}", f"{fastest} closes first, vs {slowest}",
                         "Chance a random request in the fastest ward is closed before one in the slowest "
                         "(50% = no difference)")
            + ets.figure(f"{n:,}", "Closed requests compared",
                         f"{len(groups)} wards with at least {MIN_PER_WARD} closed requests each")
            + "</div>"
        )


# ---------------------------------------------------------------------------
# Tab 2: what gets reported, and when
# ---------------------------------------------------------------------------

with tab_reports:
    top = (since_2022.groupby("category", as_index=False)["requests"].sum()
           .nlargest(10, "requests").sort_values("requests"))
    st.html('<div class="ets-section">Top 10 request categories since 2022</div>')
    fig = px.bar(top, x="requests", y="category", orientation="h", color_discrete_sequence=[ets.BLUE],
                 template=ets.TEMPLATE)
    fig.update_traces(marker_line_width=0, hovertemplate="%{y}: %{x:,} requests<extra></extra>")
    fig.update_layout(yaxis_title=None, xaxis_title="Requests", height=420, bargap=0.35)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(ets.style(fig), config=ets.figure_config(), theme=None)

    st.html('<div class="ets-section">Seasonal pattern</div>')
    default = ["Potholes", "Maintenance - Snow & Ice", "Encampments", "Litter"]
    options = top.sort_values("requests", ascending=False)["category"].tolist()
    picked = st.multiselect("Categories", options, default=[c for c in default if c in options])
    if picked:
        years = full_years["year"].nunique()
        seasonal = (full_years[full_years["category"].isin(picked)]
                    .groupby(["month", "category"], as_index=False)["requests"].sum())
        seasonal["requests_per_year"] = seasonal["requests"] / years
        fig = px.line(seasonal, x="month", y="requests_per_year", color="category", markers=True,
                      category_orders={"category": picked}, color_discrete_sequence=ets.SERIES,
                      template=ets.TEMPLATE)
        # Station dots: white centres with a ring in the line's colour
        fig.update_traces(line=dict(width=4), marker=dict(size=10, color="white", line=dict(width=3)))
        for trace in fig.data:
            trace.marker.line.color = trace.line.color
        fig.update_layout(xaxis=dict(tickmode="array", tickvals=list(range(1, 13)), ticktext=MONTHS),
                          xaxis_title=None, yaxis_title="Requests per month", height=430)
        st.html(f'<p class="ets-note">Average requests per month, full years '
                f"{full_years['year'].min()}-{full_years['year'].max()}</p>")
        st.plotly_chart(ets.style(fig), config=ets.figure_config(), theme=None)
        st.html('<p class="ets-note">Potholes peak in March with the freeze-thaw cycle; '
                "snow and ice requests disappear April to October.</p>")


# ---------------------------------------------------------------------------
# Tab 3: map by neighbourhood (one point per neighbourhood, never addresses)
# ---------------------------------------------------------------------------

with tab_map:
    shown = neighbourhoods.assign(median_label=neighbourhoods["median_days"].map(ets.day_label))
    fig = px.scatter_map(
        shown, lat="latitude", lon="longitude",
        size="requests", color="median_days",
        color_continuous_scale=[ets.GREEN, ets.AMBER, ets.RED],
        range_color=(0, neighbourhoods["median_days"].quantile(0.95)),
        custom_data=["neighbourhood", "requests", "median_label"],
        center={"lat": float(neighbourhoods["latitude"].median()), "lon": float(neighbourhoods["longitude"].median())},
        zoom=10, height=640, size_max=25, map_style="open-street-map", template=ets.TEMPLATE,
    )
    fig.update_traces(marker=dict(opacity=0.78),  # let the streets show between bubbles
                      hovertemplate=("<b>%{customdata[0]}</b><br>%{customdata[1]:,} requests since 2022"
                                     "<br>Median %{customdata[2]} to close<extra></extra>"))
    fig.update_layout(coloraxis_colorbar=dict(title="Median days", thickness=12, dtick=1),
                      margin=dict(l=0, r=0, t=0, b=0),
                      # dark, full-strength hover text (the default label was pale and hard to read)
                      hoverlabel=dict(bgcolor="white", bordercolor=ets.INK,
                                      font=dict(family=ets.FONT, size=14, color=ets.INK)))
    st.plotly_chart(fig, config=ets.figure_config(), theme=None)
    st.html('<p class="ets-note">Bubble size = requests since 2022 (closed, duplicates excluded). '
            "Colour = median days to close. Each bubble sits at the middle of its neighbourhood's requests.</p>")


# ---------------------------------------------------------------------------
# Tab 4: app vs phone
# ---------------------------------------------------------------------------

def channel_finding(category, rows):
    """One sentence comparing the fastest and slowest reporting channel, from the data on screen."""
    fast, slow = rows.iloc[0], rows.iloc[-1]
    name = category.lower()
    if slow["median_days"] - fast["median_days"] < 1:
        return (f"For <b>{name}</b>, the reporting channel makes little difference: reports close in a median of "
                f"<b>{ets.day_label(fast['median_days'])}</b> either way.")
    text = (f"For <b>{name}</b>, <b>{fast['channel'].lower()}</b> reports close in a median of "
            f"<b>{ets.day_label(fast['median_days'])}</b>, vs <b>{ets.day_label(slow['median_days'])}</b> for "
            f"{slow['channel'].lower()} reports.")
    if fast["channel"] == "App":
        text += " A likely reason: app reports include a photo and an exact location."
    return text


with tab_channels:
    both = channels.groupby("category")["channel"].nunique()
    options = channels[channels["category"].isin(both[both >= 2].index)] \
        .groupby("category")["closed_requests"].sum().sort_values(ascending=False).index.tolist()
    pick_col, why_col = st.columns([2, 3], vertical_alignment="bottom")
    category = pick_col.selectbox("Category ", options, label_visibility="collapsed",
                                  index=options.index("Potholes") if "Potholes" in options else 0)
    why_col.html('<p class="ets-note ets-note--tight">Pick a request category to compare reports made in the '
                 "311 app with reports made by phone.</p>")
    rows = channels[channels["category"] == category].sort_values("median_days")

    lines, st.session_state["channel_stops"], _ = ets.transit_lines(
        rows, "channel", "median_days",
        lambda r: f"{r['channel']}: {r['closed_requests']:,} requests, 90% closed within {r['p90_days']:.0f} days",
        previous=st.session_state.get("channel_stops"),
    )
    st.markdown(f'<div class="ets-section">{category}: median days to close by reporting channel</div>' + lines,
                unsafe_allow_html=True)
    finding_col, table_col = st.columns([1, 1], gap="large")
    with finding_col:
        st.html('<div class="ets-section">What it shows</div>'
                f'<p class="ets-verdict">{channel_finding(category, rows)}</p>')
    with table_col:
        st.dataframe(rows[["channel", "closed_requests", "median_days", "p90_days"]], hide_index=True,
                     column_config={"channel": "Channel",
                                    "closed_requests": st.column_config.NumberColumn("Closed requests", format="%,d"),
                                    "median_days": st.column_config.NumberColumn("Median days", format="%.0f"),
                                    "p90_days": st.column_config.NumberColumn("90% closed within (days)",
                                                                              format="%.0f")})


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
- **Design:** set in [Overpass](https://github.com/RedHatOfficial/Overpass) (SIL Open Font License);
  the line-map style is a nod to Edmonton Transit maps and is not affiliated with ETS.

Code: [github.com/temiloluwadeboye/edmonton-311-analysis](https://github.com/temiloluwadeboye/edmonton-311-analysis)
"""
    )
