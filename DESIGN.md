# AirSense — UI Design Specification

Complete specification of the interface: every page, section, component, button,
state, and copy string. Written so that (a) the frontend can be built from it
without further decisions, and (b) a UI mockup image can be generated from it.

**All numbers in this document are the real values produced by the actual
training run and API**, not illustrative placeholders. If you generate a mockup,
use these exact numbers — a mockup showing different figures than the deployed
app is worse than no mockup.

---

## 0. Product in one sentence

AirSense predicts the hyper-local NOx pollution peak **before it arrives** and
attaches a concrete recommended action, so air quality becomes something you plan
around instead of something you react to.

---

## 1. Page inventory

**One page. No routing, no navigation, no login, no second screen.**

| Page | Route | Purpose |
|---|---|---|
| Dashboard | `/` | The entire product. Nine stacked sections, scrolled top to bottom. |
| API docs | `/docs` | FastAPI's auto-generated Swagger UI. Free, not designed by us, not linked from the dashboard chrome but mentioned in the footer. |

There is deliberately **no** settings page, no profile, no sidebar, and no
hamburger menu. Adding them would imply functionality that does not exist.

---

## 2. Design system

### 2.1 Colour

Dark theme only. The app is a monitoring dashboard; dark reduces glare on a
projector and makes the risk colours pop.

| Token | Hex | Use |
|---|---|---|
| `bg-base` | `#0a0f1a` | Page background |
| `bg-card` | `#111827` | Card surfaces |
| `bg-card-raised` | `#1a2234` | Hovered / nested surfaces |
| `border-subtle` | `#1f2937` | 1px card borders, dividers |
| `text-primary` | `#f9fafb` | Headings, big numbers |
| `text-secondary` | `#9ca3af` | Labels, captions |
| `text-muted` | `#6b7280` | Footnotes, units, disclaimers |
| `accent` | `#38bdf8` | Brand cyan: logo mark, links, focus rings |
| `accent-dim` | `#0e7490` | Chart fills at low opacity |

**Risk band colours** — these are the only saturated colours on the page, so risk
reads instantly. They come from the API (`risk_hex`), never hardcoded in the UI.

| Band | NOx (ppb) | Hex | Swatch name |
|---|---|---|---|
| Low | `< 100` | `#22c55e` | green |
| Moderate | `100 – 200` | `#f59e0b` | amber |
| High | `200 – 300` | `#f97316` | orange |
| Severe | `> 300` | `#ef4444` | red |

> Bands are **project-defined operational thresholds for demonstration**. They are
> NOT official CPCB or WHO AQI categories and must never be labelled as such.
> This disclaimer appears in the UI, not only in this document.

### 2.2 Typography

System font stack — no webfont, because a webfont is a network dependency that
can fail during a live demo.

```css
font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
font-variant-numeric: tabular-nums;   /* numbers must not jitter when they update */
```

| Role | Size / weight | Notes |
|---|---|---|
| Hero NOx number | 72px / 800, tabular | 56px on mobile |
| Section heading | 20px / 700 | Preceded by a numbered accent bar |
| Card metric | 30px / 700, tabular | |
| Body | 14px / 400 | |
| Label (uppercase) | 11px / 600, `letter-spacing: 0.08em` | Section eyebrows, card labels |
| Caption / disclaimer | 12px / 400, `text-muted` | |

**Every number carries a unit.** `163.0 ppb`, never `163.0`. Units render at
0.5em, `text-muted`, with a leading hair space.

### 2.3 Spacing, radius, elevation

- Spacing scale: `4 / 8 / 12 / 16 / 24 / 32 / 48 / 64` px.
- Page container: `max-width: 1200px`, centred, `padding: 24px` (16px on mobile).
- Section vertical rhythm: `48px` between sections, `16px` after a section heading.
- Card radius `16px`; pill radius `9999px`; inner chip radius `8px`.
- Card border `1px solid #1f2937`. Shadow `0 1px 3px rgba(0,0,0,0.4)`.
- No glassmorphism, no gradient meshes, no decorative blur. It is an instrument panel.

### 2.4 Motion

