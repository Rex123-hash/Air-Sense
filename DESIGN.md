# AirSense — UI Design Specification

Complete specification of the interface: the app shell, every view, component,
control, state and copy string. Written so that (a) the frontend can be built
from it without further decisions, and (b) mockup images can be generated from
it (§9).

**Every number in this document is a real value produced by the actual training
run and API.** If you generate a mockup, use these exact figures — a mockup
showing different numbers than the deployed app is worse than no mockup.

---

## 0. Product in one sentence

AirSense predicts the hyper-local NOx pollution peak **before it arrives** and
attaches a concrete recommended action, turning air quality from something you
react to into something you plan around.

---

## 1. App structure

A **sidebar shell** with six client-side views. No page reloads, no router
library — the view is driven by `location.hash`.

```
┌────────────┬──────────────────────────────────────────────┐
│            │  Topbar: view title + subtitle + location    │
│  Sidebar   ├──────────────────────────────────────────────┤
│  (250px)   │  Data-mode notice  (on every view)           │
│            │                                              │
│  brand     │  ┌────────────────────────────────────────┐  │
│  nav ×7    │  │           active view content          │  │
│            │  └────────────────────────────────────────┘  │
│  ─────     │                                              │
│  status    │  Footer line                                 │
│  card      │                                              │
└────────────┴──────────────────────────────────────────────┘
```

| View | Hash | Purpose |
|---|---|---|
| **Dashboard** | `#/dashboard` | Hero reading + 6-hour forecast strip + alert banner |
| **Forecast** | `#/forecast` | History joined to forecast chart, hour-by-hour table, CSV export |
| **Data Explorer** | `#/explorer` | Daily pollution cycle + cleaning summary |
| **Model Performance** | `#/model` | Validation metrics, backtest, early-warning skill, feature importance |
| **Campus Zones** | `#/zones` | Four zones, labelled simulated |
| **Method & Limits** | `#/method` | Risk bands, data citation, limitations, credits |
| **API Docs** | `/docs` | FastAPI Swagger UI — external link, opens in a new tab |

There is deliberately **no** login, settings page, profile, search, or theme
toggle. Adding them would imply functionality that does not exist.

**Deep links carry the replay position:**
`#/dashboard?as_of=2004-06-23T06:00:00`

---

## 2. Design system

### 2.1 Colour — light theme, green eco brand

| Token | Hex | Use |
|---|---|---|
| `bg-base` | `#f4f5f6` | Page background |
| `bg-card` | `#ffffff` | Card surfaces, sidebar, topbar |
| `bg-raised` | `#f8f9fa` | Metric tiles, nested surfaces |
| `border` | `#e5e7eb` | 1px card borders |
| `border-soft` | `#eef0f2` | Inner dividers, table rules |
| `text` | `#1f2937` | Headings, all large numbers |
| `text-2` | `#4b5563` | Body copy |
| `muted` | `#6b7280` | Labels, units, captions |
| `brand` | `#15803d` | Section bars, active nav, chart lines, primary buttons |
| `brand-dark` | `#14532d` | Wordmark |
| `brand-light` | `#16a34a` | Validation card border, status dot |
| `brand-tint` | `#eff7f1` | Active nav background, notice strip, callouts |

**Risk band colours** — the only saturated colours on the page, so risk reads
instantly. They come from the API (`risk_hex`) and are **never hardcoded in the
UI**.

| Band | NOx (ppb) | Hex |
|---|---|---|
| Low | `< 100` | `#22c55e` |
| Moderate | `100 – 200` | `#f59e0b` |
| High | `200 – 300` | `#f97316` |
| Severe | `> 300` | `#ef4444` |

> Bands are **project-defined operational thresholds for demonstration**. They
> are NOT official CPCB or WHO AQI categories and must never be labelled as
> such. This disclaimer appears in the UI, not just in this document.

**Colour usage rule:** large numeric values render in `text` (near-black), never
in the band colour. Band identity is carried by the **pill, the dot, the card's
top/left border, and the band name** — so colour is never the only signal.

### 2.2 Typography

System font stack — no webfont, because a webfont is a network dependency that
can fail mid-demo.

```css
font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
font-variant-numeric: tabular-nums;   /* numbers must not jitter on update */
```

