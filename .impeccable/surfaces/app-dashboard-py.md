---
version: 1
slug: "app-dashboard-py"
primary_target: "app/dashboard.py"
related_targets: []
---

# Surface brief: Edmonton 311 dashboard (app/dashboard.py)

## Scope and mode
The live Streamlit dashboard at edmonton-311.streamlit.app. Mode: Operate (a reviewer reads findings and explores categories, wards, map and channels). Code-led build.

## Audience, task, constraints
Recruiters and hiring managers, one to two minutes, laptop or phone. Findings first and professional; must not look like a generic template; keep every current section, number and statistical test; must read well on a phone. Stays on Streamlit (theme, layout, injected CSS, Plotly templates).

## Direction contract
THESIS: Edmonton's service response drawn the way Edmontonians read their city, as a transit line. Refuses the default KPI-card-plus-chart-grid dashboard.
OWN-WORLD: White ground, near-black #1B1F24 header bar, ETS-style line colours as real data roles (blue #0057A8 primary series, red #D52B1E slowest/alert, green #00A651, amber #F2A900), thick round-capped strokes, white station dots with coloured rings, round route-bullet markers, Overpass (Highway Gothic lineage) throughout.
STORY: The reviewer sees three headline numbers, then the pothole ward comparison as one line with twelve stations, and understands that ward matters but only a little; they then explore categories, map and channels.
FIRST VIEWPORT: Dark header bar (Edmonton 311, data-last-updated). Section tabs as route bullets. Three headline numbers each led by a coloured round bullet. Below, the ward comparison line chart for the selected category with stations placed by median days, the slowest ward in red, effect size and sample size beneath.
FORM: Pick card, Edmonton Transit LRT line map; my position 1 on the ordered list; seed:6789bce3d6104bf4.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Signature interaction
Changing the category re-places the stations along the line (Plotly transition), so the comparison reads as the same line with different stops.

## Unresolved
Line metaphor is limited to the ward and channel comparisons; categories, seasonality and the map use the same palette and type, not the metaphor.