- Card entry: fade + 4px rise, 200ms `ease-out`, staggered 40ms.
- Number updates: 400ms count-up on the hero figure only.
- The alert banner: 2s `ease-in-out` infinite pulse on its **border only** (never
  the text — pulsing text is unreadable).
- `@media (prefers-reduced-motion: reduce)` disables all of the above.

---

## 3. Global states

Every data-driven section must define all four. No section may ever render blank.

| State | Treatment |
|---|---|
| **Loading** | Skeleton block: `bg-card-raised`, 16px radius, 1.5s shimmer. Same height as the loaded content so the page does not jump. |
| **Loaded** | The real content. |
| **Error** | Inside the card: ⚠ icon, `text-secondary` message "Could not load <thing>.", and a **Retry** button (see §5.4). Never an empty card, never a raw stack trace. |
| **Empty** | Not reachable — the dataset is committed to the repo, so data always exists. If a chart somehow gets zero points, show the error state instead of an empty axis. |

---

## 4. Section-by-section specification

Rendered in this exact order.

---

### Section 1 — Header

**Layout:** full-width bar, sticky at top, `bg-base` at 80% opacity with
`backdrop-filter: blur(8px)`, `1px` bottom border `border-subtle`, height 64px.
Content constrained to the 1200px container. Left group and right group,
`justify-content: space-between`.

**Left group** (horizontal, 12px gap):
1. **Logo mark** — 28×28px rounded square, `accent` cyan, containing a white
   upward-trending line-chart glyph. No external image; inline SVG.
2. **Wordmark** — `AirSense`, 20px / 800, `text-primary`.
3. **Tagline** — `Forecasting the pollution peak before it arrives.` 13px,
   `text-secondary`. Hidden below 900px viewport width.

**Right group** (horizontal, 8px gap):
4. **Location badge** — pill, `bg-card`, 1px `border-subtle`, 12px text
   `text-secondary`. Content: a 6px `accent` dot + `Live demo · MAIT, Delhi`.
5. **Replay control** — see §5.1. This is the only interactive control in the header.

**Copy, verbatim:**
- Wordmark: `AirSense`
- Tagline: `Forecasting the pollution peak before it arrives.`
- Badge: `Live demo · MAIT, Delhi`

---

### Section 2 — Data-mode notice

A single full-width strip immediately below the header. **Not dismissible.** This
is the honesty disclosure and hiding it behind an interaction would defeat it.

**Layout:** `bg-card`, 1px `border-subtle`, radius 12px, padding 12px 16px,
horizontal, 10px gap, ⓘ icon in `accent`.

**Copy, verbatim:**

> `Historical dataset replay — not a live sensor feed.` *(13px, `text-primary`)*
> `UCI Air Quality Data Set (De Vito et al., 2008), 2000 hourly readings from 11 Mar – 23 Jun 2004. Forecasts are computed live by the model from data up to the selected hour only.` *(12px, `text-muted`)*

---

### Section 3 — Hero status card

**The screenshot that goes in the deck. Give it the most visual weight on the page.**

**Layout:** one card, full container width, padding 32px, radius 16px. A `4px`
left border in the current band's colour. Two columns at ≥768px
(`grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr)`), stacked below that.

**Left column:**
1. Eyebrow label: `CURRENT READING` (uppercase label style).
2. **Hero number row** — baseline-aligned: `163.0` at 72px/800 in the band
   colour, then ` ppb` at 24px `text-muted`.
3. **Band pill** — `bg` = band colour at 15% opacity, `1px` border of the band
   colour at 40%, text in the band colour, 13px/700, padding 6px 14px. Content: a
   filled 8px dot + band name, e.g. `Moderate`.
4. Timestamp: `Dataset time · 23 Jun 2004, 12:00` — 13px `text-secondary`. The
   words "Dataset time" are mandatory; writing just a time would imply "now".

**Right column — co-pollutant grid.** 2×3 grid (2×2 + 1 on mobile), 12px gap.
Each cell: `bg-card-raised`, radius 8px, padding 12px; label 11px `text-muted`
uppercase, value 18px/700 `text-primary` with its unit at 0.55em.

