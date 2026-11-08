---
name: Edmonton 311
description: City service response drawn as an Edmonton Transit line map.
colors:
  route-blue: "#0057A8"
  terminus-red: "#D52B1E"
  express-green: "#00A651"
  signal-amber: "#F2A900"
  line-violet: "#6E3F98"
  line-slate: "#5B6770"
  header-ink: "#1B1F24"
  muted-ink: "#4A525C"
  header-muted: "#C9CFD6"
  hairline: "#D9DDE2"
  platform-panel: "#F3F5F7"
  ground-white: "#FFFFFF"
typography:
  display:
    fontFamily: "Overpass, sans-serif"
    fontSize: "2rem"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Overpass, sans-serif"
    fontSize: "2.2rem"
    fontWeight: 800
    lineHeight: 1.1
    fontFeature: "tnum"
  title:
    fontFamily: "Overpass, sans-serif"
    fontSize: "1.3rem"
    fontWeight: 800
    lineHeight: 1.25
  verdict:
    fontFamily: "Overpass, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 500
    lineHeight: 1.5
  body:
    fontFamily: "Overpass, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 400
    lineHeight: 1.55
  note:
    fontFamily: "Overpass, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Overpass, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 600
    lineHeight: 1.3
  station-name:
    fontFamily: "Overpass, sans-serif"
    fontSize: "15px"
    fontWeight: 500
  station-stop:
    fontFamily: "Overpass, sans-serif"
    fontSize: "14px"
    fontWeight: 800
rounded:
  indicator: "2px"
  base: "0.75rem"
  full: "9999px"
spacing:
  xs: "6px"
  sm: "12px"
  md: "18px"
  lg: "28px"
  xl: "48px"
components:
  header-bar:
    backgroundColor: "{colors.header-ink}"
    textColor: "{colors.ground-white}"
    padding: "14px 0 12px"
  route-bullet:
    backgroundColor: "{colors.ground-white}"
    rounded: "{rounded.full}"
    size: "14px"
  tab:
    textColor: "{colors.muted-ink}"
    typography: "{typography.label}"
    padding: "10px 2px 12px"
  tab-selected:
    textColor: "{colors.header-ink}"
  station:
    backgroundColor: "{colors.route-blue}"
    rounded: "{rounded.full}"
    size: "26px"
  headline-number:
    textColor: "{colors.header-ink}"
    typography: "{typography.headline}"
---

# Design System: Edmonton 311

## Overview

**Creative North Star: "The LRT Strip Map"**

The page reads like the line map above the doors of an Edmonton LRT car: a white ground, a near-black header bar, thick round-capped blue line, white station cores inside coloured rings, and route-bullet markers. The metaphor is functional, not decorative. Response times are stops on a line; ties are interchanges; the fastest and slowest ends are the termini, and only they get their own colours.

Density is calm and editorial: one finding per block, generous whitespace, notes in muted ink at a readable measure. Everything is set in one self-hosted family, Overpass, whose Highway Gothic lineage carries the signage voice. Charts that are not transit lines (categories, seasonality) share the palette and type but not the line metaphor. The neighbourhood map stays a familiar, detailed street map (OpenStreetMap) with bubbles on top.

The world rejects the default KPI-card-plus-chart-grid dashboard: no boxed metric cards, no shadowed tiles, no Streamlit chrome (toolbar, decoration stripe and default header are hidden).

**Key Characteristics:**
- Colour is a data role, never decoration.
- One type family, Overpass, with tabular numerals on every figure.
- Round geometry: rings, pills, round line caps, route bullets.
- Flat white ground; hairlines, not shadows, separate content.
- One signature motion: stations slide to their new stop.

## Colors

A transit-authority palette: one dominant route blue, two reserved terminus colours, three supporting line colours, and cool neutrals.

### Primary
- **Route Blue** (`route-blue`): the main series and the line itself. Every route bullet (headline numbers, tabs, header mark), the transit-line stroke, single-series bars, middle stations, links, focus ring and text selection.

### Secondary
- **Express Green** (`express-green`): fastest only. The first (fastest) terminus of a transit line and the fast end of the map's continuous scale.
- **Terminus Red** (`terminus-red`): slowest only. The last (slowest) terminus, its day label, and the slow end of the map's continuous scale.

