# Product

## Register

product

## Users

One person: Daniel, checking five holdings — SPX, QQQ, NVDA, SOXL, COST — usually at a weekend or before the open, on a laptop, sometimes a phone.

The binding constraint is a second audience: **the page must be readable by a non-technical 65-year-old**. That is not a nice-to-have added at the end; it is the design brief. It rules out finance jargon, small type, colour-only meaning, dense terminal aesthetics, and any interaction that has to be learned.

The job to be done: *"What happened to my five, what does it mean, and what should I be watching?"* — answered in under a minute, without scrolling through an essay.

## Product Purpose

A weekend/morning recap of five positions. It exists because the raw numbers are easy to find and the *interpretation* is not — specifically the two things a quote screen will never tell you:

1. **SOXL is structurally dangerous.** A 3× daily-reset fund bleeds value in choppy markets regardless of direction. It cost 57% in a month when the market was flat.
2. **Four of the five are the same bet.** NVDA is owned outright, inside SPX, inside QQQ, and levered 3× in SOXL. They fall together.

Success is Daniel closing the page knowing what moved, what it means, and the next dated catalyst — and never being misled by a number.

## Brand Personality

**Considered, plain-spoken, honest.** The voice of a good analyst talking to a smart friend who does not work in finance: no jargon, no hype, no false confidence. It says "nobody can tell you where these go next week" and means it.

Emotionally the page should feel **calm and authoritative** — the opposite of a trading app trying to generate activity. It never urges a trade.

## Anti-references

- **Trading-app dashboards** (Robinhood, WeBull): gamified, urgent, engineered to provoke transactions.
- **Bloomberg terminal / "hacker" finance UI**: dark, dense, mono-everything, tiny type. Looks expert; fails the 65-year-old test completely.
- **Crypto-dashboard maximalism**: neon gradients, glow, glass, animated tickers.
- **The AI-generated default**: cream/sand body background with a serif display and a terracotta accent; tiny uppercase tracked eyebrows above every section; identical rounded card grids; coloured side-stripe borders.
- **Hedged-to-uselessness research-speak**: "we remain constructive pending further clarity."

## Design Principles

1. **Plain English is a design constraint, not a copy choice.** If a term needs finance training, it is rewritten or explained inline. "Bull/bear" → "reasons it could go up / down". Jargon in the UI is a bug.
2. **Honesty is visible.** Derived figures are marked, unconfirmed figures say so, and the page never implies a forecast it cannot support. The SOXL caveat and the "these are not predictions" note are features, not disclaimers.
3. **Comparison without scrolling.** All five are legible together; detail swaps in place rather than stacking. Any layout that forces scrolling to compare two positions has failed.
4. **Meaning never rides on colour alone.** Every up/down carries an arrow and a word as well as a hue.
5. **The risk gets the loudest voice.** The two things most likely to hurt — SOXL's decay and the four-way overlap — are given more visual weight than any price.

## Accessibility & Inclusion

- **WCAG 2.1 AA minimum**, verified by computation, in **both** light and dark themes. Every text/background pair checked — this page previously failed on muted greys and was fixed.
- **18px base type floor**; no label below 13px. Prices and changes set larger still.
- **No colour-only meaning**: ▲/▼ arrows plus wording accompany every semantic colour.
- **No horizontal scrolling at any viewport.** The board restacks into labelled rows on narrow screens rather than scrolling sideways.
- **Large tap targets**: tabs ≥56px tall; controls ≥24px with ≥44px effective hit areas.
- **Full keyboard operation** with a visible focus ring; the tablist follows the ARIA authoring pattern including Home/End.
- **`prefers-reduced-motion` fully respected** — the mascot's animation stops and text still updates.
