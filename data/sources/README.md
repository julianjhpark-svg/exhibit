# Test sources

Two open-access arXiv papers, chosen because their abstracts contain claims we can check by eye
and because they are about citation quality and long context — the same problem Exhibit solves.

| id | arXiv | Paper |
|---|---|---|
| `liu2023` | 2307.03172 | Liu et al. — *Lost in the Middle: How Language Models Use Long Contexts* (TACL 2023) |
| `gao2023` | 2305.14627 | Gao et al. — *Enabling Large Language Models to Generate Text with Citations* (EMNLP 2023) |

## Get them

```bash
python scripts/fetch_sources.py
```

PDFs land here and are gitignored. **Do not commit third-party PDFs** to the public repo; link to
arXiv instead and check each paper's license before redistributing.

## Extra material to collect (optional, for the demanding R2 case)

- One ~40-page PDF so retrieval has to work across distance (a thesis or a long report).
- One scanned PDF with no text layer — this is failure case #1, so keep it nasty.
