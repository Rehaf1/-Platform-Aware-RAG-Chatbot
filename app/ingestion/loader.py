from pathlib import Path
import pypdf
import docx2txt

def load_document_text(filepath: str) -> str:
    """
    Extracts raw text from a document, regardless of format.
    Uses pypdf and docx2txt directly (no LangChain wrapper needed —
    the wrapper added no real value and is being deprecated anyway).
    """
    ext = Path(filepath).suffix.lower()

    if ext == ".pdf":
        reader = pypdf.PdfReader(filepath)
        pages_text = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages_text)

    elif ext == ".docx":
        return docx2txt.process(filepath)

    elif ext in (".txt", ".md"):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError(f"Unsupported file type: {ext}")