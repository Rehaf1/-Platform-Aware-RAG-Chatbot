import re

def chunk_text_fixed(text, chunk_size=50, overlap=10):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start = end - overlap
    return chunks


def chunk_text_by_sentences(text, chunk_size=50, overlap=10):
    # Simple sentence split: break after ., !, or ? followed by whitespace.
    # Not perfect (trips on "Dr." or "e.g.") but fine for a first version.
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks = []
    current_chunk_sentences = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())

        # If adding this sentence would overflow the chunk, close out the
        # current chunk first (unless it's still empty).
        if current_word_count + sentence_word_count > chunk_size and current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))

            # Build the overlap: carry the last few sentences forward so the
            # next chunk starts with some shared context, similar to your
            # word-overlap idea but at sentence granularity.
            overlap_sentences = []
            overlap_word_count = 0
            for s in reversed(current_chunk_sentences):
                if overlap_word_count >= overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_word_count += len(s.split())

            current_chunk_sentences = overlap_sentences
            current_word_count = overlap_word_count

        current_chunk_sentences.append(sentence)
        current_word_count += sentence_word_count

    # Don't forget the last partial chunk
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    return chunks

def chunk_text_recursive(text, chunk_size=50, overlap=10):
    # your code here
    pass
def chunk_text_semantic(text, chunk_size=50, overlap=10):
    # your code here
    pass
def chunk_text_structural_aware(text, chunk_size=50, overlap=10):
    # your code here
    pass

