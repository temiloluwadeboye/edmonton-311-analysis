"""Look and feel for the dashboard: an Edmonton Transit line map.

Response times are drawn as a vertical transit line (like the strip map inside an LRT car):
each stop is a median number of days, fastest at the top. Wards (or channels) that share a
median share one stop, drawn as a longer "interchange" pill with every name beside it.
"""

import html

import plotly.graph_objects as go
import plotly.io as pio

# Palette (also in .streamlit/config.toml). Colours are data roles, not decoration.
INK = "#1B1F24"      # text and the header bar
MUTED = "#4A525C"    # secondary text (7.9:1 on white)
HAIRLINE = "#D9DDE2"
PANEL = "#F3F5F7"
BLUE = "#0057A8"     # main series, route bullets
RED = "#D52B1E"      # slowest only
GREEN = "#00A651"    # fastest only
AMBER = "#F2A900"    # second series
VIOLET = "#6E3F98"   # third series
SLATE = "#5B6770"    # fourth series
SERIES = [BLUE, AMBER, VIOLET, SLATE]   # categories in a chart: never green or red, which mean fast and slow
FONT = "Overpass, sans-serif"

# Strip-map geometry, in pixels (the figure uses a 1 data unit = 1 pixel coordinate system)
STRIP_WIDTH = 380
LINE_X = 92          # where the line runs
LINE_WIDTH = 10
RING = 26            # station outer size
CORE = 17            # station white centre
PILL_STEP = 15       # each extra name at a stop lengthens the interchange pill by this much
NAME_LINE_PX = 17    # height of one name line
MIN_PX_PER_DAY = 44
EDGE_PAD = 6


pio.templates["ets"] = go.layout.Template(
    layout=dict(
        font=dict(family=FONT, color=INK, size=14),
        colorway=SERIES,
        paper_bgcolor="white",
        plot_bgcolor="white",
        hoverlabel=dict(font=dict(family=FONT, size=13), bgcolor="white", bordercolor=HAIRLINE),
        xaxis=dict(gridcolor=HAIRLINE, zeroline=False, linecolor=HAIRLINE, ticks="", automargin=True,
                   tickfont=dict(color=MUTED), title_font=dict(color=MUTED)),
        yaxis=dict(gridcolor=HAIRLINE, zeroline=False, linecolor=HAIRLINE, ticks="", automargin=True,
                   tickfont=dict(color=MUTED), title_font=dict(color=MUTED)),
        legend=dict(orientation="h", y=-0.18, x=0, title_text=""),
        margin=dict(l=8, r=8, t=12, b=8),
    )
)
pio.templates.default = "ets"
TEMPLATE = "ets"   # pass explicitly too: Streamlit resets Plotly's default template when it draws a chart


def day_label(days):
    days = float(days)
    text = f"{days:g}"
    return f"{text} day" if days == 1 else f"{text} days"


