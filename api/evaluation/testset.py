"""Sample evaluation test set for RAGAS and offline evaluation.

Contains a small curated set of question/context/answer examples. Extend this
file or load from JSON to reach 100+ pairs for production evaluation runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class EvaluationExample:
    question: str
    answer: str
    contexts: List[str]
    ground_truth: str


SAMPLE_TESTSET: List[EvaluationExample] = [
    EvaluationExample(
        question="What is retrieval-augmented generation?",
        answer="RAG combines retrieval with generation to ground answers in documents.",
        contexts=[
            "Retrieval-Augmented Generation combines document retrieval with language model generation.",
            "Vector search finds relevant chunks before answer generation.",
        ],
        ground_truth="RAG retrieves relevant documents and uses them as context for generation.",
    ),
    EvaluationExample(
        question="How does tenant isolation work?",
        answer="Each tenant's data is scoped by tenant_id across retrieval and storage.",
        contexts=[
            "Multi-tenant platforms isolate customer data using tenant identifiers.",
            "Documents, chunks, and queries are scoped to a tenant.",
        ],
        ground_truth="Tenant isolation scopes documents, chunks, and queries by tenant_id.",
    ),
    EvaluationExample(
        question="What vector index options exist?",
        answer="The platform supports in-memory, FAISS, ChromaDB, and hybrid stores.",
        contexts=[
            "FAISS provides fast ANN search without metadata filters.",
            "ChromaDB supports metadata-filtered vector retrieval.",
        ],
        ground_truth="Vector stores include in-memory, FAISS, ChromaDB, and hybrid routing.",
    ),
]


def get_sample_testset() -> List[EvaluationExample]:
    """Return the built-in sample test set."""
    return list(SAMPLE_TESTSET)
