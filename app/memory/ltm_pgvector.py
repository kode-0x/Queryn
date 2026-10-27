from __future__ import annotations

import importlib
import json
import uuid
from typing import Any

from app.memory.embeddings import embed
from app.memory.ltm_base import LongTermMemory, LTMRecord
from app.memory.ltm_memory import InMemoryLTM
from app.observability.logging import get_logger

_logger = get_logger("queryn.memory.ltm")

_DIM = 256
_TABLE = "queryn_ltm"

_DDL = (
    "CREATE EXTENSION IF NOT EXISTS vector;",
    f"CREATE TABLE IF NOT EXISTS {_TABLE} ("
    "id TEXT PRIMARY KEY, "
    "content TEXT NOT NULL, "
    "metadata JSONB NOT NULL DEFAULT '{}'::jsonb, "
    f"embedding vector({_DIM}) NOT NULL);",
)


def _vector_literal(values: Any) -> str:
    return "[" + ",".join(repr(float(v)) for v in values) + "]"


class PgVectorLTM:
    def __init__(self, dsn: str, fallback: LongTermMemory | None = None) -> None:
        psycopg = importlib.import_module("psycopg")
        self._connect = psycopg.connect
        self._dsn = dsn
        self._fallback = fallback or InMemoryLTM()

    @classmethod
    def connect(cls, dsn: str, fallback: LongTermMemory | None = None) -> PgVectorLTM:
        instance = cls(dsn, fallback)
        with instance._connect(instance._dsn) as conn:
            with conn.cursor() as cur:
                for statement in _DDL:
                    cur.execute(statement)
            conn.commit()
        return instance

    def _warn(self, operation: str, exc: Exception) -> None:
        _logger.warning(
            "pgvector_ltm_fallback",
            extra={
                "extra_fields": {
                    "event": "pgvector_ltm_fallback",
                    "operation": operation,
                    "error": type(exc).__name__,
                }
            },
        )

    def store(self, content: str, metadata: dict[str, Any]) -> str:
        record_id = uuid.uuid4().hex
        vector = _vector_literal(embed(content).tolist())
        try:
            with self._connect(self._dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {_TABLE} (id, content, metadata, embedding) "
                        "VALUES (%s, %s, %s::jsonb, %s::vector)",
                        (record_id, content, json.dumps(metadata), vector),
                    )
                conn.commit()
        except Exception as exc:
            self._warn("store", exc)
            return self._fallback.store(content, metadata)
        return record_id

    def retrieve(
        self, query: str, k: int = 5, filters: dict[str, Any] | None = None
    ) -> list[LTMRecord]:
        vector = _vector_literal(embed(query).tolist())
        where = ""
        params: list[Any] = [vector]
        if filters:
            where = " WHERE metadata @> %s::jsonb"
            params.append(json.dumps(filters))
        params.append(max(k, 0))
        try:
            with self._connect(self._dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT id, content, metadata, 1 - (embedding <=> %s::vector) AS score "
                        f"FROM {_TABLE}{where} ORDER BY embedding <=> %s::vector LIMIT %s",
                        [params[0], *params[1:-1], params[0], params[-1]],
                    )
                    rows = cur.fetchall()
        except Exception as exc:
            self._warn("retrieve", exc)
            return self._fallback.retrieve(query, k, filters)
        results: list[LTMRecord] = []
        for row in rows:
            raw_metadata = row[2]
            metadata = raw_metadata if isinstance(raw_metadata, dict) else json.loads(raw_metadata)
            results.append(
                LTMRecord(
                    id=str(row[0]),
                    content=str(row[1]),
                    metadata=dict(metadata),
                    score=float(row[3]),
                )
            )
        return results
