#!/usr/bin/env python3
"""Script to fix remaining markdown linting issues."""

import os
import re

def fix_horizontal_rules(file_path):
    """Fix horizontal rule styles in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace various horizontal rule styles with standard ---
    original_content = content
    
    # Replace long underscores
    content = re.sub(r'^_{4,}$', '---', content, flags=re.MULTILINE)
    
    # Replace short dashes with standard
    content = re.sub(r'^-{4}$', '---', content, flags=re.MULTILINE)
    content = re.sub(r'^-{5}$', '---', content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed horizontal rules in: {file_path}")
        return True
    return False

def fix_heading_increments(file_path):
    """Fix heading increment issues by promoting headings."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    result_lines = []
    changed = False
    
    # Track heading levels
    current_level = 1  # We assume first heading is h1
    
    for line in lines:
        if line.startswith('#'):
            # Count the heading level
            level = 0
            for char in line:
                if char == '#':
                    level += 1
                else:
                    break
            
            # If this is jumping more than one level, fix it
            if level > current_level + 1:
                # Promote to the next valid level
                new_level = current_level + 1
                new_line = '#' * new_level + line[level:]
                result_lines.append(new_line)
                current_level = new_level
                changed = True
                print(f"  Fixed heading: {line.strip()} -> {new_line.strip()}")
            else:
                result_lines.append(line)
                current_level = level
        else:
            result_lines.append(line)
    
    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(result_lines))
        print(f"Fixed heading increments in: {file_path}")
        return True
    return False

def fix_ordered_lists(file_path):
    """Fix ordered list numbering issues."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    result_lines = []
    changed = False
    in_list = False
    list_counter = 1
    
    for line in lines:
        # Check if this is an ordered list item
        if re.match(r'^\s*\d+\.\s', line):
            if not in_list:
                in_list = True
                list_counter = 1
            
            # Replace with correct number
            indent = len(line) - len(line.lstrip())
            rest = re.sub(r'^\s*\d+\.', '', line)
            new_line = ' ' * indent + f'{list_counter}.' + rest
            result_lines.append(new_line)
            list_counter += 1
            changed = True
        else:
            # Not a list item
            if in_list and line.strip() == '':
                # Empty line might continue the list
                result_lines.append(line)
            elif in_list:
                # Non-list content, reset counter
                in_list = False
                list_counter = 1
                result_lines.append(line)
            else:
                result_lines.append(line)
    
    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(result_lines))
        print(f"Fixed ordered lists in: {file_path}")
        return True
    return False

# Files that need specific fixes
files_with_hr_issues = [
    'docs/index.md',
    'docs/integration-guides/tasmota.md',
    'docs/integration-guides/top_lighting_integrations.md',
    'docs/technical-strategy/light_state_enhancements.md'
]

files_with_heading_issues = [
    'docs/index.md',
    'docs/integration-guides/capability_matrix.md',
    'docs/current-state/core_contribs.md',
    'docs/integration-guides/zha_zwave.md',
    'docs/technical-strategy/light_state_enhancements.md',
    'docs/technical-strategy/nonlinear_dimming.md'
]

files_with_list_issues = [
    'docs/future-enhancements/defaults.md'
]

def main():
    """Main function to fix various markdown issues."""
    total_fixed = 0
    
    print("Fixing horizontal rules...")
    for file_path in files_with_hr_issues:
        if os.path.exists(file_path) and fix_horizontal_rules(file_path):
            total_fixed += 1
    
    print("\nFixing heading increments...")
    for file_path in files_with_heading_issues:
        if os.path.exists(file_path) and fix_heading_increments(file_path):
            total_fixed += 1
    
    print("\nFixing ordered lists...")
    for file_path in files_with_list_issues:
        if os.path.exists(file_path) and fix_ordered_lists(file_path):
            total_fixed += 1
    
    print(f"\nFixed issues in {total_fixed} files.")

if __name__ == '__main__':
    main()