| Role | Size / weight |
|---|---|
| Hero NOx number | 78px / 800 (62px ≤900px, 54px ≤640px) |
| Metric tile value | 36px / 800 |
| Zone value | 32px / 800 |
| Forecast card value | 28px / 800 |
| View title (topbar) | 22px / 700 |
| Section heading | 21px / 700, preceded by a 4px green bar |
| Body | 14px / 400 |
| Uppercase label | 11.5–12px / 600, `letter-spacing: .07em` |
| Caption | 12.5px / 400, `muted` |

**Every number carries a unit** — `163.0 ppb`, never `163.0`. Units render at
~0.45em in `muted`.

### 2.3 Spacing, radius, elevation

- Spacing scale: `4 / 8 / 12 / 16 / 20 / 24 / 32 / 48`px
- Sidebar 250px; content padding 24px 28px (16px on mobile)
- Card radius 14px; pill radius 9999px; inner tile radius 12px
- Card border `1px solid #e5e7eb`; shadow `0 1px 2px rgba(16,24,40,.04), 0 1px 3px rgba(16,24,40,.06)`
- No glassmorphism, no gradient meshes, no decorative blur. It is an instrument panel.

### 2.4 Logo

Vector leaf with airflow currents, in a green gradient (`#15803d → #4ade80`),
with a darker midrib and three veins. Shipped as `app/static/logo.svg`, used for
both the sidebar mark (34×34) and the favicon. A wide banner version with
wordmark, tagline and a forecast sparkline lives at `docs/banner.svg` for the
README.

### 2.5 Motion

- Sidebar slide-in on mobile: 220ms ease
- Zone card hover: shadow lift, 150ms
- Loading skeletons: 1.5s shimmer
- `@media (prefers-reduced-motion: reduce)` disables all animation and transition

---

## 3. Global states

Every data-driven region must define all four. No region may render blank.

| State | Treatment |
|---|---|
| **Loading** | Skeleton block, same height as loaded content so layout does not jump |
| **Loaded** | Real content |
| **Error** | ⚠ icon + "Could not load <thing>." + a **Retry** button, inside the card. Never a raw stack trace, never an empty card. |
| **Empty** | Not reachable — data ships with the repo. A zero-length chart shows the error state instead of an empty axis. |

If the API is unreachable at boot, a single card appears at the end of `main`
with a Retry that reloads the page.

---

## 4. The shell

### 4.1 Sidebar (250px, sticky, full height)

**Brand block** — `logo.svg` at 34×34, then `AirSense` at 22px/800 in `brand-dark`.

**Nav** — seven items, each: 19px stroked icon + label, 10px/12px padding, 9px
radius, 3px transparent left border.
- Default: `text-2`
- Hover: `bg-raised`, `text`
- **Active: `brand-tint` background, `brand` text, 600 weight, `brand` left border**

Icons (all 1.6px stroke, `currentColor`, no fill): four squares (Dashboard),
trend line with arrow (Forecast), bar chart (Data Explorer), target/crosshair
(Model Performance), map pin (Campus Zones), database cylinder (Method & Limits),
angle brackets (API Docs).

**Status card** (bottom, pushed down with `margin-top:auto`):
- `● Live demo` — 8px `brand-light` dot + 13px `text-2`
- `MAIT, Delhi` — 15px/700
- `Historical dataset replay` — 12px `muted`
- **Replay walkthrough** button (§6.1)
- Divider, then `Dataset position` label over the current timestamp in bold

> **Do not display GPS coordinates or a wall-clock "last updated" time.**
> Coordinates imply a sensor physically at MAIT; a live timestamp implies a live
> feed. Neither is true. Show the dataset position instead.

### 4.2 Topbar (sticky, blurred white, 1px bottom border)

Mobile nav toggle (hidden ≥861px) · view title (22px/700) + subtitle (13.5px
`muted`) · location badge (pin icon + `MAIT, Delhi`, hidden ≤640px).

Title and subtitle per view:

