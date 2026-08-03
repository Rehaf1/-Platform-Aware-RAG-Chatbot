from pathlib import Path
from app.ingestion.chunking import chunk_text_structural_aware , split_by_headings
from app.ingestion.cleaning import clean_text
from app.ingestion.metadata import build_chunks_with_metadata
from app.ingestion.loader import load_document_text
from app.retrieval.vector_store import add_chunks_to_store, collection
from app.ingestion.embeddings import embed_texts
from app.ingestion.collection_and_validation import collect_documents , validate_document
from app.ingestion.duplicate_detection import hash_text,is_duplicate, load_registry ,save_registry, normalize_for_hashing



filepaths = collect_documents("sample_data")

# this is to make sure no duplicate files that have diffrent extionstion are loaded into chroma 
REGISTRY_PATH = "ingested_documents.json"
registry = load_registry(REGISTRY_PATH)


for filepath in filepaths:
    is_valid, reason = validate_document(filepath)
    
    if not is_valid:
        print(f"Skipping {filepath}: {reason}")
        continue
# Step 1: load_document_text takes a filepath, returns the raw text as one big string
    raw_text = load_document_text(filepath)

# Step 2 : The raw text is cleaned from white spaces and such 
    cleaned_text = clean_text(raw_text)
    
# step 3 : making sure there are no duplicante
    normalized_for_hash = normalize_for_hashing(cleaned_text)
    text_hash = hash_text(normalized_for_hash)
    print(f"--- {filepath} ---")
    print(repr(cleaned_text[:200]))
    
    
    if is_duplicate(text_hash, registry):
        print(f"Skipping {filepath}: duplicate content already ingested")
        continue

    registry[text_hash] = {"document_name": Path(filepath).name}
    
    
# Step 3: chunk_text_by_sentences takes that string, returns a list of smaller text chunks
    structured_chunks = chunk_text_structural_aware(cleaned_text)

    chunk_strings = [chunk_text for _, chunk_text in structured_chunks]
    sections = [section_name for section_name, _ in structured_chunks]


# Step 4: build_chunks_with_metadata takes the chunk list + filepath, returns list of dicts with metadata attached
    tagged_chunks = build_chunks_with_metadata(
        chunk_strings=chunk_strings,
        filepath=filepath,
        sections=sections,
    )


    print("IDs about to be added:", [c["document_name"] for c in tagged_chunks[:1]], filepath)
# Step 4: add_chunks_to_store takes those tagged dicts, embeds them, and saves to Chroma
    add_chunks_to_store(tagged_chunks)
    print(f"Stored {filepath}. Collection count:", collection.count())
   
   
   
"""
   # Step 5: now actually search it with a real question
    question = "How do I assign a control owner?"
    question_embedding = embed_texts([question])[0]

    results = collection.query(query_embeddings=[question_embedding], n_results=3)
    print(results)


    sections = split_by_headings(cleaned_text)
    for name, content in sections:
        print(f"SECTION: {name}")
        print(content[:100])
        print("---")
    
    """
    
    