def transit_line(items, name_col, value_col, detail, previous=None):
    """A vertical transit line (inline SVG) with one stop per distinct value of `value_col`.

    items:    DataFrame with one row per ward/channel
    detail:   function(row) -> short tooltip text for that ward/channel
    previous: {name: y} from the last render, so each name slides from its old stop to its new one

    Returns (svg_html, positions) where positions is {name: y} for the next render.
    """
    stops = []
    for value, group in items.sort_values([value_col, name_col]).groupby(value_col, sort=True):
        stops.append((float(value), group))
    values = [v for v, _ in stops]
    previous = previous or {}

    # Space stops by their real day value, but make sure their name lists never collide
    px_per_day = MIN_PX_PER_DAY
    for (v1, g1), (v2, g2) in zip(stops, stops[1:]):
        needed = (len(g1) + len(g2)) / 2 * NAME_LINE_PX + 18
        px_per_day = max(px_per_day, needed / (v2 - v1))
    top = EDGE_PAD + len(stops[0][1]) * NAME_LINE_PX / 2
    bottom = EDGE_PAD + len(stops[-1][1]) * NAME_LINE_PX / 2
    height = round(top + (values[-1] - values[0]) * px_per_day + bottom)

    def y_of(value):
        return round(top + (value - values[0]) * px_per_day, 1)

    name_x = LINE_X + (max(len(g) for _, g in stops) - 1) * PILL_STEP + RING / 2 + 14
    parts = [f'<line class="ets-line" x1="{LINE_X}" y1="{y_of(values[0])}" x2="{LINE_X}" y2="{y_of(values[-1])}"/>']
    positions = {}
    for i, (value, group) in enumerate(stops):
        ring = _ring_colour(i, len(stops))
        y = y_of(value)
        names = [str(n) for n in group[name_col]]
        for name in names:
            positions[name] = y
        moved_from = [previous[n] for n in names if n in previous]
        station_dy = round(sum(moved_from) / len(moved_from) - y, 1) if moved_from else 0
        pill = (len(names) - 1) * PILL_STEP
        tip = html.escape(f"{day_label(value)} median: " + "; ".join(detail(r) for _, r in group.iterrows()))

        # Station: a ring with a white core; several names at one stop make a longer interchange pill
        parts.append(
            f'<g class="ets-move" style="--dy:{station_dy}px"><title>{tip}</title>'
            f'<rect x="{LINE_X - RING / 2}" y="{y - RING / 2}" width="{pill + RING}" height="{RING}" '
            f'rx="{RING / 2}" fill="{ring}"/>'
            f'<rect x="{LINE_X - CORE / 2}" y="{y - CORE / 2}" width="{pill + CORE}" height="{CORE}" '
            f'rx="{CORE / 2}" fill="white"/></g>'
        )
        parts.append(f'<text class="ets-stop{" ets-stop--slow" if ring == RED else ""}" x="{LINE_X - RING / 2 - 12}" '
                     f'y="{y}" text-anchor="end" dominant-baseline="central">{day_label(value)}</text>')
        for j, name in enumerate(names):
            ny = round(y + (j - (len(names) - 1) / 2) * NAME_LINE_PX, 1)
            dy = round(previous[name] - y, 1) if name in previous else 0
            parts.append(f'<text class="ets-name ets-move" style="--dy:{dy}px" x="{name_x}" '
                         f'y="{ny}" dominant-baseline="central">{html.escape(name)}</text>')

    label = "; ".join(f"{day_label(v)}: " + ", ".join(str(n) for n in g[name_col]) for v, g in stops)
    svg = (f'<svg class="ets-strip" viewBox="0 0 {STRIP_WIDTH} {height}" width="{STRIP_WIDTH}" role="img" '
           f'aria-label="{html.escape("Median days to close. " + label)}">' + "".join(parts) + "</svg>")
    return svg, positions


# Horizontal line (laptops and wider). Geometry in viewBox pixels; the SVG scales to its column.
H_WIDTH = 1000
H_MARGIN = 96         # room for a centred name list at each end
H_MIN_GAP = 46        # stations closer than this would touch
H_NAME_WIDTH = 168    # widest ward name, so lists on the same side never overlap
H_PILL_STEP = 7       # a shared stop grows a short pill toward its names
H_PILL_MAX = 36


def _ring_colour(i, n):
    """Green marks the fastest stop and red the slowest; every other stop is blue."""
    if n == 1:
        return BLUE
    if i == 0:
        return GREEN
    if i == n - 1:
        return RED
    return BLUE


def _horizontal_layout(values):
    """x for each stop: true to scale when the names fit, otherwise evenly spaced like a transit map.

    Names alternate below/above the line, so two lists on the same side are two stops apart.
    """
    span_px = H_WIDTH - 2 * H_MARGIN
    if len(values) == 1:
        return [H_WIDTH / 2], True
    lo, hi = values[0], values[-1]
    xs = [H_MARGIN + (v - lo) / (hi - lo) * span_px for v in values]
    fits = (all(b - a >= H_MIN_GAP for a, b in zip(xs, xs[1:]))
            and all(c - a >= H_NAME_WIDTH for a, c in zip(xs, xs[2:])))
    if fits:
        return xs, True
    step = span_px / (len(values) - 1)
    return [H_MARGIN + i * step for i in range(len(values))], False


