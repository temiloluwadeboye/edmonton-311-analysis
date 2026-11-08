# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Primary: recruiters and hiring managers for data science, data analyst and data engineering roles who click through from Temiloluwa Adeboye's CV or LinkedIn and give the dashboard one or two minutes. Their job is to judge quickly whether the candidate can turn real, messy public data into trustworthy answers.

## Product Purpose
A live portfolio dashboard over 1.25M+ City of Edmonton 311 service requests (2013 to present): what residents report most, when, and how quickly the City responds, with statistical tests that rerun for any request category. Success means a reviewer leaves knowing the candidate built an end-to-end pipeline (ETL, SQL, statistics, deployment, weekly automated refresh) and reads the findings correctly.

## Positioning
Real municipal data, refreshed weekly by an automated pipeline with a data-quality gate, analysed with rank-based tests and effect sizes rather than p-values alone, and with fair comparisons that control for each ward's different request mix.

## Operating Context
Opened from a CV, LinkedIn project entry or GitHub README link, usually on a laptop, sometimes on a phone. The reviewer may never open the code.

## Capabilities and Constraints
- Stays on Streamlit, hosted free on Streamlit Community Cloud (edmonton-311.streamlit.app). Styling is limited to Streamlit theming (.streamlit/config.toml), layout, and injected CSS.
- Reads small pre-aggregated parquet summaries in app/data/ (no street addresses or individual locations).
- Data refreshes weekly via GitHub Actions; the page shows "Data last updated".
- Existing sections: headline metrics, categories, seasonality, ward comparison with live Kruskal-Wallis / Mann-Whitney tests, neighbourhood map, reporting channels.

## Evidence on Hand
Findings documented in README.md (parking about a quarter of requests; potholes peak in March; duplicates double typical encampment response time; pothole medians 2 to 7 days by ward with a small effect, epsilon squared about 0.03; app reports close faster than phone). Data: City of Edmonton Open Data, 311 Explorer dataset ukww-xkmj, under the City's Open Data Terms of Use (credit, no implied endorsement).

## Product Principles
- Findings first: a reviewer should see the answer before the method.
- Honest numbers: show effect sizes and caveats; never overstate a difference.
- Privacy by design: neighbourhood-level only, never addresses.
- Show the engineering: the pipeline and automation are part of the story, not hidden.

## Accessibility & Inclusion
No product-specific requirement established beyond readable charts and text at laptop and phone widths.
