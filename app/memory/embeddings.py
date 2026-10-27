from __future__ import annotations

import hashlib
import re

import numpy as np

_DIM = 256
_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_SPLIT.split(text.lower()) if t]


def _token_index(token: str) -> int:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % _DIM


def _token_sign(token: str) -> float:
    digest = hashlib.sha256((token + "#sign").encode("utf-8")).digest()
    return 1.0 if digest[0] & 1 else -1.0


def embed(text: str) -> np.ndarray:
    vector = np.zeros(_DIM, dtype=np.float64)
    tokens = _tokens(text)
    for token in tokens:
        vector[_token_index(token)] += _token_sign(token)
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return vector
    return vector / norm


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    value = float(np.dot(a, b) / (na * nb))
    return max(-1.0, min(1.0, value))
