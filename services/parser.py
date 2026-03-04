from pathlib import Path
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document
from config import settings


SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "env", "dist", "build", ".next", ".nuxt", "coverage",
    ".pytest_cache", ".mypy_cache", "migrations", ".idea", ".vscode",
}

SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "uv.lock", ".env", ".gitignore", ".DS_Store"
}

# maps file extension → LangChain Language enum
LANGUAGE_MAP = {
    ".py":   Language.PYTHON,
    ".js":   Language.JS,
    ".ts":   Language.TS,
    ".jsx":  Language.JS,
    ".tsx":  Language.TS,
    ".go":   Language.GO,
    ".java": Language.JAVA,
    ".cpp":  Language.CPP,
    ".c":    Language.C,
    ".rs":   Language.RUST,
    ".rb":   Language.RUBY,
}

# fallback splitter for non-code files (md, json, yaml)
fallback_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
)


def parse_repo(repo_path: str) -> list[dict]:
    """
    Main function — call this from your Celery task.
    Returns all chunks across all files ready for embedding.
    """
    all_chunks = []
    repo = Path(repo_path)

    for file_path in repo.rglob("*"):

        # skip directories
        if file_path.is_dir():
            continue

        # skip unwanted folders
        if any(part in SKIP_DIRS for part in file_path.parts):
            continue

        # skip unwanted files
        if file_path.name in SKIP_FILES:
            continue

        # skip unsupported extensions
        if file_path.suffix not in settings.SUPPORTED_EXTENSIONS:
            continue

        # skip files that are too large
        size_kb = file_path.stat().st_size / 1024
        if size_kb > settings.MAX_FILE_SIZE_KB:
            continue

        # chunk the file
        chunks = chunk_file(file_path, repo)
        print(f"Parsed {file_path.name}: {len(chunks)} chunks") 
        all_chunks.extend(chunks)
    print(f"TOTAL CHUNKS: {len(all_chunks)}")  # add this
    return all_chunks


def chunk_file(file_path: Path, repo: Path) -> list[dict]:
    """
    Route file to the correct chunker based on extension.
    """
    extension = file_path.suffix
    relative_path = str(file_path.relative_to(repo))

    if extension in LANGUAGE_MAP:
        return chunk_code_file(file_path, relative_path, extension)
    else:
        return chunk_text_file(file_path, relative_path, extension)


def chunk_code_file(file_path: Path, relative_path: str, extension: str) -> list[dict]:
    """
    Use LanguageParser for code files.
    Splits at function and class boundaries — keeps code structure intact.
    """
    try:
        language = LANGUAGE_MAP[extension]

        # GenericLoader walks the file and parses it with LanguageParser
        loader = GenericLoader.from_filesystem(
            str(file_path.parent),
            glob=file_path.name,        # only this specific file
            suffixes=[extension],
            parser=LanguageParser(language=language.value) # type: ignore
        )

        documents = loader.load()
        print(f"LanguageParser: {relative_path} → {len(documents)} chunks")  # debug

        if not documents:
            # LanguageParser failed — fall back to text chunker
            return chunk_text_file(file_path, relative_path, extension)

        chunks = []
        for i, doc in enumerate(documents):
            if not doc.page_content.strip():
                continue

            chunks.append({
                "file_path": relative_path,
                "extension": extension,
                "chunk_text": doc.page_content,
                "chunk_index": i,
                "chunk_type": doc.metadata.get("content_type", "code"),  # "functions", "classes", "simplified_code"
            })

        return chunks

    except Exception:
        # any error → fall back to text chunker
        return chunk_text_file(file_path, relative_path, extension)


def chunk_text_file(file_path: Path, relative_path: str, extension: str) -> list[dict]:
    """
    Fallback for non-code files (md, json, yaml) or when LanguageParser fails.
    Uses RecursiveCharacterTextSplitter.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        if not content.strip():
            return []

        text_chunks = fallback_splitter.split_text(content)

        return [
            {
                "file_path": relative_path,
                "extension": extension,
                "chunk_text": chunk,
                "chunk_index": i,
                "chunk_type": "text",
            }
            for i, chunk in enumerate(text_chunks)
            if chunk.strip()
        ]

    except Exception:
        return []
