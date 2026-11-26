"""Load the prompt text out of the markdown files in prompts/.

The `.md` files are documentation *and* the source of truth: each contains one fenced block with
the actual prompt. Keeping one copy means the prompt you demo is the prompt you wrote down.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

_FENCE = re.compile(r"```(?:text)?\s*\n(.*?)```", re.DOTALL)


@lru_cache(maxsize=8)
def load_prompt(name: str) -> str:
    text = (PROMPTS_DIR / name).read_text(encoding="utf-8")
    match = _FENCE.search(text)
    return (match.group(1) if match else text).strip()
