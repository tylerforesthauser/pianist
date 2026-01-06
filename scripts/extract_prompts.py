#!/usr/bin/env python3
"""
Extract example user prompts from AI_PROMPTING_GUIDE.md and create:
- <Composition Name>.prompt.txt (the actual prompt)
- <Composition Name>.json (a blank json file)
"""

import re
import json
from pathlib import Path


def extract_title_from_prompt(prompt_text: str) -> str:
    """Extract the composition title from the prompt text."""
    # Try to find Title: "..." pattern
    title_match = re.search(r'Title:\s*"([^"]+)"', prompt_text)
    if title_match:
        return title_match.group(1)
    
    # Try to find Title: ... (without quotes)
    title_match = re.search(r'Title:\s*([^\n]+)', prompt_text)
    if title_match:
        return title_match.group(1).strip()
    
    # Try to find "called "..." pattern
    called_match = re.search(r'called\s+"([^"]+)"', prompt_text)
    if called_match:
        return called_match.group(1)
    
    # Fallback: try to find any quoted string that looks like a title
    # Look for patterns like "Something in Key" or "Something - Description"
    quoted_match = re.search(r'"([A-Z][^"]*(?:in|in\s+[A-G][#b]?\s+[A-Z][^"]*|-\s+[^"]*))"', prompt_text)
    if quoted_match:
        return quoted_match.group(1)
    
    return None


def sanitize_filename(name: str) -> str:
    """Convert a composition name to a safe filename."""
    # Remove or replace invalid filename characters
    # Keep alphanumeric, spaces, hyphens, underscores
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def extract_prompts_from_markdown(markdown_path: Path) -> list[tuple[str, str]]:
    """
    Extract all prompts from the markdown file.
    Returns list of (title, prompt_text) tuples.
    """
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    prompts = []
    
    # Find all code blocks (with or without language tags)
    # Pattern matches: ``` or ```language followed by content and closing ```
    code_block_pattern = r'```[^\n]*\n(.*?)\n```'
    code_blocks = re.finditer(code_block_pattern, content, re.DOTALL)
    
    for match in code_blocks:
        block_content = match.group(1).strip()
        
        # Skip JSON examples and bash commands
        if block_content.startswith('{') or block_content.startswith('#') or 'bpm' in block_content[:50]:
            continue
        
        # Check if this looks like a user prompt (not a JSON example or other code)
        if any(block_content.startswith(prefix) for prefix in [
            'Compose a',
            'Compose an',
            'Create a',
            'Create an',
            "I'd like",
            'Title:'
        ]):
            # Extract title
            title = extract_title_from_prompt(block_content)
            if title:
                prompts.append((title, block_content))
            else:
                # If we can't extract a title, skip this prompt
                print(f"Warning: Could not extract title from prompt:\n{block_content[:100]}...")
    
    return prompts


def main():
    guide_path = Path(__file__).parent / 'AI_PROMPTING_GUIDE.md'
    output_dir = Path(__file__).parent / 'output'
    
    if not guide_path.exists():
        print(f"Error: {guide_path} not found")
        return
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Extract prompts
    prompts = extract_prompts_from_markdown(guide_path)
    
    print(f"Found {len(prompts)} prompts")
    
    # Create files for each prompt
    for title, prompt_text in prompts:
        safe_name = sanitize_filename(title)
        prompt_file = output_dir / f"{safe_name}.prompt.txt"
        json_file = output_dir / f"{safe_name}.json"
        
        # Write prompt file
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_text)
        
        # Write empty JSON file
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write('{}\n')
        
        print(f"Created: {safe_name}.prompt.txt and {safe_name}.json")
    
    print(f"\nDone! Created {len(prompts)} prompt/JSON pairs in {output_dir}")


if __name__ == '__main__':
    main()

