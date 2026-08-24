from pathlib import Path
import pypdf
import docx2txt
import pytesseract
from pdf2image import convert_from_path


def load_document_text(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()

    if ext == ".pdf":
        reader = pypdf.PdfReader(filepath)
        pages_text = [page.extract_text() or "" for page in reader.pages]
        combined_text = "\n\n".join(pages_text)

        if _needs_ocr(pages_text):
            combined_text = _ocr_pdf(filepath)

        return combined_text

    elif ext == ".docx":
        return docx2txt.process(filepath)

    elif ext in (".txt", ".md"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            raise ValueError(f"File is not valid UTF-8 text: {filepath}")

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _needs_ocr(pages_text: list[str]) -> bool:
    """A PDF needs OCR if extraction produced essentially no real text."""
    total_chars = sum(len(p.strip()) for p in pages_text)
    return total_chars < 20  # arbitrary small threshold — a real PDF page has far more than this


def _ocr_pdf(filepath: str) -> str:
    images = convert_from_path(filepath)
    page_texts = [pytesseract.image_to_string(img) for img in images]
    return "\n\n".join(page_texts)