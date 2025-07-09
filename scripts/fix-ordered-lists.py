#!/usr/bin/env python3
"""Script to fix ordered list numbering in markdown files."""

import os
import re
from pathlib import Path

def fix_ordered_lists_in_file(file_path):
    """Fix ordered list numbering in a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts an ordered list
            ordered_list_match = re.match(r'^(\s*)1\.\s+', line)
            if ordered_list_match:
                indent = ordered_list_match.group(1)
                # Start processing the ordered list
                list_counter = 1
                new_lines.append(re.sub(r'^(\s*)1\.', f'{indent}{list_counter}.', line))
                i += 1
                
                # Continue processing subsequent list items with the same indentation
                while i < len(lines):
                    next_line = lines[i]
                    # Check if it's a continuation of the same list level
                    next_match = re.match(rf'^{re.escape(indent)}1\.\s+', next_line)
                    if next_match:
                        list_counter += 1
                        new_lines.append(re.sub(rf'^{re.escape(indent)}1\.', f'{indent}{list_counter}.', next_line))
                        i += 1
                    # Check if it's a sub-list (more indented)
                    elif re.match(rf'^{re.escape(indent)}\s+1\.\s+', next_line):
                        # This is a sub-list, process it recursively
                        sub_indent_match = re.match(rf'^({re.escape(indent)}\s+)1\.\s+', next_line)
                        if sub_indent_match:
                            sub_indent = sub_indent_match.group(1)
                            sub_counter = 1
                            new_lines.append(re.sub(rf'^{re.escape(sub_indent)}1\.', f'{sub_indent}{sub_counter}.', next_line))
                            i += 1
                            
                            # Process the sub-list
                            while i < len(lines):
                                sub_line = lines[i]
                                sub_match = re.match(rf'^{re.escape(sub_indent)}1\.\s+', sub_line)
                                if sub_match:
                                    sub_counter += 1
                                    new_lines.append(re.sub(rf'^{re.escape(sub_indent)}1\.', f'{sub_indent}{sub_counter}.', sub_line))
                                    i += 1
                                elif sub_line.strip() == '' or re.match(rf'^{re.escape(indent)}\S', sub_line) or not sub_line.startswith(indent):
                                    # End of sub-list
                                    break
                                else:
                                    new_lines.append(sub_line)
                                    i += 1
                        else:
                            new_lines.append(next_line)
                            i += 1
                    # Check if it's an empty line or content that continues the list item
                    elif next_line.strip() == '' or (next_line.startswith(indent + ' ') and not re.match(rf'^{re.escape(indent)}\S', next_line)):
                        new_lines.append(next_line)
                        i += 1
                    else:
                        # End of the ordered list
                        break
            else:
                new_lines.append(line)
                i += 1
        
        new_content = '\n'.join(new_lines)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed ordered lists in: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix ordered lists in all markdown files."""
    docs_dir = Path('docs')
    if not docs_dir.exists():
        print("docs directory not found!")
        return
    
    total_fixed = 0
    total_processed = 0
    
    print("Processing markdown files...")
    
    # Process all markdown files in docs directory
    for md_file in docs_dir.rglob('*.md'):
        print(f"Processing: {md_file}")
        total_processed += 1
        if fix_ordered_lists_in_file(md_file):
            total_fixed += 1
    
    # Also check root level markdown files
    root_md_files = ['README.md', 'DOC_VALIDATION.md', 'MARKDOWN_LINTING.md']
    for md_file in root_md_files:
        if os.path.exists(md_file):
            print(f"Processing: {md_file}")
            total_processed += 1
            if fix_ordered_lists_in_file(md_file):
                total_fixed += 1
    
    print(f"\nProcessed {total_processed} files.")
    print(f"Fixed ordered lists in {total_fixed} files.")

if __name__ == '__main__':
    main()
