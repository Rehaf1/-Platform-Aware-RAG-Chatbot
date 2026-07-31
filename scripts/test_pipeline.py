from app.ingestion.chunking import chunk_text_by_sentences
from app.ingestion.metadata import build_chunks_with_metadata
from app.ingestion.loader import load_document_text
from app.retrieval.vector_store import add_chunks_to_store, collection

text = "This is a test. It has two sentences."
chunks = chunk_text_by_sentences(text)
tagged = build_chunks_with_metadata(chunks, "sample_data/imtithal/test_doc.txt")


for c in tagged:
    print(c)

add_chunks_to_store(tagged)
print("Chunks stored. Collection count:", collection.count())