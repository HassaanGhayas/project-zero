"""
YAML frontmatter generator for action files.

Creates structured markdown files with YAML frontmatter containing
8 required fields per FR-002:
- type, original_name, size, file_type, category, received, priority, status
"""

from pathlib import Path
from typing import Dict, Any

from .categorizer import categorize_file
from .utils import create_yaml_frontmatter, get_iso8601_timestamp, sanitize_filename


def generate_action_file_frontmatter(
    file_path: Path,
    status: str = "pending"
) -> Dict[str, Any]:
    """
    Generate YAML frontmatter fields for an action file.

    Args:
        file_path: Path to the source file
        status: Initial status (default: "pending")

    Returns:
        Dictionary of frontmatter fields

    Fields (FR-002):
        - type: Action category
        - original_name: Source filename
        - size: File size in bytes
        - file_type: File extension with dot
        - category: Semantic category
        - received: ISO 8601 timestamp
        - priority: low | medium | high
        - status: pending | in_progress | completed | flagged
    """
    file_type, category, priority = categorize_file(file_path)
    file_stats = file_path.stat()

    frontmatter = {
        "type": file_type,
        "original_name": file_path.name,
        "size": file_stats.st_size,
        "file_type": file_path.suffix.lower() or ".unknown",
        "category": category,
        "received": get_iso8601_timestamp(),
        "priority": priority,
        "status": status,
    }

    return frontmatter


def generate_action_file_content(file_path: Path) -> str:
    """
    Generate complete markdown content for an action file.

    Args:
        file_path: Path to the source file

    Returns:
        Markdown string with YAML frontmatter and body

    Example:
        ---
        type: document
        original_name: invoice.pdf
        size: 204800
        file_type: .pdf
        category: document
        received: 2026-02-07T15:30:00Z
        priority: medium
        status: pending
        ---

        ## File Details
        Detected new file drop for processing.

        ## Suggested Actions
        - [ ] Review content
        - [ ] Process or flag for approval
        - [ ] Move to Done/ when complete
    """
    frontmatter_fields = generate_action_file_frontmatter(file_path)
    yaml_section = create_yaml_frontmatter(frontmatter_fields)

    body = f"""
## File Details
Detected new file drop for processing.

Original file: {file_path.name}
Size: {frontmatter_fields['size']} bytes
Category: {frontmatter_fields['category']}

## Suggested Actions
- [ ] Review content
- [ ] Process or flag for approval
- [ ] Move to Done/ when complete
"""

    return yaml_section + "\n" + body


def generate_action_filename(original_filename: str) -> str:
    """
    Generate action file name from original filename (FR-015).

    Format: FILE_{sanitized_original_name}.md

    Args:
        original_filename: Original source filename

    Returns:
        Action filename

    Example:
        >>> generate_action_filename("Q4 Report (2024).pdf")
        'FILE_Q4_Report_2024.pdf.md'
    """
    sanitized = sanitize_filename(original_filename)
    return f"FILE_{sanitized}.md"
