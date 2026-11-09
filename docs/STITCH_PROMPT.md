# Stitch prompt – SawalSetu frontend

Paste the block below into Google Stitch (stitch.withgoogle.com) as the screen prompt. The
second block is a follow-up prompt for the mobile layout. The design tokens at the bottom match
what the React app in `frontend/` implements, so Stitch output and the code stay consistent.

---

## Primary prompt (desktop, 1440 × 900)

```
Design a desktop web app screen called "SawalSetu" – an AI business-insights assistant for an
Indian pharma & FMCG distributor. It answers questions about the company's accounting data
(sales invoices, purchases, customers, suppliers, receivables) that is synced from MargBooks,
a GST billing software. The feel should be "a beautifully typeset ledger that talks back":
calm, trustworthy, editorial, premium. Not a generic dark SaaS dashboard and not a chatbot
bubble UI.

LAYOUT – three columns on a warm off-white paper background (#F6F1E7):

1. LEFT RAIL (280px, slightly darker paper #EFE8DA, hairline right border):
   - Wordmark "SawalSetu" in a high-contrast serif (Fraunces), with a tiny subtitle
     "Ask your books" in a small caps sans.
   - A "Data source" card: MargBooks logo placeholder, status pill "Synced 4 min ago" in deep
     emerald, a small ledger-style list with dotted leader lines:
     Sales invoices ........ 1,284
     Purchase bills ........ 312
     Parties ............... 37
     Items ................. 50
     and a quiet secondary button "Sync now" with a refresh icon.
   - "Ask about" section: 6 suggested questions as stacked pill-shaped chips with a thin
     emerald border, e.g. "Top customers by udhaar", "Sales last month vs previous",
     "Overdue > 60 days", "Best margin items", "Amazon & Flipkart orders", "Business snapshot".
   - Footer: small text "Shree Balaji Distributors · FY 2026-27" and a settings gear.

2. CENTER – CONVERSATION (fluid, max 760px wide, centered):
   - Top: a thin header with the company name on the left and a segmented control
     "Answers | Evidence" on the right (desktop shows both so it's just a label).
   - Messages are NOT chat bubbles. User questions appear as a serif italic line with a thin
     left rule in saffron (#E0862B). Assistant answers appear as typeset editorial text on the
     paper, with a small emerald "SawalSetu" caption and timestamp above.
   - The assistant answer example should contain: a one-line lead with a big number
     (₹18.4 L in Fraunces, tabular figures), two short bullets, and a compact 3-row table
     (Customer | Outstanding | Overdue) with hairline rules only, no zebra striping.
   - Citations appear inline as small square superscript chips [1] [2] in emerald with a
     1px border; one chip is shown hovered with a tooltip preview of the source passage.
   - Bottom: a composer pinned to the bottom of the column: a rounded rectangle (16px radius)
     with a subtle inner shadow, placeholder "Ask anything about your books… e.g. kis party ka
     udhaar sabse zyada hai?", a left "+" attach icon, and a right circular emerald send button
     with an arrow-up icon. Under it, tiny helper text: "Answers are grounded in your MargBooks
     data · Claude".

3. RIGHT PANEL – EVIDENCE (360px, same paper, hairline left border):
   - Three KPI tiles in a row (each: label in small caps, value in Fraunces tabular numbers,
     delta in emerald or a muted red): "Sales MTD ₹12.6 L ▲ 8.2%", "Receivables ₹9.8 L",
     "Payables ₹4.1 L".
   - A 12-month sales vs purchases chart: two thin lines (emerald for sales, saffron for
     purchases), no gridlines except a dotted baseline, month labels in mono small caps.
   - "Sources for this answer" list: 4 cards, each with a numbered square chip, a kind tag
     ("Customer profile", "Sales invoice", "Receivables ageing"), a title, and 2 lines of
     passage text with the key numbers rendered in bold tabular figures. Cards have no shadow,
     just a 1px border that turns emerald on hover.

TYPOGRAPHY: Fraunces (variable serif) for the wordmark, big numbers and user questions;
Inter for UI and body; JetBrains Mono for bill numbers, dates and axis labels. Tabular lining
figures everywhere numbers appear.

COLOR: paper #F6F1E7, deeper paper #EFE8DA, ink #14201C, muted ink #5B6560, hairline
#D9D0BF, emerald #0F5C4A (primary), emerald tint #DDEDE6, saffron #E0862B (accent), red for
negatives #B3412E. Use color sparingly; the page should read mostly as ink on paper.

DETAILS: 8px grid, 12–16px radii, 1px hairlines instead of shadows, generous whitespace,
ledger-like dotted leaders in lists, status pills with a tiny dot. Icons: Lucide, 1.5px
stroke. Add a subtle paper grain texture at 3% opacity. No gradients, no glassmorphism,
no emoji.
```

## Follow-up prompt (mobile, 390 × 844)

```
Adapt the same SawalSetu design for mobile. Single column on paper background. Top bar with
the wordmark and a sync status dot. The conversation takes the full width; KPI tiles become a
horizontally scrollable row above the first answer. Sources collapse into a bottom sheet
opened by tapping a citation chip. The composer is pinned to the bottom with a safe-area
inset. Suggested questions appear as a horizontally scrolling chip row above the composer
when the thread is empty. Keep Fraunces for numbers and questions, Inter for UI.
```

## Tokens used by the React app

| Token            | Value     | Use                                  |
| ---------------- | --------- | ------------------------------------ |
| `--paper`        | `#F6F1E7` | page background                      |
| `--paper-2`      | `#EFE8DA` | rails, cards                         |
| `--ink`          | `#14201C` | primary text                         |
| `--ink-muted`    | `#5B6560` | secondary text                       |
| `--hairline`     | `#D9D0BF` | borders, rules                       |
| `--emerald`      | `#0F5C4A` | primary actions, citations, positive |
| `--emerald-tint` | `#DDEDE6` | chip backgrounds, hover              |
| `--saffron`      | `#E0862B` | accent rule, purchases line          |
| `--red`          | `#B3412E` | negatives, errors                    |
| Display font     | Fraunces  | wordmark, numbers, questions         |
| UI font          | Inter     | body, controls                       |
| Mono font        | JetBrains Mono | bill numbers, dates, axes       |
