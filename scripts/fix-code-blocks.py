#!/usr/bin/env python3
"""Script to automatically add language tags to fenced code blocks."""

import re
import os
import glob

def fix_code_blocks(file_path):
    """Fix code blocks in a markdown file by adding appropriate language tags."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track if we made any changes
    changes_made = False
    
    # Split content by lines for easier processing
    lines = content.split('\n')
    result_lines = []
    
    for i, line in enumerate(lines):
        # Check if this is a bare ``` line
        if line.strip() == '```':
            # Look at the next few lines to determine the language
            next_lines = lines[i+1:i+5] if i+1 < len(lines) else []
            
            # Determine language based on content
            language = 'text'  # default
            
            for next_line in next_lines:
                next_line = next_line.strip()
                if not next_line:
                    continue
                    
                # YAML patterns
                if any(x in next_line for x in ['service:', 'data:', 'target:', 'entity_id:']):
                    language = 'yaml'
                    break
                # Python patterns
                elif any(x in next_line for x in ['def ', 'import ', 'class ', 'from ', 'print(']):
                    language = 'python'
                    break
                # C++ patterns  
                elif any(x in next_line for x in ['#include', 'void ', 'int ', 'Serial.', 'digitalWrite']):
                    language = 'cpp'
                    break
                # Bash patterns
                elif any(x in next_line for x in ['#!/bin/', 'echo ', 'cd ', 'mkdir', 'ls ', 'make ']):
                    language = 'bash'
                    break
                # JSON patterns
                elif next_line.startswith('{') or next_line.startswith('['):
                    language = 'json'
                    break
                # Mermaid diagrams
                elif any(x in next_line for x in ['graph ', 'flowchart', 'sequenceDiagram']):
                    language = 'mermaid'
                    break
            
            # Replace the bare ``` with language-tagged version
            result_lines.append(f'```{language}')
            changes_made = True
        else:
            result_lines.append(line)
    
    if changes_made:
        # Write back the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(result_lines))
        print(f"Fixed code blocks in: {file_path}")
        return True
    
    return False

def main():
    """Main function to process all markdown files."""
    # Find all markdown files
    markdown_files = glob.glob('docs/**/*.md', recursive=True)
    markdown_files.extend(glob.glob('*.md'))
    
    total_fixed = 0
    for file_path in markdown_files:
        if os.path.exists(file_path):
            if fix_code_blocks(file_path):
                total_fixed += 1
    
    print(f"\nFixed code blocks in {total_fixed} files.")

if __name__ == '__main__':
    main()
