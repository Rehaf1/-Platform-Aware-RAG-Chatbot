from sentence_transformers import SentenceTransformer
from typing import List


model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.

    Supports:
    - English
    - Arabic
    - Mixed Arabic/English text

    Args:
        texts: List of strings.

    Returns:
        List of embedding vectors.
    """
    embeddings = model.encode(
        texts, # defult behavier is to convert into numpy 
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return embeddings.tolist()