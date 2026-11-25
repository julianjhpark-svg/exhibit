# Where Long-Context Models Lose the Thread — and Their Citations

Synthetic draft used only for testing Exhibit. It contains three deliberate citation errors and
one uncited claim. Ground truth lives in `data/answer_key.json`; do not edit a sentence here
without updating that file.

---

Large language models can now accept very long inputs, but relatively little is known about how
well they actually use them (Liu et al., 2023). Liu et al. (2023) analyze multi-document question
answering and key-value retrieval, two tasks that require locating relevant information inside a
long input.

Their results show that performance can degrade significantly when the position of the relevant
information changes. Accuracy is often highest when the relevant information appears at the
beginning or end of the context. It falls when the model must access information in the middle of
a long context, even for models that were explicitly built for long inputs.

This matters for citation-heavy writing, where the sentence that supports a claim may sit
anywhere in a forty-page paper. Gao et al. (2023) introduce ALCE, which they describe as the first
benchmark for automatic evaluation of citations in model-generated text. ALCE measures fluency,
correctness, and citation quality, and the authors report that these metrics correlate strongly
with human judgments. Even the best systems fail to provide complete citation support in most
cases (Gao et al., 2023).

Because Liu et al. (2023) find that models "do not robustly make use of information in long input
contexts," long contexts should be avoided for citation-heavy writing. Liu et al. (2023) also
report that GPT-4 reaches 98.1% accuracy on multi-document QA once the context is kept under 4,000
tokens. The citation metrics used in ALCE build on the long-context evaluation protocols
introduced by Liu et al. (2023).

Students increasingly paste model output into essays without checking the underlying sources.
