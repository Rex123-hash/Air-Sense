# AirSense — 60-second demo video script

**Total narration: 136 words.** At a natural pace (~150 wpm) that is ~55 seconds
spoken, leaving ~5 seconds of breathing room. Do not add more words — sixty
seconds is brutally short and rushing is the most common way these videos fail.

---

## Before you hit record

**Browser setup**
- [ ] Window at **1920×1080**, browser zoom **100%**
- [ ] Bookmarks bar hidden (`Ctrl+Shift+B`), no extra tabs, no extensions visible
- [ ] Close notifications (Windows Focus Assist on)

**Pre-load every view before recording.** Click through Dashboard → Forecast →
Data Explorer → Model Performance once, so charts are already rendered and no
loading skeleton appears on camera.

**Open these two tabs in this order:**

| Tab | URL |
|---|---|
| 1 | `https://airsense-526660427489.asia-south1.run.app/#/explorer` |
| 2 | `https://airsense-526660427489.asia-south1.run.app/#/dashboard?as_of=2004-06-23T06:00:00` |

> Tab 2 is the important one. That deep link opens **already showing the alert** —
> 73.0 ppb Low, with "Peak predicted in 2 hours" on screen from the first frame.
> No clicking around, no fumbling for the moment.

**Check the internet works.** The page loads Tailwind and Chart.js from CDNs. On
bad wifi it renders unstyled with no charts. Test the link once, right before
recording.

---

## The script

### Beat 1 — Problem · 0:00–0:08

**On screen:** your real MAIT campus photo from Assignment 1A, slow zoom in.

> "On our campus in Delhi, air quality spikes every single evening — and nobody
> knows until they're already breathing it."

*(20 words)*

---

### Beat 2 — Insight · 0:08–0:18

**On screen:** Tab 1 — **Data Explorer**. The daily-cycle bar chart. Let the
orange "6–9 PM traffic window" bracket sit in frame. Do not scroll.

> "We analysed two thousand hours of real sensor data. Evening NOx runs
> three-point-three times overnight levels. It's not random. It's a predictable
> daily cycle."

*(25 words)*

---

### Beat 3 — Demo · 0:18–0:40 ← **the heart of the video, give it the most time**

**On screen:** switch to Tab 2 — **Dashboard**, already at the alert position.

Choreograph the cursor to follow the words, pausing on each:

| When you say… | Cursor rests on |
|---|---|
| "seventy-three parts per billion" | the big `73.0` and the green **Low** pill |
| "already warning us" | the orange **alert banner** |
| "two hours, at two-forty" | the **t+2 card** — `239.7 ppb · High` |
| "what to do" | the **recommended action** line |

> "So we forecast it. AirSense is reading seventy-three parts per billion right
> now — Low. Calm. But it's already warning us: the peak lands in two hours at
> two-forty, High. And it tells you what to do — move outdoor sessions indoors."

*(41 words — then **stay silent for ~3 seconds** and just let the forecast strip
sit on screen. Silence here reads as confidence.)*

---

### Beat 4 — Validation · 0:40–0:53 ← **your differentiator**

**On screen:** click **Model Performance** in the sidebar. Hold on the four metric
tiles for ~4 seconds, then scroll down slowly to the backtest chart and stop with
the green **early-warning callout** in frame.

> "Validated on a held-out chronological test set — no future data leaked.
> Twenty-five point eight percent better than baseline. Of seventy-two hours that
> actually went High, it caught fifty-two an hour early."

*(32 words)*

---

### Beat 5 — Impact · 0:53–1:00

**On screen:** scroll back to the top of Model Performance, or cut to a clean
title card showing the live URL, large.

> "Next: a real sensor pilot at MAIT. AirSense makes air quality something you
> plan around, not react to."

*(18 words)*

---

## Numbers you say out loud — say them exactly

| Say | Not |
|---|---|
| "three-point-three times" | "over three times" |
| "twenty-five point eight percent" | "twenty-six percent" ← the UI shows 25.8 % |
| "seventy-three parts per billion" | "seventy-three" |
| "two-forty" *(for 239.7)* | "two hundred thirty-nine point seven" |

> **The 25.8 % matters.** If you say "26 percent" while the screen shows 25.8 %, a
> sharp evaluator notices the mismatch. Say the number that is on screen.

---

## Recording

- **Screen record:** OBS Studio, or Windows Game Bar (`Win+G`). 1080p, 30 fps.
- **Record audio separately** if your room is noisy, then align in the edit. Clean
  audio matters far more than video quality.
- **Rehearse three times before recording.** A usable 1-minute video usually takes
  about five takes.
- **Do not read the slides aloud.** Show the product working. The demo beat is
  what earns the marks.
- Move the cursor **slowly and deliberately**. Fast mouse movement reads as panic.

## Delivery

- [ ] Export ≤ 60 seconds
- [ ] Upload to Drive, sharing set to **"Anyone with the link"**
- [ ] **Test the link in an incognito window** — a dead link scores zero on that
      criterion
- [ ] Put the live URL on the final frame, large enough to read on a phone

---

## If something breaks mid-recording

| Problem | Fix |
|---|---|
| Page loads unstyled / no charts | CDN blocked or wifi down. Reconnect and hard-reload (`Ctrl+F5`). |
| Alert banner missing | You lost the `?as_of=` parameter. Re-open the Tab 2 URL exactly as written. |
| A loading skeleton appears on camera | You didn't pre-load. Click through all views once, then re-record. |
| Cloud Run feels slow on the first hit | Cold start. Load the URL once a minute before recording to warm it. |

---

## Fallback: 45-second cut

If you run over, drop **Beat 1** entirely and open on the Data Explorer chart with:

> "Air quality on our Delhi campus spikes every evening — three-point-three times
> overnight levels. It's a predictable cycle."

Then continue from Beat 3. **Never cut the demo or the validation beat** — those
two are the project.
