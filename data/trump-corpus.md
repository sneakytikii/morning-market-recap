# Trump-on-companies — researched corpus (as of 2026-08-01)

Ground truth for the tracker. **Nothing enters the dashboard unless it is in here with a
source.** Verbatim quotes are marked `VERBATIM`; everything else is reported summary and
must be worded in the page as reporting, never inside quote marks.

---

## 1. Dell — the reference case

**2026-07-06 · White House, first-ever presidential opening-bell event**
`VERBATIM`: **"Go out and buy a Dell computer."**
Said at an Oval Office ceremony marking the launch of "Trump Accounts" (tax-advantaged
investment accounts for under-18s). Directed at founder Michael Dell and Susan Dell, who
have pledged $6bn+ to the Trump Accounts programme.
Market: DELL rose **as much as 10% intraday**, high near **$429.35**, adding about
**$15.8bn** in market value — then gave much of it back and **closed up 4.43%**.

> **Corrected 2026-08-01.** The first draft of this file said "rose 7%+ on the day", which
> is the headline figure several outlets used for the intraday move. The *close* was
> +4.43%. Reporting the intraday peak as the day's move is exactly the misleading-precision
> error this section exists to avoid — always separate "touched" from "closed".
Sources: CNBC 2026-07-06 `https://www.cnbc.com/2026/07/06/trump-opening-bell-ceo-nyse-nasdaq-stocks-accounts.html`,
Quartz `https://qz.com/trump-dell-stock-endorsement-opening-bell-trump-accounts-070626`

**2026-02-10 → 2026-02-19 · the sequence that drew scrutiny**
Bought **$1m–$5m** of Dell shares on **2026-02-10**. Nine days later, on **2026-02-19**,
told a crowd in Rome, Georgia to "go out and buy a Dell computer". Repeated the line at a
May White House event, which lifted the shares to a record.
Context: DELL up ~227% year-to-date, helped by AI data-centre demand.
Reported as "Trump's most controversial trade of 2026".
Source: Yahoo Finance `https://finance.yahoo.com/markets/stocks/articles/trump-most-controversial-trade-2026-134434581.html`

---

## 2. The CNN investigation — 2026-07-16

Found Trump made **at least 44 stock purchases across 21 companies** within a week
*before* posting favourably about them on Truth Social. At times he announced government
actions that could benefit companies he had just invested in. Methodology: AI comparison of
Truth Social posts against his annual financial disclosures.
Companies named in coverage: **Nvidia, Tesla, Apple, GE Aerospace, Eli Lilly, American
Eagle Outfitters**. Palantir purchase of **$247,008–$630,000** in Q1 2026.
Source: CNN 2026-07-16 `https://www.cnn.com/2026/07/16/us/trump-stock-sales-truth-social-invs-vis`
(direct fetch returns HTTP 451 from here; corroborated via Yahoo News and Irish Star syndication)

**2026-07-23 · Tesla — DOES NOT SHIP.** Reported as one of his largest single Tesla
purchases of the year (**$500,000–$1,000,000**), with a next-day Truth Social post
de-escalating the Musk feud. **No source dated on or after 2026-07-23 could be found** —
the date came from a blended search summary, and the CNN piece it was attributed to is
dated 2026-07-16, a week before. Per rule 2 it stays out until a real source exists.

---

## 3. Nvidia / chips — the one that actually moves Daniel's five

This is the highest-relevance thread: NVDA is held outright, sits inside SPX and QQQ, and
is levered 3x inside SOXL. Chip-export policy is the dominant policy variable for four of
the five positions.

- **2025-04** — administration halts advanced AI chip exports to China.
- **2025-07** — reverses course; Nvidia assured it can resume H20 shipments.
- **2025-12** — Trump says the US will permit Nvidia to ship **H200** chips to approved
  customers in China, ending the export ban, in exchange for a **25% fee** collected when
  parts arrive in the US for security review before re-export.
- **2026-01-13** — Commerce/BIS final rule moves H200- and AMD MI325X-equivalent chips from
  **"presumption of denial"** to **"case-by-case review"**.
