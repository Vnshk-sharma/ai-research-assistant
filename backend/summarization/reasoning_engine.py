"""
AI Reasoning Layer.

Wraps a single instruction-tuned Hugging Face seq2seq model
(google/flan-t5-base by default) and exposes task-specific methods:
summarization, question answering, paragraph explanation, comparison,
keyword extraction, contribution/limitation extraction, future-work
suggestion, reading-note generation, and quiz generation.

Using one general-purpose model behind clear task prompts keeps the
reasoning layer simple to maintain while still demonstrating command over
transformer-based NLP. Swapping in task-specific models (e.g. a dedicated
extractive-QA model or a BART summarizer) only requires changing
`_generate()`'s backing pipeline.

IMPORTANT - context window:
google/flan-t5-base's tokenizer truncates input to ~512 tokens (~1800-2000
characters of English text). Passing a whole research paper (often
20,000+ characters) straight into one `_generate()` call means the model
only ever sees the first couple thousand characters (usually just the
abstract/intro) - everything else is silently dropped, which is why task
outputs on real papers used to look thin or off-topic.

To fix this, long-input tasks (keywords, contributions, limitations,
future work, reading notes, quiz, long-form summarize) now use a
map-reduce pattern: the paper is split into chunks that each fit the
token budget, each chunk is processed independently ("map"), and the
per-chunk results are then combined with one final call ("reduce"). This
lets the model actually take the whole document into account instead of
just its opening section.
"""

from functools import lru_cache

from utils.config import settings

# Rough chars-per-token ratio for English text is ~4, so ~1600 characters
# keeps a chunk (plus its task instructions) comfortably inside flan-t5-base's
# ~512-token input limit.
CHUNK_CHARS = 1600
CHUNK_OVERLAP = 100
# Cap how many chunks we map over per call, so very long papers still
# finish in reasonable time and the combined "reduce" input stays bounded.
MAX_CHUNKS = 10


class ReasoningEngine:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.GENERATION_MODEL
        self._pipeline = None

    @property
    def pipeline(self):
        if self._pipeline is None:
            # Lazy import: transformers/torch are heavy dependencies we
            # don't want to load until the reasoning layer is actually used.
            from transformers import pipeline
            self._pipeline = pipeline("text2text-generation", model=self.model_name)
        return self._pipeline

    def _generate(self, prompt: str, max_new_tokens: int = None) -> str:
        max_new_tokens = max_new_tokens or settings.MAX_NEW_TOKENS
        output = self.pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            truncation=True,
            do_sample=False,
        )
        return output[0]["generated_text"].strip()

    # -- Long-document handling -------------------------------------------

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP,
                     max_chunks: int = MAX_CHUNKS) -> list[str]:
        text = text.strip()
        if len(text) <= chunk_size:
            return [text] if text else []

        chunks = []
        start = 0
        while start < len(text) and len(chunks) < max_chunks:
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap if end - overlap > start else end
        return chunks

    def _map_reduce(self, text: str, map_prompt_fn, reduce_prompt_fn,
                     map_max_new_tokens: int = 96, reduce_max_new_tokens: int = 400) -> str:
        """Split `text` into chunks, run `map_prompt_fn(chunk)` on each,
        then combine the per-chunk results with one `reduce_prompt_fn(combined)`
        call. If the text already fits in a single chunk, skips straight to
        generating a direct final-form answer via `reduce_prompt_fn` on the
        raw text, avoiding an unnecessary extra round trip.
        """
        chunks = self._chunk_text(text)
        if not chunks:
            return ""
        if len(chunks) == 1:
            return self._generate(reduce_prompt_fn(chunks[0], single_chunk=True),
                                   max_new_tokens=reduce_max_new_tokens)

        partials = [
            self._generate(map_prompt_fn(chunk), max_new_tokens=map_max_new_tokens)
            for chunk in chunks
        ]
        combined = "\n".join(f"- {p}" for p in partials if p and p.strip())
        # Guard the reduce step's own input against the same token limit,
        # in case a paper produced many chunks worth of partial results.
        combined = combined[: CHUNK_CHARS * 2]
        return self._generate(reduce_prompt_fn(combined, single_chunk=False),
                               max_new_tokens=reduce_max_new_tokens)

    # -- Task-specific prompts -------------------------------------------

    def summarize(self, text: str, length: str = "medium") -> str:
        length_hint = {
            "short": "in 2-3 sentences",
            "medium": "in one concise paragraph",
            "long": "in a detailed multi-paragraph summary covering motivation, method, and results",
        }.get(length, "in one concise paragraph")

        def map_fn(chunk):
            return f"Summarize the key points of this excerpt from a research paper in 1-2 sentences:\n\n{chunk}"

        def reduce_fn(payload, single_chunk):
            if single_chunk:
                return f"Summarize the following research paper content {length_hint}:\n\n{payload}"
            return (
                f"These are partial summaries of consecutive sections of a research paper, "
                f"in order. Combine them into a single coherent summary {length_hint}:\n\n{payload}"
            )

        return self._map_reduce(text, map_fn, reduce_fn, reduce_max_new_tokens=settings.MAX_NEW_TOKENS)

    def answer_question(self, question: str, context: str) -> str:
        prompt = (
            "Answer the question using only the provided context from a research "
            "paper. If the context does not contain the answer, say so.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
        return self._generate(prompt)

    def explain_paragraph(self, paragraph: str) -> str:
        prompt = (
            "Explain the following research-paper paragraph in simple, "
            "plain-English terms for a non-expert reader:\n\n" + paragraph
        )
        return self._generate(prompt)

    def compare_papers(self, text_a: str, text_b: str, title_a: str, title_b: str) -> str:
        # Summarize each paper on its own first (each summarize() call
        # already handles long input via map-reduce), then compare the two
        # short summaries, which reliably fit together in one prompt.
        summary_a = self.summarize(text_a, length="short")
        summary_b = self.summarize(text_b, length="short")
        prompt = (
            f"Compare the following two research papers, '{title_a}' and '{title_b}', "
            "based on their summaries below. Discuss their goals, methods, and key "
            "differences.\n\n"
            f"Paper A ({title_a}) summary:\n{summary_a}\n\n"
            f"Paper B ({title_b}) summary:\n{summary_b}"
        )
        return self._generate(prompt, max_new_tokens=600)

    def extract_keywords(self, text: str) -> str:
        def map_fn(chunk):
            return ("List up to 5 important technical keywords or key phrases from this "
                     f"excerpt of a research paper, comma-separated:\n\n{chunk}")

        def reduce_fn(payload, single_chunk):
            if single_chunk:
                return "Extract the 8 most important technical keywords or key phrases from this text, as a comma-separated list:\n\n" + payload
            return (
                "These are candidate keywords gathered from different sections of a "
                "research paper. Select and return the 8 most important overall, "
                f"deduplicated, as a single comma-separated list:\n\n{payload}"
            )

        return self._map_reduce(text, map_fn, reduce_fn, reduce_max_new_tokens=128)

    def extract_contributions(self, text: str) -> str:
        def map_fn(chunk):
            return ("List any key contributions of a research paper mentioned in this "
                     "excerpt, as bullet points. If none are mentioned, say 'None'.\n\n" + chunk)

        def reduce_fn(payload, single_chunk):
            if single_chunk:
                return "List the key contributions of this research paper as bullet points:\n\n" + payload
            return (
                "These are candidate contributions gathered from different sections of a "
                "research paper (some entries may say 'None' or repeat each other). "
                f"Combine them into a single deduplicated bullet-point list of the paper's "
                f"key contributions:\n\n{payload}"
            )

        return self._map_reduce(text, map_fn, reduce_fn, reduce_max_new_tokens=400)

    def extract_limitations(self, text: str) -> str:
        def map_fn(chunk):
            return ("List any limitations or weaknesses of a research paper acknowledged or "
                     "implied in this excerpt, as bullet points. If none, say 'None'.\n\n" + chunk)

        def reduce_fn(payload, single_chunk):
            if single_chunk:
                return "List the limitations or weaknesses acknowledged or implied in this research paper as bullet points:\n\n" + payload
            return (
                "These are candidate limitations gathered from different sections of a "
                "research paper (some entries may say 'None' or repeat each other). "
                f"Combine them into a single deduplicated bullet-point list of the paper's "
                f"limitations:\n\n{payload}"
            )

        return self._map_reduce(text, map_fn, reduce_fn, reduce_max_new_tokens=400)

    def suggest_future_work(self, text: str) -> str:
        def map_fn(chunk):
            return ("Note any future work, open problems, or limitations mentioned in this "
                     "excerpt of a research paper. If none, say 'None'.\n\n" + chunk)

        def reduce_fn(payload, single_chunk):
            if single_chunk:
                return "Based on this research paper's content, suggest 3-5 promising directions for future research:\n\n" + payload
            return (
                "These are notes on future work and open problems gathered from different "
                "sections of a research paper. Based on them, suggest 3-5 promising directions "
                f"for future research, as bullet points:\n\n{payload}"
            )

        return self._map_reduce(text, map_fn, reduce_fn, reduce_max_new_tokens=400)

    def generate_reading_notes(self, text: str) -> str:
        def map_fn(chunk):
            return ("Extract any problem statement, method details, results, or takeaways "
                     "mentioned in this excerpt of a research paper, as brief notes:\n\n" + chunk)

        def reduce_fn(payload, single_chunk):
            if single_chunk:
                return (
                    "Generate concise study notes for this research paper, covering: "
                    "Problem, Method, Key Results, and Takeaways. Use bullet points.\n\n" + payload
                )
            return (
                "These are raw notes gathered from different sections of a research paper. "
                "Organize them into structured study notes with headings Problem, Method, "
                f"Key Results, and Takeaways. Use bullet points under each heading:\n\n{payload}"
            )

        return self._map_reduce(text, map_fn, reduce_fn, reduce_max_new_tokens=600)

    def generate_quiz(self, text: str, num_questions: int = 5) -> str:
        def map_fn(chunk):
            return ("Write 1-2 quiz questions with answers based on this excerpt of a research "
                     "paper. Format each as 'Q: ...' then 'A: ...'.\n\n" + chunk)

        def reduce_fn(payload, single_chunk):
            if single_chunk:
                return (
                    f"Generate {num_questions} quiz questions with answers to test understanding "
                    "of this research paper. Format each as 'Q: ...' then 'A: ...'.\n\n" + payload
                )
            return (
                "These are candidate quiz questions gathered from different sections of a "
                f"research paper. Select and return the best {num_questions}, removing "
                "duplicates or overly similar ones. Format each as 'Q: ...' then 'A: ...':\n\n" + payload
            )

        return self._map_reduce(text, map_fn, reduce_fn, reduce_max_new_tokens=600)


@lru_cache(maxsize=1)
def get_reasoning_engine() -> ReasoningEngine:
    return ReasoningEngine()
