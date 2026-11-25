# Demo script — 3:00

Screen recording, one real take per beat, no editing tricks needed. Judges score clarity, not
production. Every timestamp is a target, not a rule.

| Time | On screen | Say |
|---|---|---|
| 0:00–0:15 | Title card: "Exhibit — [citation needed]" → the essay with two highlighted bad citations | "A citation that doesn't exist is the cheapest mistake in student writing — and the hardest to see. Exhibit checks every claim against the source." |
| 0:15–0:25 | Who it's for | "For students writing cited essays from PDFs: 12 claims, two papers, one paste." |
| 0:25–1:10 | **Main task, unbroken.** Paste `essay_draft.md` → drag `2307.03172.pdf` and `2305.14627.pdf` → click Check → verdict chips fill in | Narrate only what matters: "Twelve claims. Seven supported, two partial, two unsupported, one it won't judge." |
| 1:10–1:40 | Click C10 (the 98.1% claim) → source pane shows no highlight → panel says "no passage supports this" | "This sentence looks perfectly cited. Nothing in the paper says it. Exhibit refuses to invent support." |
| 1:40–2:00 | Click C08 → quote appears with page → "partial" reason | "Here the source says 50% of the time, so 'most cases' is an overstatement. Partial, not supported." |
| 2:00–2:25 | One slide: the two-step guard (quote required → string match → downgrade) | "The model can't just assert support: it must return a verbatim span, and that span is string-matched against the page. A paraphrase is downgraded." |
| 2:25–2:45 | `eval/results.md` on screen | "Twelve labelled claims: X correct, Y fabricated quotes caught. It struggles with tables and with claims that span two paragraphs — our C__ case." |
| 2:45–3:00 | Scanned PDF rejected, earlier sources still loaded | "Bad input is detected before the model sees it, and nothing already checked is lost." |

## What must appear somewhere in the video

- [ ] The intended user, in one sentence
- [ ] The main task from start to finish (R1) — this is most of the runtime
- [ ] AI's specific job (A2), not just "we use AI"
- [ ] One caught fabrication (the money shot)
- [ ] What you built during the event
- [ ] Limitations, stated plainly (scanned pages, tables, long docs)
- [ ] If you used Prune: one sentence + one screenshot of the spend/cost view

## Recording notes

- 1080p, system audio off, your voice over it.
- Zoom the browser to 110–125% so text is legible on a phone.
- Prepare the essay and both PDFs *before* recording; a fumbled file picker reads as broken.
- If the verifier takes 3s/claim, either speed the clip up and label it ("2× speed"), or cut to
  the finished list — do not leave dead air.
