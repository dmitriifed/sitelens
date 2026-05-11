"""Pinecone connection, index management, upsert, and query helpers."""

import os

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()


def get_client() -> Pinecone:
    api_key = os.getenv("PINECONE_API_KEY")
    assert api_key, "PINECONE_API_KEY not set — check .env"
    return Pinecone(api_key=api_key)


def get_or_create_index(
    pc: Pinecone,
    name: str,
    dimension: int = 384,
    metric: str = "cosine",
    cloud: str = "aws",
    region: str = "us-east-1",
):
    if name not in pc.list_indexes().names():
        pc.create_index(
            name=name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud=cloud, region=region),
        )
    return pc.Index(name)


def upsert_records(
    index,
    records: list[dict],
    embeddings: list[list[float]],
    namespace: str = "",
) -> int:
    """Upsert {id, text} records with pre-computed embeddings. Returns vector count."""
    vectors = [
        {
            "id": records[i]["id"],
            "values": embeddings[i],
            "metadata": {"text": records[i]["text"]},
        }
        for i in range(len(records))
    ]
    index.upsert(vectors=vectors, namespace=namespace)
    return len(vectors)


def query(
    index,
    vector: list[float],
    top_k: int = 3,
    namespace: str = "",
) -> list[dict]:
    """Query the index and return top_k matches as a list of dicts."""
    results = index.query(
        vector=vector, top_k=top_k, include_metadata=True, namespace=namespace
    )
    return results["matches"]