### Tertiary
- **Signal Amber** (`signal-amber`), **Line Violet** (`line-violet`), **Line Slate** (`line-slate`): second, third and fourth series in categorical charts, after Route Blue. Amber is also the midpoint of the map's fast-to-slow scale.

### Neutral
- **Header Ink** (`header-ink`): all primary text, headline numbers, the header bar ground, the tab selection indicator.
- **Muted Ink** (`muted-ink`): secondary text, notes, ledes, captions, axis ticks and titles, unselected tabs (7.9:1 on white).
- **Header Muted** (`header-muted`): the "data last updated" line on the dark header only.
- **Hairline** (`hairline`): gridlines, axis lines, tab-row rule, the rule above figure grids, hover-label borders.
- **Platform Panel** (`platform-panel`): Streamlit secondary background and dataframe headers.
- **Ground White** (`ground-white`): page and plot ground, station cores, unfilled bullets.

### Named Rules
**The Terminus Rule.** Green means fastest and red means slowest, and nothing else. A line with one stop uses blue at both ends. Never use green or red as a category colour.

**The Series Order Rule.** Categorical charts draw from blue, amber, violet, slate, in that order.

**The Blue Bullet Rule.** Every route bullet is Route Blue; bullets mark structure, not data values.

## Typography

**Display Font:** Overpass (self-hosted variable, 100-900, from `app/static/Overpass-Variable.ttf`), with sans-serif fallback
**Body Font:** Overpass
**Label/Mono Font:** Overpass (tabular numerals for figures)

**Character:** Highway-signage sans: heavy 800 for anything you would read from a platform, 400-500 for prose.

### Hierarchy
- **Display** (800, 2rem, 1.15; 1.7rem under 480px): the page question, balanced, max 42ch.
- **Headline** (800, 2.2rem, 1.1, tabular): the three headline numbers. Figure values below a verdict step down to 800 / 1.6rem.
- **Title** (800, 1.3rem, 1.25): section headings inside tabs. The header wordmark is 800 / 1.35rem.
- **Verdict** (500, 1.15rem, 1.5, max 46ch; bold runs at 800): the plain-language test result.
- **Body** (400, 1.05rem, 1.55, max 68ch): the lede.
- **Note** (400, 0.95rem, 1.5, muted, max 68ch): explanations and caveats. Stat and figure notes run 0.82-0.85rem, never below 0.82rem (about 13px).
- **Label** (600, 0.95rem, 1.3, muted): stat labels; tabs use 600 / 1rem, 800 when selected.
- **Transit line**: horizontal stop labels 800 / 15px and names 500 / 16px, centred on their stop; the phone (vertical) version uses 14px / 15px in one aligned signage column.

### Named Rules
**The One Family Rule.** Overpass everywhere, including Plotly figures (14px, hover labels 13px). No second face.

**The Tabular Figure Rule.** Every displayed number uses `font-variant-numeric: tabular-nums`.

## Layout

Content is capped at 1180px with Streamlit's wide layout; the header bar bleeds full width. Order is fixed: header bar, question and lede, headline numbers, route-bullet tabs, then one finding per tab with control and explanation side by side (2:3), the transit line full width, then verdict and figures side by side (1:1). The map runs full width. Headline numbers sit in a wrapping row (gaps 14px / 48px, min 200px each). Figure grids are two columns under a hairline. Spacing steps observed: 6, 12, 18, 28, 48px.

Under 480px: headline numbers become three equal columns (12px gap) with bullets shrunk to 11px and notes held at 0.82rem; the tab row stays one line and scrolls horizontally with the scrollbar hidden; the display line drops to 1.7rem.

## Elevation & Depth

Flat. There are no drop shadows. Depth comes from the dark header bar against the white ground and from hairline rules. The only `box-shadow` is a 4px spread ring (`0 0 0 4px` Route Blue) that draws the header's route-bullet mark; it is a stroke, not elevation.

**The Hairline Rule.** Separate with a 1px Hairline rule or whitespace, never a raised surface.

## Shapes