Exact cells and real current values:

| Label | Value | Unit |
|---|---|---|
| `NO₂` | 106.0 | ppb |
| `CO` | 2.2 | mg/m³ |
| `BENZENE` | 13.1 | µg/m³ |
| `TEMP` | 34.9 | °C |
| `HUMIDITY` | 20.5 | % |
| `HOUR` | 12:00 | — |

**Full-width footer inside the card** — the recommended action. Separated by a
1px `border-subtle` top rule, 20px padding-top, 20px margin-top.
- Label: `RECOMMENDED ACTION NOW` (uppercase label, `text-muted`).
- Text: 16px `text-primary`, e.g.
  `Prefer indoor activity for sensitive individuals. Monitor.`
- Below it, 11px `text-muted`:
  `Project-defined operational bands for demonstration — not official CPCB/WHO standards.`

---

### Section 4 — Forecast strip

**Heading:** numbered accent bar + `6-hour forecast` + right-aligned 12px
`text-muted`: `Issued from 23 Jun 2004, 06:00`.

#### 4a. Alert banner (conditional)

Rendered **above** the cards, only when any of the next 6 hours is High or Severe
(API: `forecast.alert != null`). This element is the product thesis in one piece
of UI — make it unmissable.

**Layout:** full width, `bg` = alert band colour at 12% opacity, `1.5px` border in
the band colour (pulsing), radius 12px, padding 16px 20px. Horizontal: a 20px
warning triangle in the band colour, then a text stack, then the peak chip
right-aligned.

**Copy (values from the API, `{n}` = `alert.hours_ahead`):**
- Line 1, 18px/700 `text-primary`: `Peak predicted in 2 hours — act now.`
  - Singular form when `n == 1`: `Peak predicted in 1 hour — act now.`
- Line 2, 13px `text-secondary`:
  `Forecast reaches 239.7 ppb (High) at 08:00. Increase ventilation/filtration indoors. Move outdoor sessions indoors.`
- Right chip: `bg-card`, radius 8px, padding 8px 12px. Label `6H PEAK` 10px
  `text-muted` over `256.0 ppb` 18px/700 in the band colour.

**When `alert == null`** the banner is replaced by a calm equivalent — same
geometry, green, so the layout does not shift:
- `No High or Severe hours in the next 6 hours.`
- `Forecast peaks at 199.9 ppb (Moderate) at 18:00.`

#### 4b. The six cards

`display: grid`, `grid-template-columns: repeat(6, 1fr)`, 12px gap. Breakpoints:
6 across ≥1024px, 3 across 640–1023px, 2 across <640px. **Never a horizontal
scroller** — judges may be on a phone.

Each card: `bg-card`, 1px `border-subtle`, radius 12px, padding 14px, and a **4px
colour bar** flush across the top in that hour's band colour.

Contents, top to bottom:
1. Offset chip: `t+1` … `t+6`, 11px/700, `text-muted`, `bg-card-raised`, radius
   9999px, padding 2px 8px.
2. Clock time: `07:00`, 12px `text-secondary`.
3. Predicted value: `184.0` 30px/700 tabular in the band colour + ` ppb` at 0.5em
   `text-muted`.
4. Band name: 12px/600 in the band colour.
5. **Confidence footnote** — 10px `text-muted`. On the `t+1` card: `measured
   inputs`. On `t+2`…`t+6`: `model-fed inputs`. This is driven by the API's
   `inputs_measured` flag and is how the UI admits that error compounds with
   horizon.

**Real values at the demo replay position (`as_of=2004-06-23T06:00`):**

| Card | Time | Predicted | Band | Footnote |
|---|---|---|---|---|
| t+1 | 07:00 | 184.0 ppb | Moderate | measured inputs |
| t+2 | 08:00 | 239.7 ppb | High | model-fed inputs |
| t+3 | 09:00 | 256.0 ppb | High | model-fed inputs |
| t+4 | 10:00 | 239.9 ppb | High | model-fed inputs |
| t+5 | 11:00 | 234.7 ppb | High | model-fed inputs |
| t+6 | 12:00 | 235.0 ppb | High | model-fed inputs |

