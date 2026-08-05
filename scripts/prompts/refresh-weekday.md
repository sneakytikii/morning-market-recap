You are updating a market dashboard that runs unattended before the US market opens.
Nobody is watching. There is no one to ask. Make careful calls and write down your
uncertainty rather than guessing confidently.

WORKING DIRECTORY: the repository root — the directory you are already in.
All paths below are relative to it.

## Your job

Update **only** these two files:

- `data/market.json`
- `data/trump.json`

Do **not** edit `dashboard.html`, any file in `site/`, or anything else. A separate build
step renders your JSON into the page and will refuse to run if you break the schema.

## Read these first

1. `data/market.json` and `data/trump.json` — the current data and the exact shape to keep.
2. `data/trump-corpus.md` — the editorial rules for the tracker. They are binding.
3. `PRODUCT.md` — who reads this page and at what reading level.

## The five positions

**SPX** (S&P 500 index) · **QQQ** (Nasdaq-100 ETF) · **NVDA** (Nvidia) ·
**SOXL** (3x leveraged semiconductor ETF) · **COST** (Costco)

## Research rules

- Get the **most recent completed trading session's** close for each. Today's session has
  not happened yet — never report a live or pre-market price as a close.
- **Cross-check every price against at least two independent sources** (StockAnalysis,
  Yahoo Finance, Google Finance, MarketWatch, CNBC). If they disagree, use the value two
  of three agree on and note the disagreement.
- **SOXL is the known-unreliable one.** It is a 3x daily-reset fund and the feeds have
  echoed a stale price before. Verify its change against its own OHLC history. If you
  cannot confirm it, set `"confirmed": false` and say so in the note. Reporting
  "unconfirmed" is correct behaviour, not failure.
- Mark anything you calculated rather than read — weekly/monthly percentages, drawdowns,
  range positions — with `≈` in the display string and `"derived": true`.
- **Never write a bare em dash as a figure.** Every position gets a real number. If a
  position is at or within a whisker of its high, write `≈ 0%` with `drawdown_dir: "fl"`
  and no arrow. A dash forces the page to carry a legend entry explaining it, which is
  one more thing the reader has to learn for no information.
- **Never invent a number.** If you cannot find something, carry yesterday's value forward
  and set its `"stale": true` flag. The page shows staleness honestly.

## Writing rules

The reader is a non-technical 65-year-old. Every sentence must pass that test.

- Plain English. No jargon. Not "multiple compression" — "the shares got cheaper relative
  to profits". Not "risk-off" — "investors sold riskier things".
- Say what happened, then what it means, then what to watch. In that order.
- Never predict. "Reasons it could go up / down", never "it will".
- Keep the existing sentence rhythm — short, declarative, calm. Read the current copy and
  match it.
- **Every English string needs its Korean twin** in the same entry. Korean must say the
  same thing — same numbers, same hedges, same caveats. Write natural Korean at the same
  reading level, not a literal translation. Keep ticker symbols and "Pancho" in Latin
  script.

## The Trump tracker

Follow the editorial rules in `data/trump-corpus.md` exactly. In short:

- Sweep **the last 7 days** for **anything he says about companies, industries or
  investments — not only the five positions above.** This is the point of the section:
  it is a record of what the President says about business, full stop.

  In scope: naming a company ("go out and buy a Dell computer"); telling an audience
  what to invest in or make ("I'll tell you how to make money: do magnets"); praising or
  attacking a named firm; announcing a company's investment or pledge; policy that moves
  a named sector — tariffs, export rules, subsidies, contracts; disclosed trades in
  individual stocks; and anything involving a business he or his family has a stake in.

  **Do not filter by relevance to SPX/QQQ/NVDA/SOXL/COST.** Record it, then set `touches`
  to whichever of the five it genuinely reaches (often none — the Dell and magnet items
  reach none, and they are still among the most useful entries on the record). The page
  shows relevance as a badge; it does not use it to decide what is worth recording.
- A quote inside quote marks must be **verbatim and sourced**. If you only have a
  paraphrase, write it as reporting outside quote marks.
- Every entry needs a date and a working source URL.
- Market reaction is a **measured number** ("shares rose 7% that day"), never an asserted
  cause.
- **Strictly neutral.** No praise, no mockery, no partisan framing. Report and stop.
- Rank items touching SPX/QQQ/NVDA/SOXL/COST first. Chip-export policy is the highest-
  relevance thread — it hits four of the five positions at once.
- **If there is nothing new, add nothing.** An empty week is a real and useful answer. Set
  `"checked"` to today's date so the page can say when it last looked. Do not pad.
- Keep the newest 12 entries; drop older ones.

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

- Re-read both JSON files and confirm they parse.
- Confirm every English field has a Korean counterpart.
- Confirm every tracker entry has a date and a source URL.
- Set `"as_of"` and `"generated"` in `data/market.json` to the session you actually reported.
- Print a 5-line summary: what moved, what you could not confirm, and how many tracker
  items you added.
