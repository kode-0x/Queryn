from __future__ import annotations

import numpy as np

from app.memory.embeddings import cosine, embed


def test_embedding_is_deterministic() -> None:
    a = embed("multi agent research platform")
    b = embed("multi agent research platform")
    assert np.array_equal(a, b)


def test_identical_cosine_is_one() -> None:
    vector = embed("deterministic offline embedding")
    assert cosine(vector, vector) == 1.0


def test_distinct_token_vectors_are_near_orthogonal() -> None:
    a = embed("alpha")
    b = embed("omega")
    assert abs(cosine(a, b)) < 0.5


def test_empty_text_yields_zero_vector() -> None:
    vector = embed("")
    assert float(np.linalg.norm(vector)) == 0.0
    assert cosine(vector, embed("anything")) == 0.0


def test_vectors_are_l2_normalized() -> None:
    vector = embed("normalized output check")
    assert abs(float(np.linalg.norm(vector)) - 1.0) < 1e-9
