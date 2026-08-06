You are doing a midday sweep of the record section only. This runs unattended while the
US market is open. Nobody is watching and there is no one to ask.

WORKING DIRECTORY: the repository root — the directory you are already in.
All paths below are relative to it.

## Your job

Two things, and nothing else:

1. Sweep the record and update `data/trump.json` (the rules below).
2. Rewrite exactly four keys in `data/market.json` — the top-level `today_en`,
   `today_ko`, `today_date` (today's ISO date), and `pancho_pm` — with how TODAY's
   session is actually going (see "The Today block" and "Pancho's afternoon line").
   Touch nothing else in that file: the morning job owns the market numbers.

Do **not** touch `dashboard.html`, `dashboard.template.html`, anything in `site/`, or
any other file.

## The Today block — the afternoon rewrite

The page opens with a **Today** block whose prose the morning run wrote before the open
(the setup, what's scheduled). You run mid-session, so replace it with the story so far,
one paragraph, 3-5 short sentences, plain English a non-technical 65-year-old follows:

1. The session's character so far, from sources published TODAY ("a quiet day", "tech
   is giving back part of yesterday's jump").
2. What the reader's five are doing — the chip fund SOXL, Nvidia, the Nasdaq-100 fund
   QQQ, Costco — with rounded intraday figures from your research, worded as words
   ("up about 3%"), never bare signs. If you cannot source an intraday figure, name
   the direction only.
3. One line on what is still ahead today or next ("the jobs report lands Friday").

## Pancho's afternoon line

Pancho, the little dog on the page, speaks from a ledger of lines that each carry an
expiry, so he can never repeat a fact after it stops being true. The morning run wrote
`pancho_am`; you write `pancho_pm`, his afternoon remark:

```json
"pancho_pm": {"date": "<today ISO>", "pos": "", "en": "...", "ko": "..."}
```

- `pos` is `""` for the whole market, or one of `spx`/`qqq`/`nvda`/`soxl`/`cost` to
  attach the line to that position (he says it when that row is tapped).
- **Plain spoken English, one or two short sentences, under 120 characters.** Korean
  under 65 characters — it is a speech bubble, not a paragraph.
- **No HTML at all**, not even `<b>`: the bubble is plain text and a tag would render as
  literal angle brackets. No emojis, no markdown.
- A friendly dog explaining one thing to an older man, never an analyst, never advice.
- Say what the afternoon actually showed, not what the numbers already say on their own.

Good: "The morning's drop mostly came back after lunch."
Good: "Nvidia carried the whole thing today. Everything else drifted."
Bad: "NVDA +3.43% on SpaceX news." (a data dump the board already shows)

## The Today block wording

Inline `<b>` for key names/numbers, no other tags. Never predict. Clock times, if any,
in **Pacific Time**, plainly labeled ("5:30 in the morning Pacific time" / "서부 시각
오전 5시 30분") — the reader is on the US West Coast; never a bare New York time.
`today_ko` says the same thing in natural Korean, polite newspaper style, same `<b>`
placements. A live
price line under this prose updates itself — do not mention live prices or quote
exact-to-the-cent prices; rounded moves are what age gracefully.

## Read these first

1. `data/trump.json` — what is already on the record, and the exact shape to keep.
2. `data/trump-corpus.md` — the editorial rules. They are binding, not advisory.

## What to look for

Statements or actions from **the last 24 hours** about **companies, industries or
investments of any kind — not only the five positions the page tracks.** That breadth is
the point of the section: it is a record of what the President says about business.

In scope:

- naming a company — "go out and buy a Dell computer"
- telling an audience what to invest in or make — "I'll tell you how to make money: do magnets"
- praising or attacking a named firm
- announcing a company's pledge, investment or donation
- policy that moves a named sector: tariffs, export rules, subsidies, contracts
- disclosed trades in individual stocks
- anything involving a business he or his family holds a stake in

**Do not filter by relevance to SPX / QQQ / NVDA / SOXL / COST.** Record it, then set
`touches` to whichever of the five it genuinely reaches — very often none. The Dell
endorsement and the magnets line reach none of the five and are among the most useful
entries on the record. Relevance is a badge on an entry, never a gate in front of it.

Chip-export policy is still worth flagging when it appears, because Nvidia is held
outright, sits inside SPX and QQQ, and is levered 3× inside SOXL — so one export rule
reaches four of the five at once. That is a reason to set `touches` carefully, not a
reason to ignore everything else.

## The rules — these are what make this section worth having

1. **Verbatim or nothing.** A sentence inside quote marks must be a real, sourced,
   word-for-word quote. If you only have a paraphrase, write it as reporting *outside*
   quote marks, in the `text_en` / `text_ko` fields, and leave `quote` empty.
2. **Every entry carries a date and a working source URL.** No exceptions.
3. **Market reaction is a measured number, never an asserted cause.** "Shares rose 7%
   that day" is reportable. "Because he said it" is not, unless the source itself draws
   the link — and even then, attribute it.
4. **Separate "touched" from "closed."** If a stock spiked intraday and gave it back,
   say both. Reporting an intraday peak as the day's move is the single easiest way to
   mislead here, and it has already happened once on this page.
5. **Strictly neutral.** No praise, no mockery, no partisan framing, no loaded verbs.
   Report what was said, when, and what the price did. The reader draws their own
   conclusion. A reader who admires the man and a reader who does not should both find it
   fair.
6. **Nothing new is the correct answer most days.** Update `checked` / `checked_en` /
   `checked_ko` to today and change nothing else. **Do not pad, do not reach, do not
   promote something marginal to fill space.** An empty sweep that says so honestly is
   more valuable than a padded one.

## Shape

Match the existing entries exactly. Every entry needs: `date` (ISO), `date_en`, `date_ko`,
`verb` (one of `said` / `did` / `bought`), `headline`, `company_en`, `company_ko`,
`ticker`, `verbatim`, `quote` (English verbatim, or empty), `quote_ko` (Korean rendering
of the quote, or empty), `text_en`, `text_ko`, `reaction_en`, `reaction_ko`,
`reaction_dir` (`up` / `down` / empty), `touches` (array from spx/qqq/nvda/soxl/cost, or
empty), `source_url`, `source_en`, `source_ko`.

Do not write `reading_en`, `reading_ko`, `verb_en`, `verb_ko`, `touches_en`, `touches_ko`
or `footprint` — those are derived at build time and anything you put there is discarded.

Keep the newest **12** entries; drop the oldest beyond that.

Korean must say the same thing as the English — same numbers, same hedges, same caveats —
in natural Korean at a level a non-technical 65-year-old reads comfortably. Ticker symbols
stay in Latin script.

## Before you finish

- Confirm `data/trump.json` parses.
- Confirm every entry has a date and a source URL.
- Confirm every English field has its Korean counterpart.
- Print two lines: how many entries you added, and how many touch the five holdings.