def transit_line_horizontal(stops, name_col, detail, previous):
    """Left to right, fastest first. Returns (svg, {name: (x, y)}, true_to_scale)."""
    xs, to_scale = _horizontal_layout([v for v, _ in stops])
    below = [i % 2 == 0 for i in range(len(stops))]
    rows_below = max([len(g) for (_, g), b in zip(stops, below) if b] or [0])
    rows_above = max([len(g) for (_, g), b in zip(stops, below) if not b] or [0])

    def pill_of(k):
        return min((k - 1) * H_PILL_STEP, H_PILL_MAX)

    line_y = max(34, rows_above * NAME_LINE_PX + H_PILL_MAX + 30) if rows_above else 34
    height = round(line_y + max(34, rows_below * NAME_LINE_PX + H_PILL_MAX + 24))

    parts = [f'<line class="ets-line" x1="{xs[0]:.1f}" y1="{line_y}" x2="{xs[-1]:.1f}" y2="{line_y}"/>']
    positions = {}
    for i, ((value, group), x) in enumerate(zip(stops, xs)):
        ring = _ring_colour(i, len(stops))
        names = [str(n) for n in group[name_col]]
        k = len(names)
        down = below[i]
        pill = pill_of(k)
        tip = html.escape(f"{day_label(value)} median: " + "; ".join(detail(r) for _, r in group.iterrows()))
        moved = [previous[n] for n in names if n in previous]
        sdx = round(sum(p[0] for p in moved) / len(moved) - x, 1) if moved else 0

        # Station, or a shared stop's short pill growing toward its names
        y0 = line_y if down else line_y - pill
        parts.append(
            f'<g class="ets-move" style="--dx:{sdx}px"><title>{tip}</title>'
            f'<rect x="{x - RING / 2:.1f}" y="{y0 - RING / 2}" width="{RING}" height="{pill + RING}" '
            f'rx="{RING / 2}" fill="{ring}"/>'
            f'<rect x="{x - CORE / 2:.1f}" y="{y0 - CORE / 2}" width="{CORE}" height="{pill + CORE}" '
            f'rx="{CORE / 2}" fill="white"/></g>'
        )
        # Day label on the side away from the names
        label_y = line_y - RING / 2 - 10 if down else line_y + RING / 2 + 18
        slow = " ets-stop--slow" if ring == RED else ""
        parts.append(f'<text class="ets-stop{slow} ets-move" style="--dx:{sdx}px" x="{x:.1f}" y="{label_y}" '
                     f'text-anchor="middle">{day_label(value)}</text>')
        # Names stacked on the other side
        for j, name in enumerate(names):
            if down:
                ny = line_y + pill + RING / 2 + 20 + j * NAME_LINE_PX
            else:
                ny = line_y - pill - RING / 2 - 14 - (k - 1 - j) * NAME_LINE_PX
            px, py = previous.get(name, (x, ny))
            positions[name] = (round(x, 1), round(ny, 1))
            parts.append(f'<text class="ets-name ets-move" style="--dx:{round(px - x, 1)}px;--dy:{round(py - ny, 1)}px" '
                         f'x="{x:.1f}" y="{ny:.1f}" text-anchor="middle" dominant-baseline="central">'
                         f'{html.escape(name)}</text>')

    label = "; ".join(f"{day_label(v)}: " + ", ".join(str(n) for n in g[name_col]) for v, g in stops)
    svg = (f'<svg class="ets-strip ets-strip--h" viewBox="0 0 {H_WIDTH} {height}" role="img" '
           f'aria-label="{html.escape("Median days to close, fastest first. " + label)}">' + "".join(parts) + "</svg>")
    return svg, positions, to_scale


def transit_lines(items, name_col, value_col, detail, previous=None):
    """Both versions of the line: horizontal for laptops, vertical for phones (CSS shows one).

    Returns (html, positions, note); positions feeds the slide animation on the next render.
    """
    stops = [(float(v), g) for v, g in items.sort_values([value_col, name_col]).groupby(value_col, sort=True)]
    previous = previous or {}
    h_svg, h_pos, to_scale = transit_line_horizontal(stops, name_col, detail, previous.get("h", {}))
    v_svg, v_pos = transit_line(items, name_col, value_col, detail, previous.get("v"))
    if to_scale:
        note = "Fastest first, spaced by days. Ties share a stop."
    else:
        note = "Fastest first. Stops are evenly spaced here so every name fits: read the day labels. Ties share a stop."
    return f'<div class="ets-h">{h_svg}</div><div class="ets-v">{v_svg}</div>', {"h": h_pos, "v": v_pos}, note


