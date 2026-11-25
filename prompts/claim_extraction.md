# Prompt: claim extraction

**Job:** turn an essay into atomic, checkable claims, without changing the author's wording.

```
You split an essay into atomic claims.

Rules:
- One claim = one assertion that could be true or false on its own.
- Copy the sentence text EXACTLY. Do not fix grammar, do not shorten, do not merge sentences.
- If a sentence contains two independent assertions joined by "and" or a semicolon, split it at
  that boundary, and keep both fragments verbatim (they may overlap by a few words).
- Keep the citation marker, e.g. "(Liu et al., 2023)", inside the claim text.
- Ignore headings, captions, and reference lists.
- Do not add claims that are not in the text. Do not reorder.

Return JSON only:
{ "claims": [ { "id": "C01", "text": "<verbatim sentence>" } ] }
```

**Check before you ship it:** run it on `data/essay_draft.md` and confirm you get 12 claims whose
text matches `data/answer_key.json`. If extraction drifts, every downstream number is wrong, so
this is the first thing to stabilise.

**A4 note:** record what the model got wrong on the first attempt (we expect the C09 sentence with
nested quotes to break), what a human changed, and why.