| View | Title | Subtitle |
|---|---|---|
| Dashboard | Dashboard | Current air quality and the next six hours. |
| Forecast | Forecast | Measured history joined to the six-hour prediction. |
| Data Explorer | Data Explorer | The daily cycle the forecast is built on, and how the data was cleaned. |
| Model Performance | Model Performance | Validation against a naive baseline, backtested hour by hour. |
| Campus Zones | Campus Zones | Derived from one sensor stream — every value is labelled simulated. |
| Method & Limits | Method & Limits | Risk bands, data source, and what this system cannot do. |

### 4.3 Data-mode notice — on every view, not dismissible

`brand-tint` background, ⓘ icon in `brand`, 14px radius.

> **`Historical dataset replay — not a live sensor feed.`**
> `UCI Air Quality Data Set (De Vito et al., 2008), 2000 hourly readings from 11 Mar – 23 Jun 2004. Forecasts are computed live by the model from data up to the selected hour only.`

---

## 5. View specifications

### 5.1 Dashboard

**Hero card** — white, 5px left border in the current band colour, 26px/30px padding.

Two columns (`1fr / 1.15fr`, stacked ≤900px):

*Left:* `CURRENT READING` label · `163.0` at 78px/800 in `text` + `ppb` at 26px
`muted` · band pill (`#f59e0b` text on `#f59e0b1f`, dot + `Moderate`) ·
`Dataset time · 23 Jun 2004, 12:00`.

> The words **"Dataset time"** are mandatory. A bare time would read as "now".

*Right:* 3×2 tile grid (2×3 ≤640px), each `bg-raised`, 12px radius:

| Label | Value | Unit |
|---|---|---|
| `NO₂` | 106.0 | ppb |
| `CO` | 2.2 | mg/m³ |
| `BENZENE` | 13.1 | µg/m³ |
| `TEMP` | 34.9 | °C |
| `HUMIDITY` | 20.5 | % |
| `HOUR` | 12:00 | — |

*Card footer:* 1px rule, then `RECOMMENDED ACTION NOW` label, the action at
21px/700 (`Prefer indoor activity for sensitive individuals. Monitor.`), and the
threshold note at 12.5px `muted`.

*Below the card,* when a non-default replay position is active:
`Viewing the dataset as it stood at 23 Jun 2004, 06:00. The forecast uses only data up to that hour.`

**Alert banner** — rendered above the forecast cards when any of the next 6 hours
is High or Severe (`forecast.alert != null`). Band colour at 8% background, 1px
border in the band colour, 14px radius.

- 44px filled circle in the band colour with a white warning triangle
- Line 1, 20px/700: `Peak predicted in 2 hours — act now.` *(singular "1 hour" when n=1)*
- Line 2, 14px `text-2`: `Forecast reaches 239.7 ppb (High) at 08:00. Increase ventilation/filtration indoors. Move outdoor sessions indoors.`
- Right chip, white with band border: `6H PEAK` over `256.0 ppb`

**Calm variant** (`alert == null`) — identical geometry in `brand` green, with a
check icon: `No High or Severe hours in the next 6 hours.` /
`Forecast peaks at 199.9 ppb (Moderate) at 18:00.`

**Forecast strip** — 6 cards (`repeat(6,1fr)`; 3 ≤1180px; 2 ≤640px). Never a
horizontal scroller. Each card is centred, with a 5px top bar in its band colour:

offset chip (band-tinted pill) · time · value 28px/800 in `text` + unit · band
name with dot in band colour · footnote.

At the demo replay position `as_of=2004-06-23T06:00`:

| Card | Time | Predicted | Band | Footnote |
|---|---|---|---|---|
| t+1 | 07:00 | 184.0 ppb | Moderate | measured inputs |
| t+2 | 08:00 | 239.7 ppb | High | model-fed inputs |
| t+3 | 09:00 | 256.0 ppb | High | model-fed inputs |
| t+4 | 10:00 | 239.9 ppb | High | model-fed inputs |
| t+5 | 11:00 | 234.7 ppb | High | model-fed inputs |
| t+6 | 12:00 | 235.0 ppb | High | model-fed inputs |

The `measured inputs` / `model-fed inputs` footnote is driven by the API's
`inputs_measured` flag and is how the UI admits error compounds with horizon.

**Assumption caption**, full width, 12.5px `muted`:
`Recursive multi-step forecast · exogenous features held constant. Temperature, humidity and co-pollutants are held at their last observed values; from t+2 the NOx lags are fed by the model's own predictions, so uncertainty grows with the horizon.`

