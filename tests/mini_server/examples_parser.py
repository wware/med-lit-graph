#!/usr/bin/env python3
"""
Parse EXAMPLES.md to extract curl examples for the demo UI.

This module parses the client/curl/EXAMPLES.md file to extract:
- Example titles
- JSON query payloads
- Expected responses

The extracted data is used to populate the dropdown in the web UI.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List


def parse_examples_md(examples_md_path: Path) -> List[Dict[str, Any]]:
    """
    Parse EXAMPLES.md and extract query examples.
    
    Args:
        examples_md_path: Path to the EXAMPLES.md file
        
    Returns:
        List of example dictionaries with 'title', 'query', and optionally 'expected_response'
    """
    with open(examples_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    examples = []
    
    # Split content by example sections
    # Look for headers like "## Example 1: ..." or "## Example 2: ..."
    example_pattern = r'## (Example \d+:.*?)(?=\n##|\Z)'
    example_matches = re.finditer(example_pattern, content, re.DOTALL)
    
    for match in example_matches:
        example_section = match.group(0)
        title_raw = match.group(1).strip()
        
        # Clean up the title - extract just the main heading without markdown
        # Remove everything after the first newline or markdown code block
        title = title_raw.split('\n')[0].strip()
        
        # Extract curl commands with JSON payloads
        # Look for JSON in single quotes first
        json_pattern = r'-d\s+\'({.*?})\''
        
        # Try to find JSON in single quotes first
        json_match = re.search(json_pattern, example_section, re.DOTALL)
        
        if not json_match:
            # Try double quotes or no quotes
            json_pattern_alt = r'-d\s+"({.*?})"'
            json_match = re.search(json_pattern_alt, example_section, re.DOTALL)
        
        if not json_match:
            # Try JSON without quotes (multiline)
            json_pattern_block = r'-d\s+\'?\s*({[^}]*(?:{[^}]*}[^}]*)*})'
            json_match = re.search(json_pattern_block, example_section, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1).strip()
            
            try:
                # Parse JSON to validate and pretty-print
                query_json = json.loads(json_str)
                
                # Look for expected response
                expected_response = None
                response_pattern = r'```json\s*\n({\s*"results".*?})\s*```'
                response_match = re.search(response_pattern, example_section, re.DOTALL)
                
                if response_match:
                    try:
                        expected_response = json.loads(response_match.group(1))
                    except json.JSONDecodeError:
                        pass
                
                example = {
                    'title': title,
                    'query': query_json,
                }
                
                if expected_response:
                    example['expected_response'] = expected_response
                
                examples.append(example)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON in {title}: {e}")
                continue
    
    return examples


def generate_examples_json(examples_md_path: Path, output_path: Path) -> None:
    """
    Parse EXAMPLES.md and generate examples.json file.
    
    Args:
        examples_md_path: Path to EXAMPLES.md
        output_path: Path to write examples.json
    """
    examples = parse_examples_md(examples_md_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2)
    
    print(f"Generated {output_path} with {len(examples)} examples")


def main():
    """Generate examples.json from EXAMPLES.md"""
    # Determine paths
    script_dir = Path(__file__).parent
    examples_md = script_dir.parent.parent / "client" / "curl" / "EXAMPLES.md"
    output_json = script_dir / "static" / "examples.json"
    
    if not examples_md.exists():
        print(f"Error: {examples_md} not found")
        return
    
    generate_examples_json(examples_md, output_json)


if __name__ == "__main__":
    main()