**Assumption caption** below the grid, 11px `text-muted`, full width:
`Recursive multi-step forecast · exogenous features held constant. Temperature, humidity and co-pollutants are held at their last observed values; from t+2 the NOx lags are fed by the model's own predictions, so uncertainty grows with the horizon.`

---

### Section 5 — History + forecast chart

**Heading:** `Recent history and forecast` + right-aligned legend.

**Legend** (12px `text-secondary`, 16px gap between items):
- 12px solid `accent` line swatch + `Measured (last 48 h)`
- 12px dashed `accent` line swatch + `Forecast (next 6 h)`

**Chart:** Chart.js line chart. Container height 340px desktop / 260px mobile.

- **X axis** — hourly timestamps. Label: `Time (hourly)`. Ticks `HH:00`, with the
  date shown at midnight crossings. `maxTicksLimit: 12`, no rotation.
- **Y axis** — label `NOx (ppb)`, begins at zero, grid `#1f2937` at 60% opacity.
- **Series 1 — measured:** solid `#38bdf8`, 2px, no point markers except the final
  one (4px filled), `tension: 0.3`.
- **Series 2 — forecast:** dashed `[6,4]`, 2px, same cyan at 90%, 3px point
  markers, `tension: 0.3`. **Starts at the last measured point** so the two lines
  visibly join rather than floating apart.
- **Risk bands as horizontal background zones**, drawn behind the data at 8%
  opacity of each band colour: 0–100 green, 100–200 amber, 200–300 orange,
  300+ red. Each labelled at the right edge, 10px, band colour at 70%.
- **Vertical "now" divider** at the last measured timestamp: 1px dashed
  `#6b7280`, with the rotated label `now` above the plot area.
- **Tooltip:** dark `#1a2234` card, 1px `border-subtle`, showing
  `23 Jun 2004, 08:00` then `239.7 ppb · High` then `Forecast` or `Measured`.
- **Interaction:** `mode: 'index'`, `intersect: false`. No zoom, no pan, no
  brushing — nothing that can be accidentally triggered during a live demo.

---

### Section 6 — Daily profile chart

**Heading:** `Daily pollution cycle` + right-aligned 12px `text-muted`:
`Mean of 2000 hourly readings · 83.3 days`.

**Chart:** Chart.js bar chart, 24 bars, one per hour-of-day. Height 280px.

- X axis label `Hour of day (0–23)`, ticks every 2 hours.
- Y axis label `Mean NOx (ppb)`.
- **Bar colours:** each bar coloured by the band its own mean falls into, at 85%
  opacity. Bars in the **18:00–21:00 evening window** get a 2px `#f97316`
  top border and full opacity so the window reads as highlighted.
- An annotation bracket spans hours 18–21 above the bars, labelled
  `6–9 PM traffic window`, 11px `#f97316`.

**Real bar values (ppb), hour 0 → 23:**
`95.9, 69.6, 48.3, 48.5, 35.3, 46.0, 83.5, 175.4, 219.7, 210.8, 179.3, 153.6,
135.2, 128.5, 122.5, 125.4, 128.8, 152.4, 175.9, 198.4, 187.8, 138.3, 111.6, 111.1`

**Caption below the chart** — the core insight, computed live, **never hardcoded**:

> `Evening peak averages 3.3x overnight levels (175.1 ppb in 18:00–21:00 vs 53.3 ppb in 03:00–06:00).` *(14px `text-primary`)*
> `Pollution is not random — it is a predictable daily cycle tracking traffic. That predictability is what makes forecasting viable.` *(12px `text-muted`)*

---

### Section 7 — Model validation card

**This is the differentiator. Give it real visual weight — border in `accent`, not
`border-subtle`.**

**Heading:** `Model validation` + a pill on the right: `bg` green at 15%, text
`#22c55e`, 12px/700, content `Beats baseline`. (Driven by `metrics.beats_baseline`
— if it were ever false the pill must read `Does not beat baseline` in red. Do not
suppress it.)

