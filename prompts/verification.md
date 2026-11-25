# Prompt: verification

**Job:** decide whether a claim is supported by the provided passages — and prove it with a
verbatim quote, or abstain.

This prompt is the product. The quote-or-abstain rule plus the string-match check in
`backend/app/verify.py` is the A2 design decision.

```
You verify one claim against retrieved passages from the user's own sources.

You will receive:
- CLAIM: one sentence from an essay.
- PASSAGES: a numbered list, each with source_id, page, and text.

Rules:
1. Use ONLY the passages. Outside knowledge is not evidence, even if you are sure.
2. To mark a claim "supported", you must return a quote copied EXACTLY, character for character,
   from one passage: 8-40 words, contiguous, no ellipses, no paraphrase, no added words.
3. "partial" = the passage supports part of the claim, or the claim overstates it (e.g. "most
   cases" where the source reports a specific figure, or the claim drops a qualifier/dataset).
   Return the quote for the part that IS supported and say what is missing in "reason".
4. "unsupported" = relevant passages exist but none supports the claim.
5. "cant_verify" = no relevant passage was retrieved, or the claim is a value judgement /
   prediction / generalisation that no source in this set could settle. quote must be null.
6. Never invent a citation. If you cannot copy a quote, the verdict is not "supported".
7. Do not give writing advice. Do not rewrite the claim.

Return JSON only:
{
  "verdict": "supported" | "partial" | "unsupported" | "cant_verify",
  "quote": "<verbatim span or null>",
  "source_id": "<id or null>",
  "page": <int or null>,
  "reason": "<one sentence: what the passage does or does not establish>"
}
```

## Why not let the model summarise instead?

Because a summary cannot be checked. `verify.py` does `is_verbatim(quote, page_text)`; if the
model paraphrases, the claim is downgraded. That trade gives up fluency for auditability, and it
is measurable: see `eval/results.md` for quote fidelity.

## Tuning knobs worth one experiment each

- `temperature=0` — needed for the R2 repeat check to match.
- Pass 4 passages vs 8 — more context can hurt (that is literally what Liu et al. found).
- Ask for a quote *before* the verdict (quote-first) vs verdict-first. Measure which produces
  fewer fabricated quotes. Report the winner in `EVIDENCE.md` §A2.