### 5.2 Forecast

**Chart card** — legend top-right: solid green `Measured (last 48 h)`, dashed
green `Forecast (next 6 h)`. Chart height 340px (300px mobile).

- Solid `#15803d` 2.5px line for 48 measured hours, point marker only on the last
- Dashed `[7,5]` continuation **starting at the last measured point** so the lines join
- Risk-band zones tinted at 10% behind the data, labelled in an 84px right gutter
- Vertical dashed `now` divider at the last measured hour, with rotated label
- Axes: `Time (hourly)`, `NOx (ppb)` from zero
- Dark `#1f2937` tooltip: `23 Jun 2004, 08:00` / `239.7 ppb · Forecast`
- `mode:'index'`, no zoom, no pan — nothing accidentally triggerable during a demo

**Hour-by-hour table** — columns: Horizon · Time · Predicted NOx · Risk band ·
Inputs · Recommended action. Horizontally scrollable inside its card below 640px.
Header has a **Download CSV** button (§6.4).

### 5.3 Data Explorer

**Daily cycle chart** — 24 bars, one per hour-of-day, 340px tall.
- Each bar coloured by the band its own mean falls into
- Hours 18–21 get full opacity and a 2px `#ea580c` border
- Value labels printed above every bar
- An orange bracket spans hours 18–21, labelled `6–9 PM traffic window`
- Risk zones tinted behind, labelled in the right gutter
- Axes: `Hour of day (0–23)`, `Mean NOx (ppb)`

Real values, hour 0 → 23:
`95.9, 69.6, 48.3, 48.5, 35.3, 46.0, 83.5, 175.4, 219.7, 210.8, 179.3, 153.6,
135.2, 128.5, 122.5, 125.4, 128.8, 152.4, 175.9, 198.4, 187.8, 138.3, 111.6, 111.1`

Meta: `Mean of 2000 hourly readings · 83.3 days`

Caption (computed live, **never hardcoded**):
> `Evening peak averages 3.3x overnight levels (175.1 ppb in 18:00–21:00 vs 53.3 ppb in 03:00–06:00).` *(15px/600)*
> `Pollution is not random — it is a predictable daily cycle tracking traffic. That predictability is what makes forecasting viable.` *(12.5px muted)*

**Cleaning summary** — 3×2 tile grid, then the five numbered cleaning steps, then
the honesty caption.

| Rows in | Rows out | Sentinels replaced | Nulls filled | Duplicates removed | Non-hourly gaps |
|---|---|---|---|---|---|
| 2000 | 2000 | **0** | 0 | 0 | 63 |

Caption: `This source was already cleaned upstream, so the sentinel pass found nothing to replace. The guard remains because a raw UCI file contains thousands of −200 values. We are not claiming credit for removing sentinels that were not there.`

### 5.4 Model Performance — the differentiator

**Validation card** — 1.5px `brand-light` border (the only accent-bordered card).
Heading pill: `✓ Beats baseline` (green). If `beats_baseline` were ever false it
must read `✕ Does not beat baseline` in red — never suppressed.

Four metric tiles:

| Label | Value | Sublabel |
|---|---|---|
| `TEST MAE` | 25.92 ppb | our model |
| `BASELINE MAE` | 34.94 ppb | persistence |
| `IMPROVEMENT` | 25.8 % *(in `brand` green)* | lower error vs baseline |
| `R²` | 0.801 | on held-out test set |

Then a two-column split — left: comparison bars on a shared scale (`AirSense`
green 25.92 ppb, `Persistence` grey 34.94 ppb, caption `Mean absolute error —
lower is better.`); right, behind a vertical rule:

- `Chronological train/test split — no future data leaked into training.`
- `Train: 1580 rows · 12 Mar 2004, 18:00 → 2 Jun 2004, 22:00`
- `Test: 396 rows · 2 Jun 2004, 23:00 → 23 Jun 2004, 12:00`
- `Baseline "persistence" predicts next hour = current hour — the honest naive benchmark.`
- `Co-pollutants and weather lagged 1 h, so every feature was knowable before the predicted hour.`

