#!/usr/bin/env python3
"""Script to add appropriate headings to markdown files that are missing them."""

import os
import re

# Files that need headings with their appropriate titles
files_to_fix = {
    'docs/current-state/core_contribs.md': 'Core Contributors Analysis',
    'docs/integration-guides/tasmota.md': 'Tasmota Integration Guide',
    'docs/integration-guides/top_lighting_integrations.md': 'Top Lighting System Integrations',
    'docs/integration-guides/zha_zwave.md': 'ZHA and Z-Wave Integration',
    'docs/integration-guides/zigbee2mqtt.md': 'Zigbee2MQTT Integration',
    'docs/technical-strategy/esphome_proposal.md': 'ESPHome Enhancement Proposal',
    'docs/technical-strategy/light_state_enhancements.md': 'Light State Management Enhancements',
    'docs/technical-strategy/nonlinear_dimming.md': 'Nonlinear Dimming Strategy',
    'docs/technical-strategy/simultaneous_dimming.md': 'Simultaneous Dimming Control'
}

def add_heading_to_file(file_path, title):
    """Add a top-level heading to the beginning of a file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if it already has a top-level heading
    if content.strip().startswith('# '):
        print(f"File already has heading: {file_path}")
        return False
    
    # Special case for simultaneous_dimming.md which starts with ## 
    if file_path == 'docs/technical-strategy/simultaneous_dimming.md' and content.strip().startswith('## '):
        # Replace the first ## with #
        content = re.sub(r'^## ', '# ', content, count=1)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed heading level in: {file_path}")
        return True
    
    # Add heading to the top
    new_content = f"# {title}\n\n{content}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Added heading to: {file_path}")
    return True

def main():
    """Main function to add headings to all files that need them."""
    total_fixed = 0
    
    for file_path, title in files_to_fix.items():
        if add_heading_to_file(file_path, title):
            total_fixed += 1
    
    print(f"\nFixed headings in {total_fixed} files.")

if __name__ == '__main__':
    main()
