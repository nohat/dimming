#!/usr/bin/env python3
"""Script to fix long lines in markdown files by wrapping them appropriately."""

import os
import re
import textwrap
from pathlib import Path

MAX_LINE_LENGTH = 120

def wrap_markdown_line(line, max_length=MAX_LINE_LENGTH):
    """
    Wrap a markdown line while preserving formatting.
    """
    # Don't wrap certain lines
    if (line.strip().startswith('```') or  # Code blocks
        line.strip().startswith('|') or    # Tables
        line.strip().startswith('#') or    # Headers
        line.strip().startswith('<!--') or # Comments
        line.strip().startswith('http') or # URLs
        line.strip().startswith('[') and '](http' in line or # Links
        len(line.strip()) <= max_length):  # Already short enough
        return [line]
    
    # Handle list items
    list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+', line)
    if list_match:
        indent = list_match.group(1)
        marker = list_match.group(2)
        content = line[len(list_match.group(0)):]
        
        if len(line) <= max_length:
            return [line]
        
        # Wrap the content
        wrapped = textwrap.fill(
            content,
            width=max_length - len(indent) - len(marker) - 1,
            subsequent_indent=indent + ' ' * (len(marker) + 1)
        )
        
        # Reconstruct with proper list formatting
        lines = wrapped.split('\n')
        result = [f"{indent}{marker} {lines[0]}"]
        result.extend(lines[1:])
        return result
    
    # Handle quoted text (blockquotes)
    if line.strip().startswith('>'):
        quote_match = re.match(r'^(\s*>+\s*)', line)
        if quote_match:
            prefix = quote_match.group(1)
            content = line[len(prefix):]
            
            if len(line) <= max_length:
                return [line]
            
            wrapped = textwrap.fill(
                content,
                width=max_length - len(prefix),
                subsequent_indent=' ' * len(prefix)
            )
            
            lines = wrapped.split('\n')
            return [prefix + lines[0]] + [' ' * len(prefix) + l for l in lines[1:]]
    
    # Handle regular paragraphs
    # Check if this looks like a paragraph (not starting with special chars)
    if not re.match(r'^\s*[>#*-+\d]', line) and line.strip():
        # Find leading whitespace
        leading_space = len(line) - len(line.lstrip())
        indent = line[:leading_space]
        content = line[leading_space:]
        
        if len(line) <= max_length:
            return [line]
        
        # Try to break at sentence boundaries first
        sentences = re.split(r'(\.\s+)', content)
        if len(sentences) > 1:
            current_line = indent
            result = []
            
            for i, part in enumerate(sentences):
                test_line = current_line + part if current_line == indent else current_line + part
                
                if len(test_line) <= max_length:
                    current_line += part
                else:
                    if current_line.strip():
                        result.append(current_line.rstrip())
                    current_line = indent + part
            
            if current_line.strip():
                result.append(current_line.rstrip())
            
            return result if len(result) > 1 else [line]
        
        # Fallback to regular text wrapping
        wrapped = textwrap.fill(
            content,
            width=max_length - leading_space,
            subsequent_indent=indent
        )
        return wrapped.split('\n')
    
    # For everything else, don't wrap
    return [line]

def fix_long_lines_in_file(file_path):
    """Fix long lines in a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        in_code_block = False
        
        for line in lines:
            line = line.rstrip('\n\r')
            
            # Track code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                new_lines.append(line)
                continue
            
            # Don't wrap lines inside code blocks
            if in_code_block:
                new_lines.append(line)
                continue
            
            # Don't wrap if line contains URLs that would break
            if 'http' in line and ('](http' in line or line.strip().startswith('http')):
                new_lines.append(line)
                continue
            
            # Wrap the line if it's too long
            if len(line) > MAX_LINE_LENGTH:
                wrapped_lines = wrap_markdown_line(line, MAX_LINE_LENGTH)
                new_lines.extend(wrapped_lines)
            else:
                new_lines.append(line)
        
        # Write back to file
        new_content = '\n'.join(new_lines) + '\n'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Fixed long lines in: {file_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix long lines in all markdown files."""
    docs_dir = Path('docs')
    if not docs_dir.exists():
        print("docs directory not found!")
        return
    
    total_fixed = 0
    total_processed = 0
    
    print("Processing markdown files for long lines...")
    
    # Process all markdown files in docs directory
    for md_file in docs_dir.rglob('*.md'):
        print(f"Processing: {md_file}")
        total_processed += 1
        if fix_long_lines_in_file(md_file):
            total_fixed += 1
    
    # Also check root level markdown files
    root_md_files = ['README.md', 'DOC_VALIDATION.md', 'MARKDOWN_LINTING.md']
    for md_file in root_md_files:
        if os.path.exists(md_file):
            print(f"Processing: {md_file}")
            total_processed += 1
            if fix_long_lines_in_file(md_file):
                total_fixed += 1
    
    print(f"\nProcessed {total_processed} files.")
    print(f"Fixed long lines in {total_fixed} files.")

if __name__ == '__main__':
    main()
