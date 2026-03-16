from __future__ import annotations

from typing import Any, Optional, Union

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.settings import settings


PointId = Union[int, str]


class QdrantStore:
    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection = settings.qdrant_collection

    def ensure_collection(self, vector_size: int) -> None:
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection in existing:
            return

        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
        )

    def upsert(self, point_id: PointId, vector: list[float], payload: dict[str, Any]) -> None:
        self.client.upsert(
            collection_name=self.collection,
            points=[qm.PointStruct(id=point_id, vector=vector, payload=payload)],
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        user_id: Optional[int] = None,
    ):
        qfilter = None
        if user_id is not None:
            qfilter = qm.Filter(
                must=[qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id))]
            )

        #qdrant-client 1.16.x
        res = self.client.query_points(
            collection_name=self.collection,
            query=qm.NearestQuery(nearest=query_vector),
            limit=limit,
            query_filter=qfilter,
            with_payload=True,
        )
        return res.points

    def delete_by_document_id(self, user_id: int, document_id: int) -> None:
        qfilter = qm.Filter(
            must=[
                qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id)),
                qm.FieldCondition(key="document_id", match=qm.MatchValue(value=document_id)),
            ]
        )
        self.client.delete(
            collection_name=self.collection,
            points_selector=qm.FilterSelector(filter=qfilter),
        )

    def delete_doc(self, user_id: int, doc_id: str) -> None:
        qfilter = qm.Filter(
            must=[
                qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id)),
                qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id)),
            ]
        )
        self.client.delete(
            collection_name=self.collection,
            points_selector=qm.FilterSelector(filter=qfilter),
        )
