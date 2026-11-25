# Devpost answers — fill these in

Five questions, judged against the rubric. Write plainly; judges read a lot of these.
Paste the tables from `EVIDENCE.md` — do not retype numbers.

---

### 1. Who is it for, and why would they use it?

<One paragraph: the user, the moment, the cost of the current approach. Then: "Evidence: <classmate
quote / TA comment / published source with link>." Then the use example from `EVIDENCE.md` §V1.>

### 2. What did your team build during the hackathon?

<New project, built 25–28 Nov. List: PDF ingestion with page numbers, claim extraction, retrieval,
the quote-or-abstain verifier, the string-match guard, the side-by-side UI, the eval harness.
Then: "Third-party: <model API>, <Prune gateway>, <PDF library>. Everything else is ours.">

### 3. How did you use AI?

**AI in the finished project.** <Model name and job. Why this model (A1 table). The quote-or-abstain
design decision and what it changed (A2 numbers). How you assessed quality and what the limits are
(A3 table + the honest weakness).>

**AI during development.** <Tool name + the specific contribution from the A4 table, what the human
check found, and the keep/change/reject decision.>

**Sponsor tools.** <"We routed model calls through Prune, which capped spend and cached repeat
calls; it cut the cost of our repeat test to zero." — or delete this line.>

### 4. How do people access it, and what results does it achieve?

<Repo link, quickstart, requirements (Python, an API key or our hosted demo, internet for model
calls). Then the R2 table verbatim. Then D1–D4 in four short bullets — one design decision each.>

### 5. Limitations, and what happens when things go wrong?

<Known issues list: tables/figures, scanned PDFs, synthesis across many sources, no .docx, no
accounts. Then the R3 table: three failures, each with cause → detection → what the user sees →
what was preserved. Label anything simulated.>

---

## Final checks before you hit submit

- [ ] Video is 2–4 minutes and the link opens logged out
- [ ] Repo is public and the quickstart matches reality
- [ ] No keys, no `.env`, no third-party PDFs committed
- [ ] Team roster complete (up to 6)
- [ ] Everyone submitted the participant form
- [ ] "Best Use of Prune" selected only if the project genuinely uses it
- [ ] Every `<...>` in this file and in `EVIDENCE.md` is gone
