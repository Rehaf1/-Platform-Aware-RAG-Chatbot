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

HEADING_PATTERNS = [
    r'^#{1,6}\s+(.+)',              # Markdown: captures text after the #'s
    r'^Section:\s*(.+)',            # captures text after "Section:"
    r'^Chapter\s+\d+[:.]?\s*(.+)',  # captures text after "Chapter N:"
    r'^\d+(?:\.\d+)*\s+(.+)',       # captures text after the number
]

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




def is_heading(line: str, patterns: list[str] = None) -> bool:
    if patterns is None:
        patterns = HEADING_PATTERNS
    line = line.strip()
    return any(re.match(pattern, line) for pattern in patterns)


def clean_heading_text(line: str, patterns: list[str] = None) -> str:
    if patterns is None:
        patterns = HEADING_PATTERNS
    line = line.strip()
    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            return match.group(1).strip()
    return line

def split_by_headings(text: str, patterns: list[str] = None) -> list[tuple[str, str]]:
    """
    Splits text into (section_name, section_text) pairs using heading detection.
    Text before the first detected heading is grouped under section_name=None.
    """
    lines = text.splitlines()

    sections = []
    current_section_name = None
    current_lines = []

    for line in lines:
        if is_heading(line, patterns):
            # close out whatever we were accumulating before this heading
            if current_lines:
                sections.append((current_section_name, "\n".join(current_lines)))

            current_section_name = clean_heading_text(line, patterns)
            current_lines = []
        else:
            current_lines.append(line)

    # don't forget the last section — nothing comes after it to trigger a close-out
    if current_lines:
        sections.append((current_section_name, "\n".join(current_lines)))

    return sections

def chunk_text_structural_aware(text, chunk_size=50, overlap=10, patterns=None):
    sections = split_by_headings(text, patterns)
    
    all_chunks = []
    for section_name, section_text in sections:
        units = split_into_units(section_text, chunk_size, separators=["\n\n", SENTENCE_SPLIT_REGEX])
        section_chunks = pack_units_into_chunks(units, chunk_size, overlap)
        
        for chunk_text in section_chunks:
            all_chunks.append((section_name, chunk_text))
    
    return all_chunks