**Layout:** card, padding 24px. A 4-up metric grid (2-up on mobile), 16px gap,
then a comparison bar, then the footnote block.

**Metric tiles** — each `bg-card-raised`, radius 12px, padding 16px: 11px
`text-muted` uppercase label, 30px/700 tabular value, 11px `text-muted` sublabel.

| Label | Value | Sublabel |
|---|---|---|
| `TEST MAE` | `25.92 ppb` | `our model` |
| `BASELINE MAE` | `34.94 ppb` | `persistence` |
| `IMPROVEMENT` | `25.8 %` | `lower error vs baseline` — value in `#22c55e` |
| `R²` | `0.801` | `on held-out test set` |

**Comparison bar** — two stacked horizontal bars sharing one scale, making the
improvement visible rather than merely stated:
- Row 1: label `AirSense`, bar width ∝ 25.92, fill `accent`, value `25.92 ppb`.
- Row 2: label `Persistence`, bar width ∝ 34.94, fill `#6b7280`, value `34.94 ppb`.
- Bar height 10px, radius 9999px, track `bg-card-raised`.
- Caption: `Mean absolute error — lower is better.`

**Footnote block**, 1px top rule, 16px padding-top, 12px `text-secondary`, one
line each:
- `Chronological train/test split — no future data leaked into training.`
- `Train: 1580 rows · 12 Mar 2004 18:00 → 2 Jun 2004 22:00`
- `Test: 396 rows · 2 Jun 2004 23:00 → 23 Jun 2004 12:00`
- `Baseline "persistence" predicts next hour = current hour — the honest naive benchmark.`
- `Co-pollutants and weather lagged 1 h, so every feature was knowable before the predicted hour.`

---

### Section 8 — Feature importance

**Heading:** `What the model relies on`.

**Chart:** horizontal bar chart, 13 rows (all features), height 320px. Bars in
`accent`, descending. Value labels to the right of each bar as percentages, 11px
`text-secondary`. Y-axis tick labels use the raw feature names in `ui-monospace`,
12px — they are the actual column names and dressing them up would obscure what
the model really consumes.

**Real values:**

| Feature | Importance |
|---|---|
| `nox_lag_1` | 0.6106 |
| `benzene_lag_1` | 0.1194 |
| `hour_sin` | 0.0679 |
| `hour_cos` | 0.0472 |
| `nox_lag_3` | 0.0297 |
| `nox_lag_24` | 0.0226 |
| `nox_roll_24` | 0.0214 |
| `temp_lag_1` | 0.0198 |
| `no2_lag_1` | 0.0187 |
| `nox_lag_2` | 0.0152 |
| `humidity_lag_1` | 0.0124 |
| `co_lag_1` | 0.0084 |
| `nox_roll_3` | 0.0067 |

**Caption:** `Recent NOx and hour-of-day dominate — consistent with a traffic-driven daily cycle. Every input is lagged by at least one hour.`

---

### Section 9 — Campus zones

**Heading:** `Campus zones` + a **warning pill** on the right, not a subtle one:
`bg` amber at 15%, 1px amber border, text `#f59e0b`, 12px/700, content
`⚠ Simulated`.

**Mandatory disclosure strip** directly under the heading, before the cards.
`bg` amber at 8%, 1px amber at 25%, radius 8px, padding 10px 14px, 12px
`text-secondary`:

> `simulated zone offset — single sensor stream.` *(in `#f59e0b`, 600 weight)*
> `We have one sensor, not four. Each zone applies a fixed documented multiplier to the one real measured value (163.0 ppb) to demonstrate the multi-zone design. These are not four independent sensors.`

**Cards:** 4-up grid (2-up mobile), 12px gap. Each `bg-card`, 1px `border-subtle`,
radius 12px, padding 16px, with a 3px left border in its band colour:
1. Zone name, 15px/700 `text-primary`.
2. Value, 24px/700 tabular in band colour + ` ppb`.
3. Band name, 12px/600 band colour.
4. Multiplier chip: `bg-card-raised`, radius 9999px, 10px `text-muted`, e.g. `×1.25`.
5. Rationale, 11px `text-muted`.
6. A small `simulated` tag, 10px, amber at 70% — **on every card**, not only in
   the section header.