**Backtest card** — legend: grey `Actual`, green `Predicted`. A 396-point line
chart across the whole held-out test period, risk zones tinted behind, 340px.

Below it, an **early-warning callout** (`brand-tint`, 4px green left border):
> `EARLY WARNING · 1 HOUR AHEAD`
> `Of the 72 hours that actually exceeded 200 ppb (High) in the test period, the model flagged 52 of them an hour in advance — 72.2% caught, 77.6% of warnings correct (20 missed, 15 false alarms).`

Then a 3×2 stat grid:

| Hours tested | Median error | Within 25 ppb | Within 50 ppb | Worst error | Baseline MAE |
|---|---|---|---|---|---|
| 396 | 17.52 ppb | 61.6 % | 86.4 % | 166.3 ppb | 34.94 ppb |

**Feature importance** — two-column split: horizontal green bar chart (13 rows,
raw importance values printed to the right of each bar, monospace y-labels, x-axis
hidden) on the left; explanatory copy on the right behind a rule.

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

Copy: `Recent NOx and hour-of-day dominate — consistent with a traffic-driven daily cycle. Every input is lagged by at least one hour, so the model never sees the hour it is predicting.`

### 5.5 Campus Zones

Heading pill: `⚠ Simulated` (amber, bordered — deliberately not subtle).

**Mandatory disclosure strip** before the cards — amber tinted, warning icon:
> **`simulated zone offset — single sensor stream.`** `We have one sensor, not four. Each zone applies a fixed documented multiplier to the one real measured value (163.0 ppb) to demonstrate the multi-zone design. These are not four independent sensors.`

Four cards (2-up ≤1180px, 1-up ≤640px), each with a 5px left border in its band
colour: name 16.5px/700 · value 32px/800 in `text` · a row containing the band
pill and the `×1.25` multiplier chip · rationale above a hairline rule · an
amber `simulated` tag **on every card**.

| Zone | Value | Band | Multiplier | Rationale |
|---|---|---|---|---|
| Main Gate | 203.8 ppb | High | ×1.25 | Directly traffic-exposed — vehicle queue at entry |
| Parking Block | 187.4 ppb | Moderate | ×1.15 | Cold starts and idling vehicles |
| Central Lawn | 146.7 ppb | Moderate | ×0.90 | Open ground, set back from the road |
| Library Block | 130.4 ppb | Moderate | ×0.80 | Sheltered, furthest from the carriageway |

Zone cards are **not clickable** and must not look clickable — no chevron, no
pointer cursor. Hover lifts the shadow only.

### 5.6 Method & Limits

1. **Risk bands table** — Band pill · NOx range · Recommended action, for all four
   bands, followed by the `project-defined … not official CPCB/WHO standards` note.
2. **Data source** — full De Vito et al. (2008) citation and the pipeline line.
3. **Limitations** — the seven honesty notes as a real bulleted list, with the
   gap count and sentinel count injected from `metrics.json` rather than typed.
4. **Credits** — team, stack, and the AI-tools disclosure.

---

## 6. Interactive controls — the complete list

Nine interactive elements. Anything else in a mockup is wrong.

| # | Control | Behaviour |
|---|---|---|
| 6.1 | **Replay walkthrough** dropdown (sidebar) | Green outlined pill button + play icon. Opens a listbox of 5 options above it. Sets `?as_of=` in the hash. |
| 6.2 | **Nav links** ×6 | Switch view via hash. Each link **carries the current `as_of`** so the replay position survives navigation. |
| 6.3 | **API Docs** link | Opens `/docs` in a new tab (`target="_blank" rel="noopener"`). |
| 6.4 | **Download CSV** (Forecast view) | Exports the current forecast with `#` provenance headers: issue time, data mode, assumption, threshold note. |
| 6.5 | **Mobile nav toggle** | ≤860px only. Slides the sidebar in; sets `aria-expanded`. |
| 6.6 | **Nav scrim** | Closes the mobile sidebar on click. |
| 6.7 | **Chart tooltips** | Hover/tap on any of the four charts. |
| 6.8 | **Retry buttons** | Only inside a failed region. |
| 6.9 | **Skip to content** link | Visible on keyboard focus only. |

**Replay options** (populated from `GET /api/replay`, never hardcoded):

