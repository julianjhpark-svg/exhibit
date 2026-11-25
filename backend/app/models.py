"""API contracts. Keep these stable — the frontend and the eval script both depend on them."""

from typing import Literal

from pydantic import BaseModel, Field

Verdict = Literal["supported", "partial", "unsupported", "cant_verify"]


class Source(BaseModel):
    id: str
    title: str
    pages: int | None = None
    # "upload" | "url" | "paste" — shown in the UI, and useful in the limitations section
    kind: Literal["upload", "url", "paste"] = "upload"


class Passage(BaseModel):
    source_id: str
    page: int
    text: str


class ClaimInput(BaseModel):
    id: str
    text: str


class VerdictOut(BaseModel):
    claim_id: str
    verdict: Verdict
    quote: str | None = None
    source_id: str | None = None
    page: int | None = None
    reason: str | None = None
    # true when verify.enforce() had to override the model's claim of support
    downgraded: bool = False


class CheckRequest(BaseModel):
    essay: str
    sources: list[Source] = Field(default_factory=list)


class CheckResponse(BaseModel):
    claims: list[VerdictOut]
    stats: dict[str, int]
    warnings: list[str] = Field(default_factory=list)


class SourceOut(BaseModel):
    source: Source
    pages: int
    chars: int
    usable: bool
