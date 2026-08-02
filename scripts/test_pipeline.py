from app.ingestion.chunking import chunk_text_recursive
from app.ingestion.cleaning import clean_text
from app.ingestion.metadata import build_chunks_with_metadata
from app.ingestion.loader import load_document_text
from app.retrieval.vector_store import add_chunks_to_store, collection
from app.ingestion.embeddings import embed_texts


filepath = "sample_data/imtithal/control_management_guide.pdf"  # <- update to your real file's actual path

# Step 1: load_document_text takes a filepath, returns the raw text as one big string
raw_text = load_document_text(filepath)

# Step 2 : The raw text is cleaned from white spaces and such 
clened_text = clean_text(raw_text)

# Step 3: chunk_text_by_sentences takes that string, returns a list of smaller text chunks
chunks = chunk_text_recursive(clened_text)

# Step 3: build_chunks_with_metadata takes the chunk list + filepath, returns list of dicts with metadata attached
tagged_chunks = build_chunks_with_metadata(chunks, filepath)

# Step 4: add_chunks_to_store takes those tagged dicts, embeds them, and saves to Chroma
add_chunks_to_store(tagged_chunks)
print("Real document stored. Collection count:", collection.count())

# Step 5: now actually search it with a real question
question = "How do I assign a control owner?"
question_embedding = embed_texts([question])[0]

results = collection.query(query_embeddings=[question_embedding], n_results=3)
print(results)