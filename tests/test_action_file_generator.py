#!/usr/bin/env python3
"""
Unit tests for action file generator.

Tests cover:
- YAML frontmatter generation
- Field validation
- ISO 8601 timestamp formatting
- File metadata extraction
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.watchers.action_file_generator import generate_action_file_content


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary test file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Sample content for testing")
    return test_file


class TestActionFileGenerator:
    """Test suite for action file generation."""

    def test_basic_frontmatter_structure(self, temp_file):
        """Test that generated content has valid YAML frontmatter."""
        content = generate_action_file_content(temp_file)

        # Verify frontmatter delimiters
        assert content.startswith("---\n")
        assert "\n---\n" in content

        # Verify required fields are present
        assert "type:" in content
        assert "original_name:" in content
        assert "size:" in content
        assert "file_type:" in content
        assert "category:" in content
        assert "received:" in content
        assert "priority:" in content
        assert "status:" in content

    def test_original_name_field(self, temp_file):
        """Test that original_name field contains correct filename."""
        content = generate_action_file_content(temp_file)
        assert "original_name: test.txt" in content

    def test_file_type_field(self, temp_file):
        """Test that file_type field contains correct extension."""
        content = generate_action_file_content(temp_file)
        assert "file_type: .txt" in content

    def test_status_field_default(self, temp_file):
        """Test that status field defaults to 'pending'."""
        content = generate_action_file_content(temp_file)
        assert "status: pending" in content

    def test_size_field_accuracy(self, temp_file):
        """Test that size field matches actual file size."""
        actual_size = temp_file.stat().st_size
        content = generate_action_file_content(temp_file)
        assert f"size: {actual_size}" in content

    def test_iso8601_timestamp_format(self, temp_file):
        """Test that received timestamp is in ISO 8601 format."""
        content = generate_action_file_content(temp_file)

        # Extract timestamp line
        for line in content.split("\n"):
            if line.startswith("received:"):
                timestamp = line.split("received: ")[1]
                # Verify ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
                try:
                    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    assert True
                except ValueError:
                    pytest.fail(f"Invalid ISO 8601 timestamp: {timestamp}")
                break
        else:
            pytest.fail("received field not found in frontmatter")

    def test_categorization_text_file(self, tmp_path):
        """Test that .txt files are categorized correctly."""
        test_file = tmp_path / "document.txt"
        test_file.write_text("Text content")

        content = generate_action_file_content(test_file)
        assert "type: text" in content
        assert "category: text" in content

    def test_categorization_pdf_file(self, tmp_path):
        """Test that .pdf files are categorized correctly."""
        test_file = tmp_path / "document.pdf"
        test_file.write_text("PDF content")

        content = generate_action_file_content(test_file)
        assert "type: document" in content
        assert "category: document" in content

    def test_categorization_csv_file(self, tmp_path):
        """Test that .csv files are categorized correctly."""
        test_file = tmp_path / "data.csv"
        test_file.write_text("col1,col2\n1,2")

        content = generate_action_file_content(test_file)
        assert "type: data" in content
        assert "category: data" in content

    def test_categorization_image_file(self, tmp_path):
        """Test that .jpg files are categorized correctly."""
        test_file = tmp_path / "photo.jpg"
        test_file.write_text("Image data")

        content = generate_action_file_content(test_file)
        assert "type: image" in content
        assert "category: image" in content

    def test_categorization_unknown_file(self, tmp_path):
        """Test that unknown extensions are categorized as unknown."""
        test_file = tmp_path / "file.xyz"
        test_file.write_text("Unknown content")

        content = generate_action_file_content(test_file)
        assert "type: unknown" in content
        assert "category: unknown" in content

    def test_priority_assignment(self, temp_file):
        """Test that priority is assigned based on category."""
        content = generate_action_file_content(temp_file)
        # Text files should have low priority
        assert "priority: low" in content

    def test_markdown_body_structure(self, temp_file):
        """Test that markdown body contains expected sections."""
        content = generate_action_file_content(temp_file)

        # Check for body sections after frontmatter
        body_start = content.find("---\n", 4) + 4
        body = content[body_start:]

        assert "# Action Required" in body
        assert "**File**:" in body
        assert "**Size**:" in body
        assert "**Category**:" in body

    def test_large_file_handling(self, tmp_path):
        """Test that large files are handled correctly."""
        large_file = tmp_path / "large.bin"
        # Create a 10MB file
        large_file.write_bytes(b"x" * (10 * 1024 * 1024))

        content = generate_action_file_content(large_file)
        assert "size: 10485760" in content

    def test_special_characters_in_filename(self, tmp_path):
        """Test that special characters in filenames are handled."""
        special_file = tmp_path / "file with spaces & symbols!.txt"
        special_file.write_text("Content")

        content = generate_action_file_content(special_file)
        assert "original_name: file with spaces & symbols!.txt" in content

    def test_no_extension_file(self, tmp_path):
        """Test that files without extensions are handled."""
        no_ext_file = tmp_path / "README"
        no_ext_file.write_text("Readme content")

        content = generate_action_file_content(no_ext_file)
        assert "file_type:" in content
        assert "type: unknown" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
