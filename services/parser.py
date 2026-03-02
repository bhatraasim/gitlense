from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import settings

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "env", "dist", "build", ".next", ".nuxt", "coverage",
    ".pytest_cache", ".mypy_cache", "migrations", ".idea", ".vscode",
}

SKIP_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    ".env",
    ".gitignore",
    ".DS_Store"
}


# code-aware separators — tries these in order before falling back to chars
CODE_SEPARATORS = [
    "\nclass ",      # split at class definitions
    "\ndef ",        # split at function definitions
    "\n\n",          # split at blank lines
    "\n",            # split at newlines
    " ",             # split at spaces
    "",              # last resort — character level
]

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # characters per chunk
    chunk_overlap=100,      # overlap for context continuity
    separators=CODE_SEPARATORS
)


def get_all_files(repo_path: str) -> list[dict]:
    files = []
    repo = Path(repo_path)

    for file_path in repo.rglob("*"):
        if file_path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in file_path.parts):
            continue
        if file_path.name in SKIP_FILES:      # ← add this line
            continue
        if file_path.suffix not in settings.SUPPORTED_EXTENSIONS:
            continue

        size_kb = file_path.stat().st_size / 1024
        if size_kb > settings.MAX_FILE_SIZE_KB:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if not content.strip():
            continue

        files.append({
            "file_path": str(file_path.relative_to(repo)),
            "extension": file_path.suffix,
            "size_kb": round(size_kb, 2),
            "content": content
        })

    return files


def chunk_file(file: dict) -> list[dict]:
    chunks = text_splitter.split_text(file["content"])

    return [
        {
            "file_path": file["file_path"],
            "extension": file["extension"],
            "chunk_text": chunk,
            "chunk_index": i,        # position in file, useful for ordering results
        }
        for i, chunk in enumerate(chunks)
    ]


def parse_repo(repo_path: str) -> list[dict]:
    all_chunks = []

    files = get_all_files(repo_path)
    for file in files:
        chunks = chunk_file(file)
        all_chunks.extend(chunks)

    return all_chunks