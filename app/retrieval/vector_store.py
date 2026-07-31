import chromadb
from app.ingestion.embeddings import embed_texts

CHROMA_PATH = "./chroma_data"  

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="documents")

def _sanitize_metadata(chunk: dict) -> dict:
    """
    Chroma only accepts str, int, float, or bool as metadata values.
    None and lists must be converted before storage.
    """
    metadata = {k: v for k, v in chunk.items() if k != "text"}

    for key, value in metadata.items():
        if value is None:
            metadata[key] = ""  # empty string = "no value set"
        elif isinstance(value, list):
            metadata[key] = ",".join(value)  # e.g. ["a", "b"] -> "a,b"

    return metadata

def add_chunks_to_store(chunks: list[dict]):
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [_sanitize_metadata(chunk) for chunk in chunks]
    ids = [
        f"{chunk['platform_id']}:{chunk['document_name']}:{chunk['chunk_index']}"
        for chunk in chunks
    ]
    embeddings = embed_texts(documents)

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )