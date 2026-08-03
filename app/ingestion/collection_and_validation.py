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