**Real values (derived from measured 163.0 ppb):**

| Zone | Value | Band | Multiplier | Rationale |
|---|---|---|---|---|
| Main Gate | 203.8 ppb | High | ×1.25 | Directly traffic-exposed — vehicle queue at entry |
| Parking Block | 187.4 ppb | Moderate | ×1.15 | Cold starts and idling vehicles |
| Central Lawn | 146.7 ppb | Moderate | ×0.90 | Open ground, set back from the road |
| Library Block | 130.4 ppb | Moderate | ×0.80 | Sheltered, furthest from the carriageway |

---

### Section 10 — Footer

1px top border, 32px padding, 12px `text-secondary`, three stacked blocks 12px apart.

**Block 1 — How it works.** A horizontal chevron flow, wrapping on mobile. Each
step a `bg-card` chip, radius 8px, padding 6px 12px, separated by `›` in
`text-muted`:
`Data › Cleaning › Features › Model › Forecast › Action`

**Block 2 — Credits.**
- `Data source: UCI Air Quality Data Set — De Vito et al. (2008), multi-sensor device readings.`
- `Built by Amaan Khan and Srishti Rathi · MAIT, Delhi`
- `Python · scikit-learn · FastAPI · Chart.js · Google Cloud Run`

**Block 3 — Honesty notes.** 11px `text-muted`, a real bulleted list:
- `Single sensor stream — the four campus zones are simulated offsets, labelled as such.`
- `Historical dataset (2004), not a live feed.`
- `Exogenous features held constant in the recursive forecast.`
- `Risk bands are project-defined for demonstration, not official CPCB/WHO standards.`
- `Lag features are positional; 63 of 2000 intervals are not exactly one hour.`
- `Cleaning found 0 sentinel values — this source file was already cleaned upstream.`

Right-aligned link, `accent`: `API docs` → `/docs`.

---

## 5. Interactive controls — the complete list

The page has **five** interactive elements. That is the entire interaction surface;
anything else in a mockup is wrong.

### 5.1 Replay position selector — header

The only significant control. A native `<select>`, styled: `bg-card`, 1px
`border-subtle`, radius 8px, padding 6px 10px, 12px `text-primary`, custom cyan
chevron. Focus: 2px `accent` ring.

- Preceded by an 11px `text-muted` label: `REPLAY`.
- Options, in order — first is default on load:

| Option label | `as_of` sent |
|---|---|
| `Latest reading (23 Jun 12:00)` | *(none — omitted from the request)* |
| `Peak inbound — alert in 2h` | `2004-06-23T06:00:00` |
| `Overnight trough before morning rush` | `2004-06-21T04:00:00` |
| `Quiet night, peak 6h out` | `2004-06-17T01:00:00` |
| `Morning build-up` | `2004-06-18T06:00:00` |

- Populated from `GET /api/replay`, not hardcoded in the HTML.
- **On change:** re-fetch `/api/current`, `/api/history`, `/api/forecast`,
  `/api/zones` with the new `as_of`; those four sections enter their loading state.
  Validation, daily-profile and feature-importance do **not** refetch — they
  describe the model and the whole dataset, not a moment in it.
- A 11px `text-muted` hint sits under the hero card when a non-default option is
  selected: `Viewing the dataset as it stood at 23 Jun 2004, 06:00. The forecast uses only data up to that hour.`

### 5.2 Chart tooltips
Hover (desktop) / tap (touch) on either chart. Not a button; no click target
beyond the tooltip. Cursor `crosshair` over the plot area.

### 5.3 `API docs` link — footer
Text link, `accent`, underline on hover, opens `/docs` in the same tab.

### 5.4 Retry button — error states only
Appears only inside a card that failed to load. `bg-card-raised`, 1px
`border-subtle`, radius 8px, padding 6px 12px, 12px `text-primary`, label
`Retry`. Re-issues that section's fetch.

