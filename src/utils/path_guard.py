import os
from pathlib import Path
from typing import List, Tuple

# Folders to filter out during directory listings for cleanliness and performance
IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".mypy_cache",
    ".pytest_cache",
}

# Maximum text file size in bytes to render inline in chat (50 KB).
# Files larger than this will be sent as documents.
MAX_INLINE_FILE_SIZE = 50 * 1024


class SecurityPathError(Exception):
    """Raised when an attempted path traversal or invalid path access is detected."""
    pass


def resolve_safe_path(base_dir: str | Path, sub_path: str = "") -> Path:
    """
    Safely resolves a target path ensuring it strictly remains within base_dir.
    Guards against directory traversal attacks (e.g. '../../etc/passwd').
    """
    base_resolved = Path(base_dir).resolve()
    if not base_resolved.exists() or not base_resolved.is_dir():
        raise SecurityPathError(f"Base project directory does not exist: {base_dir}")

    if not sub_path or sub_path.strip() in (".", "/"):
        return base_resolved

    # Sanitize and resolve target path
    clean_sub = sub_path.strip().lstrip("/\\")
    target_path = (base_resolved / clean_sub).resolve()

    try:
        # Python 3.9+ is_relative_to check
        if not target_path.is_relative_to(base_resolved):
            raise SecurityPathError("Access denied: Target path escapes project root boundary.")
    except AttributeError:
        # Fallback for older python environments
        try:
            target_path.relative_to(base_resolved)
        except ValueError:
            raise SecurityPathError("Access denied: Target path escapes project root boundary.")

    return target_path


def list_directory_entries(
    project_root: str | Path,
    rel_path: str = "",
    max_items: int = 60
) -> Tuple[List[str], List[str], bool]:
    """
    Safely lists subdirectories and files within a relative directory.
    Returns: (directories, files, is_truncated)
    """
    target_dir = resolve_safe_path(project_root, rel_path)

    if not target_dir.is_dir():
        raise SecurityPathError(f"Target path is not a directory: {rel_path or '.'}")

    dirs: List[str] = []
    files: List[str] = []
    total_scanned = 0
    is_truncated = False

    try:
        for entry in sorted(target_dir.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            if entry.name in IGNORED_DIRECTORIES:
                continue

            total_scanned += 1
            if total_scanned > max_items:
                is_truncated = True
                break

            if entry.is_dir():
                dirs.append(f"{entry.name}/")
            else:
                files.append(entry.name)
    except PermissionError as err:
        raise SecurityPathError(f"Permission denied accessing directory: {err}")

    return dirs, files, is_truncated
