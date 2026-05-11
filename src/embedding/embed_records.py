"""Sentence-transformer embedding wrapper. Lazy-loads model on first call."""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
DIMENSION = 384

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: list[str], show_progress: bool = False) -> list[list[float]]:
    """Embed a list of strings. Returns list of 384-dim float vectors."""
    return get_model().encode(texts, show_progress_bar=show_progress).tolist()