### 5.5 Zone card hover
Background lifts `bg-card` → `bg-card-raised`, 150ms. Purely affordance feedback;
zone cards are **not** clickable and must not look clickable — no chevron, no
pointer cursor.

**Explicitly NOT present:** no login, no signup, no search, no filters, no date
picker beyond the replay select, no theme toggle, no export/download, no share,
no notification bell, no settings gear, no sidebar, no tabs, no modal, no
hamburger menu, no "upgrade" CTA.

---

## 6. Responsive behaviour

| Breakpoint | Layout |
|---|---|
| ≥1024px | Container 1200px. Hero 2-col. Forecast 6-across. Metrics 4-up. Zones 4-up. |
| 768–1023px | Hero 2-col. Forecast 3-across (2 rows). Metrics 2-up. Zones 2-up. |
| 640–767px | Hero stacks. Forecast 3-across. Metrics 2-up. Zones 2-up. |
| <640px | Everything single-column except forecast (2-across) and zones (2-up). Hero number 56px. Tagline hidden. Charts 260px. Padding 16px. |

Mobile rules: minimum touch target 44×44px (the replay select gets 44px height);
no horizontal page scroll at 360px width; charts stay inside their card.

---

## 7. Accessibility

- Contrast ≥ 4.5:1 for body text. The band colours are used for large text and
  fills only; band identity is **never conveyed by colour alone** — the band name
  is always printed next to the swatch.
- Every `<canvas>` has an adjacent visually-hidden text summary of the same data.
- Landmarks: `<header>`, `<main>`, `<footer>`; sections use `<section
  aria-labelledby>`.
- The alert banner is `role="status" aria-live="polite"` so it is announced when it
  appears.
- Visible 2px `accent` focus ring on the select, links and the retry button.
- Loading skeletons carry `aria-busy="true"`.

---

## 8. Prompts for generating mockup images

The page is tall; generate it in pieces and stitch, or generate the hero region
alone for the deck. **Prefix every prompt with this shared style block.**

**Shared style block:**

> Dark UI dashboard screenshot, very dark navy background #0a0f1a, card surfaces
> #111827 with 1px #1f2937 borders and 16px rounded corners, cyan #38bdf8 accent,
> clean system sans-serif, tabular numbers, generous whitespace, flat design with
> no gradients or glass effects, crisp and data-dense like a professional
> monitoring instrument panel, 1440px wide desktop viewport, straight-on view, no
> perspective, no device frame, no drop shadow around the page.

**Prompt A — hero region (best single image for the deck):**

> [style block] A web dashboard header reading "AirSense" with a small cyan
> rounded-square logo containing an upward line-chart glyph, tagline "Forecasting
> the pollution peak before it arrives.", and a pill badge "Live demo · MAIT,
> Delhi" at the right. Below it a thin info strip: "Historical dataset replay —
> not a live sensor feed." Below that a large card with a 4px amber left border
> containing the label "CURRENT READING", an enormous amber number "163.0" with
> smaller grey "ppb" beside it, an amber pill labelled "Moderate", and the line
> "Dataset time · 23 Jun 2004, 12:00". On the right of that card a 2×3 grid of
> small dark tiles: NO₂ 106.0 ppb, CO 2.2 mg/m³, BENZENE 13.1 µg/m³, TEMP 34.9 °C,
> HUMIDITY 20.5 %, HOUR 12:00. Across the card bottom, separated by a hairline
> rule: "RECOMMENDED ACTION NOW" above "Prefer indoor activity for sensitive
> individuals. Monitor."

**Prompt B — forecast strip with the alert (the product thesis):**

> [style block] A dashboard section headed "6-hour forecast". A prominent full
> width alert banner with a translucent orange background and a 1.5px orange
> border, an orange warning triangle, bold white text "Peak predicted in 2 hours
> — act now.", smaller grey text "Forecast reaches 239.7 ppb (High) at 08:00.
> Increase ventilation/filtration indoors.", and a small dark chip at the right
> reading "6H PEAK" above orange "256.0 ppb". Below it a row of six equal narrow
> cards, each with a 4px coloured bar across the top, showing in order: t+1 07:00
> "184.0 ppb" amber "Moderate" footnote "measured inputs"; t+2 08:00 "239.7 ppb"
> orange "High"; t+3 09:00 "256.0 ppb" orange "High"; t+4 10:00 "239.9 ppb" orange
> "High"; t+5 11:00 "234.7 ppb" orange "High"; t+6 12:00 "235.0 ppb" orange
> "High"; the last five footnoted "model-fed inputs".