def style(fig):
    """Set the ground and type on the figure itself, which Streamlit cannot override."""
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", font=dict(family=FONT, color=INK, size=14),
                      legend_title_text="")
    fig.update_xaxes(gridcolor=HAIRLINE, zeroline=False, linecolor=HAIRLINE)
    fig.update_yaxes(gridcolor=HAIRLINE, zeroline=False, linecolor=HAIRLINE)
    return fig


def figure_config():
    """Plotly toolbar off: these are read-only charts."""
    return {"displayModeBar": False, "responsive": True}


def header(updated_on):
    updated = f"Data last updated {html.escape(updated_on)}, refreshed automatically every week" if updated_on else ""
    return f"""
<div class="ets-header">
  <div class="ets-header__inner">
    <div class="ets-header__name">Edmonton 311</div>
    <div class="ets-header__updated">{updated}</div>
  </div>
</div>"""


def headline_numbers(items):
    """items: list of (label, value, note)"""
    cells = "".join(
        f"""<div class="ets-stat">
  <div class="ets-stat__label"><span class="ets-bullet"></span>{html.escape(label)}</div>
  <div class="ets-stat__value">{html.escape(value)}</div>
  <div class="ets-stat__note">{html.escape(note)}</div>
</div>"""
        for label, value, note in items
    )
    return f'<div class="ets-stats">{cells}</div>'


