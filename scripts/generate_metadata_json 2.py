#!/usr/bin/env python3
"""
Generate metadata JSON file for a MIDI file.

This script creates a companion JSON file (filename.mid.json) with metadata
that the review script can use to identify the composition.

Usage:
    # Interactive mode (prompts for information)
    python scripts/generate_metadata_json.py file.mid

    # Non-interactive mode (command-line arguments)
    python scripts/generate_metadata_json.py file.mid \\
        --composer "Scott Joplin" \\
        --title "Maple Leaf Rag" \\
        --style "Ragtime" \\
        --form "ragtime" \\
        --techniques "syncopation,stride_bass" \\
        --description "Classic ragtime piece demonstrating syncopation"

    # Update existing JSON file
    python scripts/generate_metadata_json.py file.mid --update

    # Show template/example
    python scripts/generate_metadata_json.py --template
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Metadata JSON schema template
# Only composer and title are required. Other fields are optional and will be
# determined automatically during the review process.
METADATA_TEMPLATE = {
    "composer": None,  # Required
    "title": None,  # Required
    "catalog_number": None,  # Optional (BWV, K., etc.)
    "opus": None,  # Optional (Op. 28 No. 7)
    "style": None,  # Optional (Baroque, Classical, Romantic, etc.)
    "form": None,  # Optional (binary, ternary, sonata, etc.)
    "techniques": [],  # Optional (list of strings)
    "description": "",  # Optional
    "year": None,  # Optional
    "source": None,  # Optional
    "notes": None,  # Optional
}


def load_existing_metadata(json_path: Path) -> dict[str, any]:
    """Load existing metadata JSON if it exists."""
    if json_path.exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {json_path}: {e}", file=sys.stderr)
            return {}
        except Exception as e:
            print(f"Warning: Could not load {json_path}: {e}", file=sys.stderr)
            return {}
    return {}


def prompt_for_value(prompt: str, default: str | None = None, required: bool = False) -> str | None:
    """Prompt user for a value."""
    full_prompt = f"{prompt} [{default}]: " if default else f"{prompt}: "

    while True:
        value = input(full_prompt).strip()
        if value:
            return value
        elif default:
            return default
        elif not required:
            return None
        else:
            print("This field is required. Please enter a value.")


def prompt_for_list(prompt: str, default: list[str] | None = None) -> list[str]:
    """Prompt user for a comma-separated list."""
    if default:
        default_str = ", ".join(default)
        full_prompt = f"{prompt} [{default_str}]: "
    else:
        full_prompt = f"{prompt} (comma-separated): "

    value = input(full_prompt).strip()
    if value:
        return [item.strip() for item in value.split(",") if item.strip()]
    elif default:
        return default
    return []


def prompt_for_int(prompt: str, default: int | None = None) -> int | None:
    """Prompt user for an integer."""
    full_prompt = f"{prompt} [{default}]: " if default is not None else f"{prompt}: "

    while True:
        value = input(full_prompt).strip()
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid integer.")


def generate_metadata_interactive(
    midi_path: Path, existing: dict[str, any] | None = None
) -> dict[str, any]:
    """Generate metadata interactively.

    Only composer and title are required. All other fields will be determined
    by AI during the review process.
    """
    if existing is None:
        existing = {}

    print(f"\nGenerating metadata for: {midi_path.name}")
    print("\nOnly composer and title are required.")
    print("Other fields (style, form, techniques, description, etc.) are optional")
    print("and will be determined automatically during the review process.\n")
    print("Press Enter to use default value or skip optional fields.\n")

    metadata = {}

    # Required fields
    metadata["composer"] = prompt_for_value(
        "Composer (required)", default=existing.get("composer"), required=True
    )

    metadata["title"] = prompt_for_value(
        "Title (required)", default=existing.get("title"), required=True
    )

    # Optional fields
    print("\nOptional fields:")

    metadata["source"] = prompt_for_value(
        "Source (e.g., 'Public domain', 'IMSLP', etc.) - Optional", default=existing.get("source")
    )

    metadata["notes"] = prompt_for_value(
        "Additional notes - Optional", default=existing.get("notes")
    )

    # Note: Other fields (catalog_number, opus, style, form, techniques, description, year)
    # are not prompted - they will be determined automatically during review

    # Clean up None values
    metadata = {k: v for k, v in metadata.items() if v is not None and v != ""}

    return metadata


def generate_metadata_from_args(
    args: argparse.Namespace, existing: dict[str, any] | None = None
) -> dict[str, any]:
    """Generate metadata from command-line arguments.

    Only composer and title are required. Other fields are optional and will be
    determined automatically during the review process.
    """
    if existing is None:
        existing = {}

    metadata = {}

    # Required fields
    metadata["composer"] = args.composer or existing.get("composer")
    metadata["title"] = args.title or existing.get("title")

    if not metadata["composer"] or not metadata["title"]:
        print("Error: Both --composer and --title are required.", file=sys.stderr)
        sys.exit(1)

    # Optional user-provided fields (AI will determine others)
    if args.source:
        metadata["source"] = args.source
    elif existing.get("source"):
        metadata["source"] = existing["source"]

    if args.notes:
        metadata["notes"] = args.notes
    elif existing.get("notes"):
        metadata["notes"] = existing["notes"]

    # Note: Other fields (catalog_number, opus, style, form, techniques, description, year)
    # are not set here - they will be determined automatically during review

    return metadata


def save_metadata(json_path: Path, metadata: dict[str, any], update: bool = False) -> None:
    """Save metadata to JSON file."""
    if json_path.exists() and not update:
        response = input(f"{json_path} already exists. Overwrite? [y/N]: ").strip().lower()
        if response != "y":
            print("Cancelled.")
            return

    # Ensure required fields
    if not metadata.get("composer") or not metadata.get("title"):
        print("Error: Both composer and title are required.", file=sys.stderr)
        sys.exit(1)

    # Write JSON file with pretty formatting
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved metadata to {json_path}")


def show_template() -> None:
    """Show metadata template/example."""
    example_minimal = {"composer": "Scott Joplin", "title": "Maple Leaf Rag"}

    example_with_optional = {
        "composer": "Scott Joplin",
        "title": "Maple Leaf Rag",
        "source": "Public domain",
        "notes": "Essential example of ragtime form",
    }

    print("Metadata JSON Template/Example:\n")
    print("Minimal (required fields only):")
    print(json.dumps(example_minimal, indent=2, ensure_ascii=False))
    print("\nWith optional user-provided fields:")
    print(json.dumps(example_with_optional, indent=2, ensure_ascii=False))
    print("\nRequired fields: composer, title")
    print("\nOptional user fields: source, notes")
    print("\nAuto-determined fields (added during review):")
    print("  - catalog_number, opus, style, form, techniques, description, year")
    print("\nNote: All fields except composer and title will be determined automatically")
    print("during the review process. You only need to provide composer and title.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate metadata JSON file for a MIDI file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python scripts/generate_metadata_json.py file.mid

  # Non-interactive mode (only composer and title required)
  python scripts/generate_metadata_json.py file.mid \\
      --composer "Scott Joplin" \\
      --title "Maple Leaf Rag"

  # Update existing JSON
  python scripts/generate_metadata_json.py file.mid --update

  # Show template
  python scripts/generate_metadata_json.py --template
        """,
    )

    parser.add_argument(
        "midi_file", nargs="?", type=Path, help="MIDI file to generate metadata for"
    )

    parser.add_argument("--composer", help="Composer name")

    parser.add_argument("--title", help="Work title")

    # Note: catalog_number, opus, style, form, techniques, description, year are not
    # command-line options - they will be determined automatically during review.
    # Only source and notes remain as optional user-provided fields.

    parser.add_argument("--source", help="Source of the MIDI file")

    parser.add_argument("--notes", help="Additional notes")

    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing JSON file (preserves existing values)",
    )

    parser.add_argument(
        "--template", action="store_true", help="Show metadata template/example and exit"
    )

    args = parser.parse_args()

    if args.template:
        show_template()
        return

    if not args.midi_file:
        parser.error("MIDI file is required (or use --template to see example)")

    midi_path = Path(args.midi_file)
    if not midi_path.exists():
        print(f"Error: File not found: {midi_path}", file=sys.stderr)
        sys.exit(1)

    json_path = midi_path.with_suffix(midi_path.suffix + ".json")

    # Load existing metadata if updating
    existing = None
    if args.update or json_path.exists():
        existing = load_existing_metadata(json_path)

    # Generate metadata
    if args.composer or args.title:
        # Non-interactive mode
        metadata = generate_metadata_from_args(args, existing)
    else:
        # Interactive mode
        metadata = generate_metadata_interactive(midi_path, existing)

    # Save metadata
    save_metadata(json_path, metadata, update=args.update)


if __name__ == "__main__":
    main()