**Prompt C — validation card:**

> [style block] A dashboard card with a cyan border headed "Model validation" with
> a small green pill reading "Beats baseline" at the right. Inside, four metric
> tiles in a row: "TEST MAE 25.92 ppb / our model", "BASELINE MAE 34.94 ppb /
> persistence", "IMPROVEMENT 25.8 % / lower error vs baseline" with the number in
> green, "R² 0.801 / on held-out test set". Below them two horizontal comparison
> bars on a shared scale: a shorter cyan bar labelled "AirSense 25.92 ppb" and a
> longer grey bar labelled "Persistence 34.94 ppb", captioned "Mean absolute error
> — lower is better." Below a hairline rule, small grey lines reading
> "Chronological train/test split — no future data leaked into training." and
> "Train: 1580 rows · Test: 396 rows".

**Prompt D — charts region:**

> [style block] Two stacked dashboard chart cards. The upper card headed "Recent
> history and forecast" contains a line chart on a dark grid: a solid cyan line
> across the left two-thirds, continuing as a dashed cyan line on the right third,
> joined at a single bright point marked by a vertical dashed grey divider
> labelled "now"; faint horizontal colour zones green at the bottom, amber in the
> middle, orange above, each labelled at the right edge; y-axis "NOx (ppb)",
> x-axis "Time (hourly)"; legend "Measured (last 48 h)" solid and "Forecast (next
> 6 h)" dashed. The lower card headed "Daily pollution cycle" contains a bar chart
> of 24 bars rising from very low at hours 3–5 to tall bars at hours 8–9 and again
> at 18–20, bars coloured green when short and amber to orange when tall, the
> 18–21 group outlined in orange under a bracket labelled "6–9 PM traffic window",
> y-axis "Mean NOx (ppb)", x-axis "Hour of day (0–23)", captioned "Evening peak
> averages 3.3x overnight levels (175.1 ppb vs 53.3 ppb)."

**Prompt E — zones section:**

> [style block] A dashboard section headed "Campus zones" with an amber warning
> pill reading "⚠ Simulated" at the right, and directly below a translucent amber
> disclosure strip reading "simulated zone offset — single sensor stream." with
> smaller grey text "We have one sensor, not four. Each zone applies a fixed
> documented multiplier to the one real measured value (163.0 ppb)." Below, four
> equal cards each with a coloured left border: "Main Gate 203.8 ppb High ×1.25",
> "Parking Block 187.4 ppb Moderate ×1.15", "Central Lawn 146.7 ppb Moderate
> ×0.90", "Library Block 130.4 ppb Moderate ×0.80", each with a tiny amber
> "simulated" tag and one line of small grey rationale text.

**Negative prompt for all of the above:**

> light mode, white background, glassmorphism, gradient mesh, neon glow, 3D,
> isometric, device mockup, phone frame, browser chrome, lorem ipsum, placeholder
> text, stock photography, human faces, illegible text, watermark, sidebar,
> hamburger menu, login form, avatar.

---

## 9. Hard rules

1. **Every number has a unit.**
2. **Every number comes from the API.** Nothing is hardcoded in the HTML —
   including the risk thresholds, the 3.3x ratio, and the band colours.
3. **Anything simulated says "simulated" on screen**, in the section header and on
   each individual card.
4. **No lorem ipsum, no placeholder images, no stock photos, no fake logos.**
5. **Never call the risk bands official.** The phrase "project-defined" appears
   next to them.
6. **Never write a bare time** where it could be read as the present moment —
   prefix `Dataset time`.
7. **No section renders blank.** Loading skeleton, then content or an error with
   Retry.
8. **Must be legible on a 360px-wide phone.**