| Label | `as_of` |
|---|---|
| `Latest reading (23 Jun 12:00)` | *(none)* |
| `Peak inbound - alert in 2h` | `2004-06-23T06:00:00` |
| `Overnight trough before morning rush` | `2004-06-21T04:00:00` |
| `Quiet night, peak 6h out` | `2004-06-17T01:00:00` |
| `Morning build-up` | `2004-06-18T06:00:00` |

On change, only **Dashboard, Forecast and Zones data** refetch. Validation,
backtest, daily profile and feature importance describe the model and the whole
dataset, not a moment in it.

**Explicitly NOT present:** login, signup, search, filters, theme toggle, share
button, notification bell, settings gear, tabs, modals, "upgrade" CTA, or any
link to a page that does not exist (no Privacy policy or Terms of use — shipping
dead links is worse than omitting them).

---

## 7. Responsive behaviour

| Breakpoint | Layout |
|---|---|
| ≥1181px | Sidebar fixed. Forecast 6-across. Metrics 4-up. Zones 4-up. Splits two-column. |
| 901–1180px | Forecast 3-across. Metrics 2-up. Zones 2-up. Splits collapse to one column with a top rule. |
| 861–900px | Hero stacks; hero number 62px. |
| ≤860px | **Sidebar becomes off-canvas** with a toggle and scrim. Content padding 16px. |
| ≤640px | Forecast 2-across. Pollutants 2-up. Zones 1-up. Charts 300px. Hero number 54px. Topbar subtitle and location badge hidden. |

Mobile rules: minimum 44×44px touch targets; **no horizontal page scroll at
360px**; charts constrained by `canvas { max-width: 100% }`; wide tables scroll
inside their own card.

---

## 8. Accessibility

- Body text contrast ≥ 4.5:1. Band colours are used for pills, borders and fills;
  **band identity is never conveyed by colour alone** — the band name is always printed.
- Every `<canvas>` has an adjacent visually-hidden text summary of the same data.
- Landmarks: `<aside>`, `<header>`, `<main>`, `<footer>`; nav is `<nav aria-label="Sections">`.
- The alert banner is `role="status" aria-live="polite"`.
- The replay dropdown is a `button[aria-haspopup=listbox][aria-expanded]` over a
  `ul[role=listbox]` of `li[role=option][aria-selected]`, operable with Enter,
  Space and Escape, and closes on outside click.
- Visible 2px `brand` focus ring on every interactive element.
- Skip-to-content link as the first focusable element.

---

## 9. Prompts for generating mockup images

Generate per-screen and stitch, or generate the Dashboard alone for the deck.
**Prefix every prompt with this shared style block.**

**Shared style block:**

> Light-mode SaaS dashboard screenshot, very light grey page background #f4f5f6,
> pure white cards with 1px #e5e7eb borders and 14px rounded corners and a very
> subtle shadow, dark green #15803d accent, near-black #1f2937 text, clean system
> sans-serif, tabular numbers, generous whitespace, flat design with no gradients
> or glass effects, crisp and data-dense like a professional monitoring
> instrument panel, 1440px desktop viewport, straight-on view, no perspective, no
> device frame. A 250px white left sidebar with a green leaf logo and the
> wordmark "AirSense", a vertical nav list, and the active item highlighted in
> pale green with a green left bar.

**Prompt A — Dashboard (best single image for the deck):**

> [style block] The main area shows a topbar reading "Dashboard" with the
> subtitle "Current air quality and the next six hours", a pale green info strip
> reading "Historical dataset replay — not a live sensor feed.", then a large
> white card with a 5px amber left border containing "CURRENT READING", an
> enormous near-black number "163.0" with grey "ppb", an amber pill labelled
> "Moderate", and "Dataset time · 23 Jun 2004, 12:00"; to its right a 3×2 grid of
> pale tiles: NO₂ 106.0 ppb, CO 2.2 mg/m³, BENZENE 13.1 µg/m³, TEMP 34.9 °C,
> HUMIDITY 20.5 %, HOUR 12:00; across the card bottom "RECOMMENDED ACTION NOW"
> above bold "Prefer indoor activity for sensitive individuals. Monitor."

