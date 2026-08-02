from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

def load_document_text(filepath: str) -> str:
    """
    Extracts raw text from a document, regardless of format.
    Uses LangChain loaders under the hood (PDF/DOCX); plain Python for TXT/MD
    since those don't need a special parser.
    """
    ext = Path(filepath).suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(filepath)
        pages = loader.load()  # returns a list of Document objects, one per page
        return "\n\n".join(page.page_content for page in pages)

    elif ext == ".docx":
        loader = Docx2txtLoader(filepath)
        docs = loader.load()
        return "\n\n".join(doc.page_content for doc in docs)

    elif ext in (".txt", ".md"):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError(f"Unsupported file type: {ext}")
    
#text = load_document_text("/Users/rehaf/Downloads/control_management_guide.pdf")
#print(text[:300])