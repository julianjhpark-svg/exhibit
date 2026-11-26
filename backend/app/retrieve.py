"""Lexical retrieval over source pages.

No embeddings, no vector DB, no numpy: two papers is ~200 chunks, and a 40-line BM25 finds the
abstract sentence fine. Zero dependencies means the demo cannot break because a wheel didn't
install — which matters more than the last few points of recall.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .extract import Page, passages_from

_TOKEN = re.compile(r"[a-z0-9]+")

STOP = {
    "the", "and", "for", "that", "this", "with", "from", "are", "was", "were", "have", "has",
    "not", "but", "they", "their", "which", "when", "what", "how", "why", "can", "does", "did",
    "into", "than", "then", "there", "these", "those", "such", "also", "may", "more", "most",
    "its", "our", "you", "his", "her", "she", "him", "one", "two", "all", "any", "use", "used",
    "using", "been", "being", "because", "about", "would", "could", "should", "will", "shall",
}


@dataclass(frozen=True)
class Chunk:
    source_id: str
    page: int
    text: str


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if len(t) > 2 and t not in STOP]


class Index:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self._tokens = [tokenize(c.text) for c in chunks]
        self._bm25 = _BM25(self._tokens) if chunks else None

    def top_k(self, query: str, k: int = 8) -> list[Chunk]:
        """Always returns up to k chunks; the verifier is responsible for abstaining."""
        if not self.chunks or self._bm25 is None:
            return self.chunks[:k]
        q = tokenize(query)
        if not q:
            return self.chunks[:k]
        scores = self._bm25.scores(q)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.chunks[i] for i in order]


class _BM25:
    """BM25Okapi, small enough to read. k1=1.5, b=0.75 are the usual defaults."""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75) -> None:
        self.docs = docs
        self.k1, self.b = k1, b
        self.n = len(docs)
        self.avgdl = sum(len(d) for d in docs) / self.n if self.n else 0.0
        df: Counter[str] = Counter()
        for doc in docs:
            df.update(set(doc))
        self.idf = {t: math.log(1 + (self.n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def scores(self, query: list[str]) -> list[float]:
        out: list[float] = []
        for doc in self.docs:
            counts = Counter(doc)
            dl = len(doc) or 1
            total = 0.0
            for term in query:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                idf = self.idf.get(term, 0.0)
                denom = tf + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
                total += idf * tf * (self.k1 + 1) / denom
            out.append(total)
        return out


def build_index(pages: dict[str, list[Page]]) -> Index:
    chunks: list[Chunk] = []
    for source_id, source_pages in pages.items():
        for raw in passages_from(source_pages, source_id):
            chunks.append(Chunk(source_id=raw["source_id"], page=raw["page"], text=raw["text"]))
    return Index(chunks)


def recall(index: Index, claims: list, answer_key: dict, k: int = 8) -> tuple[int, list[str]]:
    """Dev helper: how often is the gold source retrieved for each labelled claim?

    Used for the A3 write-up — "retrieval found the right paper for N/12 claims in the top 8".
    """
    gold = {c["id"]: c.get("expected_source") for c in answer_key["claims"]}
    hits, misses = 0, []
    for claim in claims:
        want = gold.get(claim.id)
        if not want:
            continue
        got = {c.source_id for c in index.top_k(claim.text, k)}
        if want in got:
            hits += 1
        else:
            misses.append(claim.id)
    return hits, misses
