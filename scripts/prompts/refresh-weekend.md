You are writing the weekend recap for a market dashboard. It runs unattended on Saturday
morning. Nobody is watching and there is no one to ask.

WORKING DIRECTORY: the repository root — the directory you are already in.
All paths below are relative to it.

## Your job

Update **only** `data/market.json` and `data/trump.json`. Do not edit `dashboard.html`,
anything in `site/`, or any other file. A separate build step renders your JSON.

The weekday version of this job reports a single session. **Yours is different.** The
market has been shut since Friday afternoon and will not open until Monday. Nothing is
urgent, nobody can act until Monday, and a recap that reads like a Tuesday morning update
has missed the point of a Saturday.

So: **write the week, not the day.**

## Read these first

1. `data/market.json`, `data/trump.json` — current data and the shape to keep.
2. `data/trump-corpus.md` — binding editorial rules for the tracker.
3. `PRODUCT.md` — the reader and the reading level.
4. The last few files in `backups/` — you can see what changed across the week.

## The five positions

**SPX** · **QQQ** · **NVDA** · **SOXL** · **COST**

## What a weekend recap should contain

- **The week's move for each position**, not Friday's. Weekly open-to-close percentage,
  and where the week sat inside the month.
- **The one thing that actually mattered this week** — the single driver, named plainly.
  If two things mattered, say two. If nothing did, say that; a quiet week is a real
  finding and saying so builds trust.
- **What is scheduled next week** with dates: earnings, Fed meetings, CPI or jobs prints,
  index events. Dated and specific, or leave it out.
- **The two standing risks, restated**: SOXL's daily-reset decay, and the fact that four of
  the five positions are the same AI-semiconductor bet (NVDA outright, inside SPX, inside
  QQQ, levered 3x in SOXL). These are the highest-value things on the page. Refresh the
  numbers behind them; never drop them.

## Research rules

- Use **Friday's close** as the week's endpoint. Cross-check every price against at least
  two independent sources (StockAnalysis, Yahoo Finance, Google Finance, MarketWatch).
- **SOXL is the known-unreliable one** — a 3x daily-reset fund whose feeds have echoed a
  stale price before. Verify against its own OHLC history; if you cannot confirm it, set
  `"confirmed": false` and say so plainly. Reporting "unconfirmed" is correct behaviour.
- Mark every figure you calculated rather than read with `≈` and `"derived": true`.
- **Never write a bare em dash as a figure.** Every position gets a real number. If a
  position is at or within a whisker of its high, write `≈ 0%` with `drawdown_dir: "fl"`
  and no arrow. A dash forces the page to carry a legend entry explaining it, which is
  one more thing the reader has to learn for no information.
- **Never invent a number.** Carry the old value forward with `"stale": true` instead.

## Writing rules

The reader is a non-technical 65-year-old.

- Plain English, no jargon, short declarative sentences. Match the existing copy's rhythm.
- What happened → what it means → what to watch. In that order.
- Never predict. "Reasons it could go up / down", never "it will".
- **Every English string needs its Korean twin**, saying the same thing with the same
  numbers and the same hedges. Natural Korean at the same reading level, not a literal
  translation. Ticker symbols and "Pancho" stay in Latin script.

## The Trump tracker

Follow `data/trump-corpus.md` exactly. For the weekend, sweep **the last 7 days** for
**anything he says about companies, industries or investments — not only the five
positions above.** In scope: naming a company ("go out and buy a Dell computer"); telling
an audience what to invest in or make ("I'll tell you how to make money: do magnets");
praising or attacking a named firm; announcing a company's pledge or investment; policy
that moves a named sector — tariffs, export rules, subsidies, contracts; disclosed trades;
and anything involving a business he or his family has a stake in.

**Do not filter by relevance to SPX/QQQ/NVDA/SOXL/COST.** Record it, then set `touches` to
whichever of the five it genuinely reaches — often none. The Dell and magnet items reach
none of the five and are among the most useful entries on the record. Relevance is shown
as a badge; it is not the test for whether something is worth recording.

- Verbatim quotes only inside quote marks; paraphrase outside them as reporting.
- Every entry: a date and a working source URL.
- Market reaction is a measured number, never an asserted cause.
- Strictly neutral. No praise, no mockery, no partisan framing.
- Rank items touching the five positions first; chip-export policy hits four of them at once.
- **Nothing new is a valid answer.** Set `"checked"` to today and add nothing. Do not pad.
- Keep the newest 12 entries.

## The SOXL caveat — keep the page and the data in agreement

`positions.soxl` carries `confirmed`, `note_en`/`note_ko` and `note_head_en`/`note_head_ko`,
and the notes section of the page renders those fields directly. So if you re-check SOXL's
daily change and satisfy yourself it is real, set `confirmed: true` **and** rewrite the note
and its heading to say what you checked and what you concluded. If you cannot confirm it,
set `confirmed: false` and say so plainly, and make sure the board's `day_en`/`day_ko`
carry an explicit unconfirmed marker.

What is not acceptable is changing one and not the other — a board that reads "flat" over a
note that says "I could not confirm this" makes the page argue with itself, and that costs
more trust than the number is worth.

## Before you finish

- Confirm both JSON files parse.
- Confirm every English field has a Korean counterpart.
- Confirm every tracker entry has a date and a source URL.
- Set `"as_of"`, `"generated"`, and `"mode": "weekend"` in `data/market.json`.
- Print a 5-line summary: the week's moves, what you could not confirm, what is scheduled
  next week, and how many tracker items you added.
