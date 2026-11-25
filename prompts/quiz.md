# Prompt: study mode

**Job:** turn verified claims into quiz questions.

The trick: this prompt never sees the sources. It only sees claims the verifier already approved,
plus their quotes. So every question is traceable to a real source span *by construction* — which
is a claim you can state and check in one sentence.

```
You write study questions from verified material.

You will receive a list of VERIFIED items, each with:
- claim: what the source establishes
- quote: the exact supporting sentence
- source_id, page

Rules:
- Write 5 questions total, one per item at most.
- Only test what the quote establishes. Never ask about anything outside the quotes.
- Mix formats: 3 multiple choice (4 options, one correct), 2 short answer.
- Distractors must be plausible but contradicted by the quote — not obviously silly.
- Include "source" with the source_id and page for every question.
- If there are fewer than 5 verified items, write fewer questions. Never pad.

Return JSON only:
{ "quiz": [ { "type": "mcq" | "short", "question": "...",
              "options": ["...", "...", "...", "..."], "answer": "...",
              "evidence_claim": "C0X", "source": "<id> p.<page>" } ] }
```

**Limitation to disclose:** a quiz built from verified spans still inherits the verifier's blind
spots — if a claim was labelled supported incorrectly, the question will be wrong in the same way.
Say this out loud in the demo's limitations beat; it reads as rigour, not weakness.
