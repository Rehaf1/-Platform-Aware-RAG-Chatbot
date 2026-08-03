from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

def collect_documents(root_folder: str) -> list[str]:
    """
    Recursively finds all supported document files under root_folder,
    across all platform subfolders.
    Returns a list of file paths as strings.
    """
    root = Path(root_folder)
    documents = []

    for filepath in root.rglob("*"):
        if filepath.is_file() and filepath.suffix.lower() in SUPPORTED_EXTENSIONS:
            documents.append(str(filepath))

    return documents

MAX_FILE_SIZE_BYTES = 1_000_000_000  # 1 GB safety ceiling

def validate_document(filepath: str) -> tuple[bool, str]:
    path = Path(filepath)

    if not path.exists():
        return False, "File does not exist"

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {path.suffix}"

    file_size = path.stat().st_size

    if file_size == 0:
        return False, "File is empty"

    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File too large: {file_size} bytes"

    return True, ""