- **2026-01-14/15** — proclamation imposing a **25% tariff** on a narrow range of advanced
  computing chips incl. Nvidia H200 and AMD MI325X, effective **2026-01-15**. Chips
  supporting US supply-chain buildout are **exempt** — TSMC's $165bn Arizona investment
  exempts it.
- **2026-06-01** — US states the ban on AI chip shipments applies to Chinese firms
  *outside* China too.

Sources: Tom's Hardware, CNN Business 2026-01-14 `https://www.cnn.com/2026/01/14/tech/chip-tariff-trump`,
Seeking Alpha, White House fact sheet
`https://www.whitehouse.gov/fact-sheets/2026/01/fact-sheet-president-donald-j-trump-takes-action-on-certain-advanced-computing-chips-to-protect-americas-economic-and-national-security/`,
Al Jazeera 2026-06-01, Mayer Brown 2026-01

---

## 4. Why a tracker is a rational thing to build — Truth API

Trump Media pitched **Truth API**, a paid real-time data feed giving banks and trading
firms faster access to Truth Social posts — from the President **and nine other top
accounts**. Top speed tier pitched at **$100,000 per month**, falling to **$60,000** on a
three-year commitment. Aimed at high-frequency and algorithmic desks; delivery advertised
in milliseconds. Expected to go live for institutional customers on **2026-08-01**.

Senators Warren and Schiff asked the SEC on **2026-07-29** to examine whether selling early
access to the President's posts breaks the law.

**Wording caution:** it was *pitched* and only now going live — write "trading firms are
being asked for up to $100,000 a month", never "banks pay $100,000 a month".
Sources: CNBC 2026-07-18 `https://www.cnbc.com/2026/07/18/trump-media-pitched-100000/month-fee-for-fastest-feed-of-trump-posts.html`,
Al Jazeera 2026-07-29 `https://www.aljazeera.com/economy/2026/7/29/democrat-senators-ask-us-sec-to-probe-trump-medias-fast-feed-sale`
DJT rallied ~**48–50%** off its all-time low of **$6.96** (2026-06-26) on the news;
Trump's net worth rose about **$600m** in under a month. DJT still down ~46% YTD from
~$13.77 at the start of 2026.
Sources: Forbes 2026-07-30 `https://www.forbes.com/sites/antoniopequenoiv/2026/07/30/trump-medias-nearly-50-rally-adds-600-million-to-presidents-net-worth/`,
Yahoo Finance, Benzinga

**The point for the page:** trading firms are being asked for six figures a month for a
latency edge on these posts. That is the plainest possible evidence that what he says about individual
companies moves their share price — which is exactly why a private investor might want a
plain-English log of it.

---

## Editorial rules for this section — non-negotiable

1. **Verbatim or nothing.** A sentence in quote marks must be a real, sourced quote. If
   only a paraphrase is available, write it as reporting outside quote marks.
2. **Every entry carries a date and a working source link.**
3. **Market reaction is a measured number, never an inference.** "Shares rose 7% that day"
   is reportable. "Because he said it" is not, unless the source draws the link.
4. **Neutral voice.** Report what was said, when, and what the price did. No praise, no
   mockery, no partisan framing. The reader draws their own conclusion.
5. **The pixel character never speaks words attributed to the real person.** It is a
   section marker and a guide. Any speech bubble it shows is dashboard voice ("3 new
   items this week") or a clearly-attributed verbatim quote with its source visible.
6. **Scope is every company, not the portfolio.** This is a record of what the President
   says about business — any company, any industry, any investment. The Dell endorsement
   and the "do magnets" line touch none of the five positions and are among the most
   useful entries here. Never use relevance to the five as a filter for what to record;
   it is a badge on an entry, not a gate in front of it.

7. **Order is strictly reverse-chronological, and relevance is shown, not sorted.**
   An earlier draft of this rule said relevant items should be surfaced first. The
   shipped design does it differently and deliberately: a dated record whose dates are
   out of order stops being a record, and a reader who spots that stops trusting it. So
   entries run newest-first, and relevance is carried by two visible devices instead —
   the per-entry "Touches NVDA, SOXL, QQQ, SPX" badge, and the footprint strip at the
   top that lights the affected positions. The reading line names the most recent
   entry that touches anything, so the relevance question is answered before the first
   entry is read.
