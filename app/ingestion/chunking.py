import re

# the first chunking strategy but cuts mid sentence so won't use it 
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



# improved the splitting by sentence to actually intake diffrent cases 
SENTENCE_SPLIT_REGEX = r'(?<=[.!?])\s+'

def split_into_units(text, chunk_size, separators):
    """
    Recursively splits text using separators, from biggest to smallest,
    until every piece is <= chunk_size words.
    """
    if not separators:
        return [text]  # no more separators left, give up and return as-is

    separator = separators[0]
    remaining_separators = separators[1:]

    if separator == SENTENCE_SPLIT_REGEX:
        pieces = re.split(separator, text)
    else:
        pieces = text.split(separator)

    units = []
    for piece in pieces:
        if len(piece.split()) <= chunk_size:
            units.append(piece)
        else:
            # too big — recurse with the NEXT separator down the list
            units.extend(split_into_units(piece, chunk_size, remaining_separators))

    return units

def _split_by_words(text, chunk_size):
    words = text.split()
    pieces = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        piece_words = words[start:end]
        pieces.append(" ".join(piece_words))
        start = end  # no overlap needed at this level
    return pieces

def pack_units_into_chunks(units, chunk_size, overlap):
    """
    Groups a list of small text pieces into chunks of ~chunk_size words each,
    carrying `overlap` words of context forward between consecutive chunks.
    """
    chunks = []
    current_chunk_units = []
    current_word_count = 0

    for unit in units:
        unit_word_count = len(unit.split())

        if current_word_count + unit_word_count > chunk_size and current_chunk_units:
            chunks.append(" ".join(current_chunk_units))

            # carry overlap forward
            overlap_units = []
            overlap_word_count = 0
            for u in reversed(current_chunk_units):
                if overlap_word_count >= overlap:
                    break
                overlap_units.insert(0, u)
                overlap_word_count += len(u.split())

            current_chunk_units = overlap_units
            current_word_count = overlap_word_count

        current_chunk_units.append(unit)
        current_word_count += unit_word_count

    if current_chunk_units:
        chunks.append(" ".join(current_chunk_units))

    return chunks

def chunk_text_recursive(text, chunk_size=50, overlap=10):
    units = split_into_units(text, chunk_size, separators=["\n\n", SENTENCE_SPLIT_REGEX])
    return pack_units_into_chunks(units, chunk_size, overlap)

# wont use this stat

def chunk_text_structural_aware(text, chunk_size=50, overlap=10):
    # your code here
    pass

