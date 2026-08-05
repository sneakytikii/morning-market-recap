# Morning Market Recap

A plain-English recap of five positions — **SPX, QQQ, NVDA, SOXL, COST** — in English and
Korean, that rebuilds itself every weekday morning before the open and again on Saturday.

---

## Sending it to someone

Three ways, in order of how good the experience is for the person receiving it.

### 1. The single file — works right now, no setup

**`Market Recap.html`** in this folder. AirDrop it, text it, email it, put it in a shared
album. They tap it and it opens.

- No account, no login, no app.
- Works with no internet at all — the whole page, both languages, and both pixel
  characters are inside that one file. Nothing is fetched.
- On an iPad: tap the attachment → it opens in Safari. Share → **Add to Home Screen** for
  an icon.
- The catch: it is a snapshot. When the dashboard updates, they still have the old one
  unless you send it again.

### 2. A real link — one command, then it updates itself

```bash
./scripts/deploy.sh
```

Run this once. It creates a public GitHub repo, turns on GitHub Pages, and prints your
link — something like `https://sneakytikii.github.io/morning-market-recap/`.

After that the morning refresh publishes to it automatically, so **the link is always
current and you never send anything again**. Add to Home Screen gives a proper app icon.

I did not run this myself: creating a public web page is a publish-to-the-internet action
and you were asleep. Worth knowing before you run it — the page contains five ticker
symbols, public market data, and commentary. It has **no name, no holdings, no dollar
amounts, and no share counts** (I scanned for all of those). But it is public, so anyone
with the link can read it.

### 3. The Claude artifact

<https://claude.ai/code/artifact/3298e5ef-2251-463e-8ea4-f442b250205d> — best for you,
worst for a stranger, since sharing depends on a claude.ai account.

---

## Where this lives, and why not the Desktop

The project sits at `~/MarketRecap`, with a link on the Desktop pointing to it.

That is not cosmetic. macOS treats `~/Desktop`, `~/Documents` and `~/Downloads` as
privacy-protected: a background job started by `launchd` is refused access to them, with
a bare "Operation not permitted" and no prompt. The scheduled refresh ran on time for
three days from the Desktop and was turned away every single time, while the page quietly
kept showing stale numbers.

**Do not move this folder back into Desktop, Documents or Downloads.** If you want it
somewhere else, keep it outside those three, then update the three plists in
`~/Library/LaunchAgents/com.danielkim.marketrecap.*.plist` and the `WORKING DIRECTORY`
line in each of `scripts/prompts/refresh-*.md`.

A failed run now raises a macOS notification, and any run that finds the page more than
three days old raises one too — so this cannot fail quietly again.

## The morning refresh

Three scheduled jobs are installed and running:

| When | What it writes |
| --- | --- |
| **Weekdays 06:12** | The previous session's close, ~80 minutes before the 07:30 open |
| **Weekdays 13:07** | Mid-session sweep of the record section only — market numbers untouched |
| **Saturday 08:12** | The week, not the day — plus what's scheduled next week |

You asked for constant scraping of what the President says about companies. Truly
continuous would mean a crawler running against a paid feed — the thing trading desks are
being quoted $100,000 a month for. What's here instead is a **mid-session sweep plus a
morning sweep**, so a statement made during the day shows up within hours rather than
overnight. That is the honest version of "constantly" at this scale.

Each run: researches → writes `data/*.json` → rebuilds the page → publishes.

**If anything fails, the previous page stays up.** A stale correct page beats a fresh
broken one, and nobody is watching at 6am.

```bash
# see what happened
cat .state/logs/refresh-*.log | tail -40

# run one by hand
./scripts/refresh.sh weekday
./scripts/refresh.sh weekend
./scripts/refresh.sh tracker

# turn them off
launchctl unload ~/Library/LaunchAgents/com.danielkim.marketrecap.{weekday,tracker,weekend}.plist
```

Market holidays are skipped. The Mac has to be awake — asleep at 06:12 means the job runs
when it next wakes.

Only one refresh can run at a time; a second is turned away rather than allowed to edit the
same files. If a run dies without cleaning up, the lock is cleared automatically after 45
minutes, so a crash can never block the schedule permanently. The research step is capped
at 30 minutes and confined to `data/` — and the script checks afterwards that nothing
outside `data/` was touched.

---

## What the President said about companies

The tracked record, built only from `data/trump-corpus.md`. The rules are enforced by the
design, not by good intentions:

- **A quote in quote marks is verbatim and sourced.** It is set in serif with real quote
  marks; reported summaries are plain sans and *cannot* carry quote marks. The stylesheet
  makes the distinction, so it can't drift.
- **In Korean the quote stays in English** — a translated quote is no longer a quote —
  with the Korean rendering below it, labelled 번역, outside the marks.
- **Every entry has a date and a source link.**
- **Price moves are measured, never causal.** "Dell rose 7% that day" is reportable;
  "because he said it" is not.
- **Neutral.** No praise, no mockery, no partisan framing. It reports and stops.
- **The character never speaks.** It marks the section. No words are ever put in a real
  person's mouth.

The strip under the heading shows which of your five anything on the record actually
touches. Right now chip policy lights **four of five** — NVDA outright, inside SPX, inside
QQQ, and levered 3× in SOXL — while the whole Dell episode touches **none**. That contrast
is the point of the section.

---

## Editing it

```text
dashboard.template.html   ← EDIT THIS. Structure and copy.
data/*.json               ← EDIT THIS. Numbers and record entries.
dashboard.html            ← generated. Edits here are overwritten.
site/index.html           ← generated. The hosted build.
Market Recap.html         ← generated. The sendable build.
```

```bash
python3 scripts/build.py       # data + template -> dashboard.html
python3 scripts/wrap_site.py   # -> site/index.html and Market Recap.html
python3 scripts/sprite.py      # sprite -> data URIs + app icons
```

`build.py` **refuses to write** if a build would break English/Korean parity, drop the
charset tag, unbalance a tag, leak `<!DOCTYPE>` into the artifact build, make the sprite
ragged, or shrink the page by a third. That check is the reason an unattended 6am job is
safe to leave running.

### The characters

Both are 28×28 pixel grids in `data/*-sprite.json`, rendered to PNG data URIs at build
time and shown as `<img>`.

They used to be drawn to `<canvas>`, which is why **Pancho did not appear on the iPad**:
iOS purges canvas backing stores under memory pressure, the page drew each canvas exactly
once, and the only repaint path started with a reduced-motion early return — so with
Reduce Motion on he vanished permanently. An `<img>` cannot be purged, needs no timer, and
renders even if JavaScript never runs.

Always look at a sprite before shipping it:

```bash
python3 scripts/render_sprite.py data/pancho-sprite.json
```

A hand-typed pixel grid validates perfectly as code while being misshapen as art. This
project has already shipped one with slab ears and an off-centre row that every automated
check passed.