CSS = f"""
<style>
/* Streamlit chrome: our own header bar replaces the toolbar and the coloured top stripe */
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 0; max-width: 1180px; }}

::selection {{ background: {BLUE}; color: white; }}
:focus-visible {{ outline: 3px solid {BLUE}; outline-offset: 2px; }}

.ets-header {{ background: {INK}; color: white; margin: 0 calc(50% - 50vw) 22px; padding: 0 calc(50vw - 50%); }}
.ets-header__inner {{ display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between;
  gap: 6px 24px; padding: 14px 0 12px; }}
.ets-header__name {{ font: 800 1.35rem/1.1 {FONT}; letter-spacing: 0.01em; }}
.ets-header__name::before {{ content: ""; display: inline-block; width: 0.8em; height: 0.8em; margin-right: 0.45em;
  border-radius: 50%; background: white; box-shadow: 0 0 0 4px {BLUE}; vertical-align: -0.06em; }}
.ets-header__updated {{ font: 500 0.9rem/1.3 {FONT}; color: #C9CFD6; }}

.ets-title {{ font: 800 2rem/1.15 {FONT}; letter-spacing: -0.01em; margin: 0 0 8px; color: {INK};
  text-wrap: balance; max-width: 42ch; }}
.ets-lede {{ font: 400 1.05rem/1.55 {FONT}; color: {MUTED}; max-width: 68ch; margin: 0 0 18px; }}

.ets-stats {{ display: flex; flex-wrap: wrap; gap: 14px 48px; margin: 0 0 14px; }}
.ets-stat {{ min-width: 200px; }}
.ets-stat__label {{ font: 600 0.95rem/1.3 {FONT}; color: {MUTED}; display: flex; align-items: center; gap: 9px; }}
.ets-bullet {{ width: 14px; height: 14px; border-radius: 50%; flex: none; box-sizing: border-box;
  border: 4px solid {BLUE}; background: white; }}
.ets-stat__value {{ font: 800 2.2rem/1.1 {FONT}; color: {INK}; font-variant-numeric: tabular-nums;
  margin: 6px 0 2px 23px; }}
.ets-stat__note {{ font: 400 0.85rem/1.35 {FONT}; color: {MUTED}; margin-left: 23px; max-width: 32ch; }}

/* Section tabs as route bullets */
[role="tablist"] {{ gap: 30px; border-bottom: 1px solid {HAIRLINE}; flex-wrap: nowrap; overflow-x: auto;
  scrollbar-width: none; }}
[role="tablist"]::-webkit-scrollbar {{ display: none; }}
[role="tab"] {{ flex: none; white-space: nowrap; }}
[role="tab"] {{ padding: 10px 2px 12px; }}
[role="tab"] p {{ font: 600 1rem/1.2 {FONT}; color: {MUTED}; display: flex; align-items: center; }}
[role="tab"]:hover p {{ color: {INK}; }}
[role="tab"][aria-selected="true"] p {{ color: {INK}; font-weight: 800; }}
[role="tab"] p::before {{ content: ""; flex: none; width: 16px; height: 16px; box-sizing: border-box;
  margin-right: 10px; border-radius: 50%; border: 4px solid var(--bullet); background: white;
  transition: background-color 180ms ease-out; }}
[role="tab"][aria-selected="true"] p::before {{ background: var(--bullet); }}
[role="tab"] {{ --bullet: {BLUE}; }}
[role="tablist"] .react-aria-SelectionIndicator {{ background-color: {INK}; height: 4px; border-radius: 2px; }}

.ets-strip {{ display: block; width: 100%; max-width: {STRIP_WIDTH}px; height: auto; overflow: visible;
  margin: 4px 0 28px; }}
.ets-strip--h {{ max-width: 100%; margin: 12px 0 20px; }}
.ets-v {{ display: none; }}
@media (max-width: 640px) {{ .ets-h {{ display: none; }} .ets-v {{ display: block; }} }}
.ets-strip .ets-line {{ stroke: {BLUE}; stroke-width: {LINE_WIDTH}; stroke-linecap: round; }}
.ets-strip .ets-stop {{ font: 800 14px {FONT}; fill: {INK}; }}
.ets-strip .ets-stop--slow {{ fill: {RED}; }}
.ets-strip .ets-name {{ font: 500 15px {FONT}; fill: {INK}; }}
.ets-strip--h .ets-name {{ font-size: 16px; }}
.ets-strip--h .ets-stop {{ font-size: 15px; }}
.ets-strip .ets-move {{ animation: ets-slide 520ms cubic-bezier(0.16, 1, 0.3, 1) both; }}
@keyframes ets-slide {{ from {{ transform: translate(var(--dx, 0px), var(--dy, 0px)); }} to {{ transform: none; }} }}
@media (prefers-reduced-motion: reduce) {{ .ets-strip .ets-move {{ animation: none; }} }}

.ets-section {{ font: 800 1.3rem/1.25 {FONT}; color: {INK}; margin: 10px 0 4px; }}
.ets-note {{ font: 400 0.95rem/1.5 {FONT}; color: {MUTED}; max-width: 68ch; margin: 0 0 10px; }}

.ets-verdict {{ font: 500 1.15rem/1.5 {FONT}; color: {INK}; max-width: 46ch; margin: 4px 0 16px; }}
.ets-verdict b {{ font-weight: 800; }}
.ets-nowrap {{ white-space: nowrap; }}
.ets-figures--side {{ border-top: none; padding-top: 0; margin-top: 14px; }}
.ets-figures {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 28px;
  padding-top: 18px; border-top: 1px solid {HAIRLINE}; }}
.ets-figure__value {{ font: 800 1.6rem/1.1 {FONT}; color: {INK}; font-variant-numeric: tabular-nums; }}
.ets-figure__label {{ font: 700 0.9rem/1.3 {FONT}; color: {INK}; margin-top: 4px; }}
.ets-figure__note {{ font: 400 0.82rem/1.4 {FONT}; color: {MUTED}; margin-top: 2px; }}

[data-testid="stCaption"], [data-testid="stCaption"] * {{ color: {MUTED} !important; opacity: 1; }}
.ets-note--tight {{ margin: 6px 0 0; }}

/* Phones: headline numbers as one compact row */
@media (max-width: 480px) {{
  .ets-title {{ font-size: 1.7rem; }}
  .ets-stats {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
  .ets-stat {{ min-width: 0; }}
  .ets-stat__label {{ font-size: 0.82rem; align-items: flex-start; gap: 6px; }}
  .ets-bullet {{ width: 11px; height: 11px; border-width: 3px; margin-top: 2px; }}
  .ets-stat__value {{ font-size: 1.45rem; margin: 4px 0 2px; }}
  .ets-stat__note {{ font-size: 0.82rem; line-height: 1.3; margin-left: 0; }}
}}
a {{ text-underline-offset: 3px; }}
</style>
"""


def figure(value, label, note):
    return (f'<div class="ets-figure"><div class="ets-figure__value">{html.escape(value)}</div>'
            f'<div class="ets-figure__label">{html.escape(label)}</div>'
            f'<div class="ets-figure__note">{html.escape(note)}</div></div>')
