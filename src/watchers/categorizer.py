"""
File categorization logic for action file generation.

Maps file extensions to semantic categories per FR-003:
- document: PDF, Word, PowerPoint
- text: Plain text, Markdown, RTF
- data: CSV, Excel, JSON, XML
- image: JPG, PNG, GIF, SVG
- email: EML, MSG
- unknown: Unrecognized extensions
"""

from pathlib import Path
from typing import Tuple


# FR-003: Category mapping rules
CATEGORY_RULES = {
    # Documents
    ".doc": ("document", "document", "medium"),
    ".docx": ("document", "document", "medium"),
    ".pdf": ("document", "document", "medium"),
    ".ppt": ("document", "document", "medium"),
    ".pptx": ("document", "document", "medium"),
    # Text files
    ".txt": ("text", "text", "low"),
    ".md": ("text", "text", "low"),
    ".rtf": ("text", "text", "low"),
    # Data files
    ".csv": ("data", "data", "medium"),
    ".xlsx": ("data", "data", "medium"),
    ".xls": ("data", "data", "medium"),
    ".json": ("data", "data", "medium"),
    ".xml": ("data", "data", "medium"),
    # Images
    ".jpg": ("image", "image", "low"),
    ".jpeg": ("image", "image", "low"),
    ".png": ("image", "image", "low"),
    ".gif": ("image", "image", "low"),
    ".svg": ("image", "image", "low"),
    # Email
    ".eml": ("email", "email", "high"),
    ".msg": ("email", "email", "high"),
}


def categorize_file(file_path: Path) -> Tuple[str, str, str]:
    """
    Categorize file by extension according to FR-003 rules.

    Args:
        file_path: Path to the file to categorize

    Returns:
        Tuple of (type, category, priority)

    Example:
        >>> from pathlib import Path
        >>> categorize_file(Path("document.pdf"))
        ('document', 'document', 'medium')
        >>> categorize_file(Path("unknown.xyz"))
        ('unknown', 'unknown', 'medium')
    """
    file_extension = file_path.suffix.lower()

    if file_extension in CATEGORY_RULES:
        return CATEGORY_RULES[file_extension]

    # Default to unknown for unrecognized extensions
    return ("unknown", "unknown", "medium")


def should_ignore_file(file_path: Path) -> bool:
    """
    Determine if file should be ignored (FR-011: hidden files and temp files).

    Args:
        file_path: Path to the file

    Returns:
        True if file should be ignored, False otherwise

    Rules:
        - Hidden files (starting with .)
        - Temporary files (*.tmp, *.swp, *.bak)
        - System files (.DS_Store, Thumbs.db)
    """
    filename = file_path.name

    # Hidden files (start with .)
    if filename.startswith("."):
        return True

    # Temporary file extensions
    temp_extensions = [".tmp", ".swp", ".bak", ".temp"]
    if file_path.suffix.lower() in temp_extensions:
        return True

    # System files
    system_files = [".DS_Store", "Thumbs.db", "desktop.ini"]
    if filename in system_files:
        return True

    return False
