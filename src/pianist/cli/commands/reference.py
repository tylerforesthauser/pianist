"""Reference command handler."""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from ...iterate import composition_to_canonical_json
from ...parser import parse_composition_from_text
from ...reference_db import MusicalReference, get_default_database
from ..util import add_common_flags, read_text, write_text


def setup_parser(subparsers) -> None:
    """Setup the reference command parser."""
    reference = subparsers.add_parser(
        "reference",
        help="Manage musical reference database (add, list, search, get, delete).",
    )
    reference_sub = reference.add_subparsers(dest="reference_cmd", required=True)
    
    # Add reference
    ref_add = reference_sub.add_parser("add", help="Add a composition to the reference database.")
    ref_add.add_argument(
        "-i", "--input",
        dest="in_path",
        type=Path,
        required=True,
        help="Input composition JSON file.",
    )
    ref_add.add_argument(
        "--id",
        type=str,
        default=None,
        help="Reference ID (auto-generated from title if not provided).",
    )
    ref_add.add_argument(
        "--title",
        type=str,
        default=None,
        help="Reference title (uses composition title if not provided).",
    )
    ref_add.add_argument(
        "--description",
        type=str,
        default="",
        help="Description of the reference.",
    )
    ref_add.add_argument(
        "--style",
        type=str,
        default=None,
        help="Musical style (e.g., Baroque, Classical, Romantic, Modern).",
    )
    ref_add.add_argument(
        "--form",
        type=str,
        default=None,
        help="Musical form (e.g., binary, ternary, sonata).",
    )
    ref_add.add_argument(
        "--techniques",
        type=str,
        default=None,
        help="Comma-separated list of techniques (e.g., sequence,inversion,augmentation).",
    )
    add_common_flags(ref_add)
    
    # List references
    ref_list = reference_sub.add_parser("list", help="List all references in the database.")
    add_common_flags(ref_list)
    
    # Search references
    ref_search = reference_sub.add_parser("search", help="Search for references matching criteria.")
    ref_search.add_argument(
        "--style",
        type=str,
        default=None,
        help="Filter by musical style.",
    )
    ref_search.add_argument(
        "--form",
        type=str,
        default=None,
        help="Filter by musical form.",
    )
    ref_search.add_argument(
        "--technique",
        type=str,
        default=None,
        help="Filter by technique.",
    )
    ref_search.add_argument(
        "--title-contains",
        type=str,
        default=None,
        help="Filter by title substring.",
    )
    ref_search.add_argument(
        "--description-contains",
        type=str,
        default=None,
        help="Filter by description substring.",
    )
    ref_search.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10).",
    )
    add_common_flags(ref_search)
    
    # Get reference
    ref_get = reference_sub.add_parser("get", help="Get a reference by ID and output its composition.")
    ref_get.add_argument(
        "id",
        type=str,
        help="Reference ID.",
    )
    ref_get.add_argument(
        "-o", "--output",
        dest="out_path",
        type=Path,
        default=None,
        help="Output JSON path. If omitted, prints to stdout.",
    )
    add_common_flags(ref_get)
    
    # Delete reference
    ref_delete = reference_sub.add_parser("delete", help="Delete a reference from the database.")
    ref_delete.add_argument(
        "id",
        type=str,
        help="Reference ID to delete.",
    )
    add_common_flags(ref_delete)
    
    # Count references
    ref_count = reference_sub.add_parser("count", help="Count total references in the database.")
    add_common_flags(ref_count)


def handle(args: argparse.Namespace) -> int:
    """Handle the reference command."""
    try:
        if args.reference_cmd == "add":
            # Add a reference from a JSON file
            text = read_text(args.in_path)
            comp = parse_composition_from_text(text)
            
            ref_db = get_default_database()
            
            # Generate ID from title if not provided
            ref_id = args.id or comp.title.lower().replace(" ", "_").replace("-", "_")
            
            reference = MusicalReference(
                id=ref_id,
                title=args.title or comp.title or "Untitled",
                description=args.description or "",
                composition=comp,
                style=args.style,
                form=args.form,
                techniques=args.techniques.split(",") if args.techniques else None,
                metadata=None,
            )
            
            ref_db.add_reference(reference)
            sys.stdout.write(f"Added reference: {ref_id}\n")
            return 0
        
        elif args.reference_cmd == "list":
            ref_db = get_default_database()
            references = ref_db.list_all_references()
            
            if not references:
                sys.stdout.write("No references in database.\n")
                return 0
            
            sys.stdout.write(f"Found {len(references)} references:\n\n")
            for ref in references:
                sys.stdout.write(f"ID: {ref.id}\n")
                sys.stdout.write(f"Title: {ref.title}\n")
                if ref.description:
                    sys.stdout.write(f"Description: {ref.description}\n")
                if ref.style:
                    sys.stdout.write(f"Style: {ref.style}\n")
                if ref.form:
                    sys.stdout.write(f"Form: {ref.form}\n")
                if ref.techniques:
                    sys.stdout.write(f"Techniques: {', '.join(ref.techniques)}\n")
                sys.stdout.write("\n")
            
            return 0
        
        elif args.reference_cmd == "search":
            ref_db = get_default_database()
            references = ref_db.search_references(
                style=args.style,
                form=args.form,
                technique=args.technique,
                title_contains=args.title_contains,
                description_contains=args.description_contains,
                limit=args.limit
            )
            
            if not references:
                sys.stdout.write("No matching references found.\n")
                return 0
            
            sys.stdout.write(f"Found {len(references)} matching references:\n\n")
            for ref in references:
                sys.stdout.write(f"ID: {ref.id}\n")
                sys.stdout.write(f"Title: {ref.title}\n")
                if ref.description:
                    sys.stdout.write(f"Description: {ref.description}\n")
                if ref.style:
                    sys.stdout.write(f"Style: {ref.style}\n")
                if ref.form:
                    sys.stdout.write(f"Form: {ref.form}\n")
                if ref.techniques:
                    sys.stdout.write(f"Techniques: {', '.join(ref.techniques)}\n")
                sys.stdout.write("\n")
            
            return 0
        
        elif args.reference_cmd == "get":
            ref_db = get_default_database()
            reference = ref_db.get_reference(args.id)
            
            if reference is None:
                sys.stderr.write(f"Reference '{args.id}' not found.\n")
                return 1
            
            comp_json = composition_to_canonical_json(reference.composition)
            
            if args.out_path:
                write_text(args.out_path, comp_json)
                sys.stdout.write(f"Saved to: {args.out_path}\n")
            else:
                sys.stdout.write(comp_json)
            
            return 0
        
        elif args.reference_cmd == "delete":
            ref_db = get_default_database()
            deleted = ref_db.delete_reference(args.id)
            
            if deleted:
                sys.stdout.write(f"Deleted reference: {args.id}\n")
                return 0
            else:
                sys.stderr.write(f"Reference '{args.id}' not found.\n")
                return 1
        
        elif args.reference_cmd == "count":
            ref_db = get_default_database()
            count = ref_db.count_references()
            sys.stdout.write(f"Total references: {count}\n")
            return 0
        
    except Exception as exc:
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        sys.stderr.write(f"error: {type(exc).__name__}: {exc}\n")
        return 1
    return 0
