from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model