**Prompt B — Forecast strip with the alert (the product thesis):**

> [style block] A section headed "6-hour forecast" with a full-width pale orange
> alert banner: a solid orange circle containing a white warning triangle, bold
> near-black text "Peak predicted in 2 hours — act now.", grey subtext "Forecast
> reaches 239.7 ppb (High) at 08:00. Increase ventilation/filtration indoors.",
> and a white chip at the right reading "6H PEAK" above "256.0 ppb". Below, six
> equal white cards each with a coloured top bar: t+1 07:00 "184.0 ppb" amber
> "Moderate" footnote "measured inputs"; then t+2 08:00 "239.7 ppb", t+3 09:00
> "256.0 ppb", t+4 10:00 "239.9 ppb", t+5 11:00 "234.7 ppb", t+6 12:00 "235.0
> ppb", all orange "High" and footnoted "model-fed inputs".

**Prompt C — Model Performance:**

> [style block] A white card with a green border headed "Model validation" with a
> pale green pill "✓ Beats baseline". Four pale metric tiles: "TEST MAE 25.92
> ppb / our model", "BASELINE MAE 34.94 ppb / persistence", "IMPROVEMENT 25.8 % /
> lower error vs baseline" with the number in green, "R² 0.801 / on held-out test
> set". Below, two horizontal comparison bars on a shared scale: a shorter green
> bar "AirSense 25.92 ppb" and a longer grey bar "Persistence 34.94 ppb". Beneath,
> a second card headed "Backtest — predicted vs actual" showing a long line chart
> where a grey "Actual" line and a green "Predicted" line track each other
> closely across faint horizontal green, yellow and orange bands, and a pale green
> callout reading "EARLY WARNING · 1 HOUR AHEAD" above "Of the 72 hours that
> actually exceeded 200 ppb, the model flagged 52 an hour in advance".

**Prompt D — Data Explorer:**

> [style block] A card headed "Daily pollution cycle" containing a bar chart of 24
> bars with the value printed above each bar, rising from very low green bars at
> hours 3–5 to tall orange bars at hours 8–9 and again at 18–20, with the 18–21
> group outlined in orange beneath an orange bracket labelled "6–9 PM traffic
> window", faint horizontal green/yellow/orange risk bands behind, y-axis "Mean
> NOx (ppb)", x-axis "Hour of day (0–23)", and the bold caption "Evening peak
> averages 3.3x overnight levels (175.1 ppb vs 53.3 ppb)."

**Prompt E — Campus Zones:**

> [style block] A section headed "Campus zones" with an amber pill "⚠ Simulated"
> at the right and a pale amber disclosure strip reading "simulated zone offset —
> single sensor stream." with grey subtext "We have one sensor, not four." Below,
> four white cards each with a coloured left border: "Main Gate 203.8 ppb" with an
> orange "High" pill and "×1.25" chip; "Parking Block 187.4 ppb" Moderate ×1.15;
> "Central Lawn 146.7 ppb" Moderate ×0.90; "Library Block 130.4 ppb" Moderate
> ×0.80 — each with one line of grey rationale and a small amber "simulated" tag.

**Negative prompt for all of the above:**

> dark mode, black background, glassmorphism, gradient mesh, neon glow, 3D,
> isometric, device mockup, phone frame, browser chrome, lorem ipsum, placeholder
> text, stock photography, human faces, illegible text, watermark, hamburger menu
> on desktop, login form, avatar, shopping cart.

---

## 10. Hard rules

1. **Every number has a unit.**
2. **Every number comes from the API** — including risk thresholds, band colours,
   the 3.3× ratio, and the cleaning counts. Nothing is hardcoded in the HTML.
3. **Anything simulated says "simulated" on screen**, in the section header *and*
   on each individual card.
4. **No lorem ipsum, no placeholder images, no stock photos, no dead links.**
5. **Never call the risk bands official.** "Project-defined" appears beside them.
6. **Never write a bare time** where it could read as the present moment — prefix
   `Dataset time`.
7. **Never imply a live feed or a physical sensor** — no wall-clock timestamps,
   no GPS coordinates.
8. **No region renders blank** — skeleton, then content or an error with Retry.
9. **Legible on a 360px-wide phone**, with no horizontal page scroll.