Round and signage-like: fully round bullets and stations, interchange pills with fully rounded ends, round line caps on a 10px line, and a 4px tab indicator with 2px radius. Streamlit widgets use a 0.75rem base radius and fully round buttons. No sharp-cornered cards; there are no cards.

## Components

### Header Bar
Near-black full-bleed band: the "Edmonton 311" wordmark (800) led by a white dot inside a Route Blue ring, and the muted "data last updated" line baseline-aligned on the right, wrapping on narrow screens.

### Route-Bullet Tabs
- **Style:** text tabs with a 16px ring (4px Route Blue border, white core) before the label; 30px gaps over a hairline rule.
- **States:** hover darkens text to Header Ink; selected fills the bullet, sets text to 800, and shows a 4px Header Ink indicator. Bullet fill transitions 180ms ease-out.
- **Mobile:** one non-wrapping, horizontally scrolling row.

### Headline Numbers
Label (bullet + muted 600 text), big tabular value, short muted note, all indented 23px to the bullet's text edge. No box, no border.

### Transit Line (signature)
Two inline SVGs rendered together through `st.markdown` (st.html strips SVG); CSS shows one.
- **Horizontal (wider than 640px):** a 1000-unit viewBox that scales to the full content width, fastest on the left. Stops are placed true to scale in days when every name fits; name lists alternate below and above the line so two lists on one side are two stops apart. When stops are too crowded for that (for example Sportsfields: 3, 4, 5, 5.5, 7 and 18.5 days), stops are evenly spaced like a schematic transit map and the note says so; every stop keeps its day label. The day label sits on the opposite side of the line from its names. A shared stop grows a short pill (7px per extra name, at most 36px) toward its names.
- **Vertical (640px and narrower):** 380px wide, fastest at the top, day labels left and names in one aligned column; spacing in days, stretched only to stop name lists colliding.
- Stations are a 26px ring around a 17px white core. Ring colour follows the Terminus Rule. Each station carries a `<title>` tooltip, and each SVG a full `aria-label`.
- **Motion:** when the category changes, each name and station slides from its previous position (kept in session state per orientation, per-element `--dx` / `--dy`) over 520ms `cubic-bezier(0.16, 1, 0.3, 1)`. Off under `prefers-reduced-motion`.

### Neighbourhood Map
A street map (Plotly `scatter_map`, OpenStreetMap basemap at zoom 10, 640px tall) with one bubble per neighbourhood at the middle of its requests, never an address. The OpenStreetMap style is used for its sharp roads, river valley, parks and place names; the paler CARTO styles made places hard to tell apart.
- Bubble size follows requests (max 25px) at 0.78 opacity so streets show between bubbles; colour is a continuous Express Green → Signal Amber → Terminus Red scale of median days (0 to the 95th percentile), with a whole-day colourbar.
- Hover labels are white with a Header Ink border and 14px ink text: neighbourhood, requests since 2022, and median days written out ("Median 4 days to close"). The default pale hover text is not used.

### Charts
A Plotly template named `ets`: white ground, Overpass 14px ink, hairline grids, no zero lines or ticks, muted tick and title text, horizontal legend below, toolbar off. Seasonal lines are 4px wide with white 10px markers ringed in the series colour, echoing stations.

### Focus and Selection
A 3px Route Blue outline at 2px offset on `:focus-visible`; `::selection` is Route Blue with white text. Links underline at a 3px offset.

## Do's and Don'ts

### Do:
- **Do** reserve Express Green for the fastest and Terminus Red for the slowest, including continuous fast-to-slow scales.
- **Do** colour chart categories in the order blue, amber, violet, slate.
- **Do** draw every route bullet in Route Blue: an outline ring for unselected, filled for selected.
- **Do** set every figure in Overpass with tabular numerals.
- **Do** keep notes at 0.82rem (about 13px) or larger, including on phones.
- **Do** honour `prefers-reduced-motion` for the station slide.

### Don't:
- **Don't** use green or red as a series or category colour.
- **Don't** put headline numbers or charts in boxed, shadowed KPI cards.
- **Don't** introduce a second typeface or fall back to a system display face.
- **Don't** show Streamlit's default toolbar, decoration stripe or header.
- **Don't** render the transit line with `st.html`; it strips inline SVG.
