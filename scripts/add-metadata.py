#!/usr/bin/env python3
"""
Script to add metadata to documentation files for the Universal Smart Lighting Control project.
This script adds YAML frontmatter with descriptions to files that don't already have it.
"""

import os
import re
import yaml

# Metadata for each documentation file
FILE_METADATA = {
    # Current State
    'current-state/community_discussions.md': {
        'description': 'Key community discussions, feature requests, and user feedback that informed this project\'s direction',
        'summary': 'Community discussions and user feedback analysis',
    },
    'current-state/challenges.md': {
        'description': 'Technical challenges, implementation risks, and potential obstacles to address in universal lighting control',
        'summary': 'Technical challenges and implementation risks',
    },
    'current-state/core_contribs.md': {
        'description': 'Key people and teams involved in lighting control development and their contributions to the ecosystem',
        'summary': 'Core contributors and key team members',
    },
    
    # Architecture
    'architecture/pro_concepts.md': {
        'description': 'Fundamental concepts, terminology, and design principles underlying the universal lighting control architecture',
        'summary': 'Fundamental concepts and design principles',
    },
    'architecture/scope.md': {
        'description': 'Detailed scope definition, requirements analysis, and project boundaries for universal lighting control',
        'summary': 'Scope definition and requirements analysis',
    },
    'architecture/project_plan.md': {
        'description': 'High-level project timeline, milestones, and execution strategy for universal lighting control implementation',
        'summary': 'Project timeline and execution strategy',
    },
    
    # Technical Strategy
    'technical-strategy/esphome_proposal.md': {
        'description': 'ESPHome-specific implementation strategy for native device support and protocol integration',
        'summary': 'ESPHome-specific implementation strategy',
    },
    'technical-strategy/esphome_strategy.md': {
        'description': 'Detailed ESPHome technical strategy and integration patterns for universal lighting control',
        'summary': 'Detailed ESPHome technical approach',
    },
    'technical-strategy/light_state_enhancements.md': {
        'description': 'Proposed enhancements to Home Assistant\'s light entity state management and attribute handling',
        'summary': 'Light entity state management improvements',
    },
    'technical-strategy/nonlinear_dimming.md': {
        'description': 'Technical approach to perceptually uniform dimming curves and gamma correction for natural lighting transitions',
        'summary': 'Perceptually uniform dimming curves implementation',
    },
    'technical-strategy/simultaneous_dimming.md': {
        'description': 'Strategy for coordinating simultaneous brightness changes across multiple lights with synchronized transitions',
        'summary': 'Coordinated multi-light brightness control',
    },
    
    # Integration Guides
    'integration-guides/top_lighting_integrations.md': {
        'description': 'Overview of the most popular lighting integrations and their native dimming capabilities and limitations',
        'summary': 'Popular lighting platforms overview',
    },
    'integration-guides/zha_zwave.md': {
        'description': 'Implementation details for Zigbee Home Automation (ZHA) and Z-Wave integrations with native protocol support',
        'summary': 'ZHA and Z-Wave implementation details',
    },
    'integration-guides/zigbee2mqtt.md': {
        'description': 'Integration strategy and native command support for Zigbee2MQTT with move/stop command implementation',
        'summary': 'Zigbee2MQTT integration strategy',
    },
    'integration-guides/tasmota.md': {
        'description': 'Tasmota device integration and dimming control implementation with firmware command support',
        'summary': 'Tasmota device integration approach',
    },
    'integration-guides/tuya.md': {
        'description': 'Tuya Smart and Smart Life integration patterns, limitations, and workaround strategies',
        'summary': 'Tuya integration patterns and limitations',
    },
    
    # Implementation
    'implementation/execution_plan_b.md': {
        'description': 'Alternative implementation approach and contingency planning for universal lighting control deployment',
        'summary': 'Alternative implementation approach',
    },
    
    # Future Enhancements
    'future-enhancements/control_mapping.md': {
        'description': 'Advanced control mapping features for customized dimming behaviors and device-specific optimizations',
        'summary': 'Advanced control mapping and customization',
    },
    'future-enhancements/defaults.md': {
        'description': 'Intelligent default configuration system that automatically detects and configures optimal settings for different controller types',
        'summary': 'Intelligent auto-configuration system',
    },
    
    # Resources
    'resources/kickoff_post.md': {
        'description': 'Original community kickoff post that started this project, including discussion links and community feedback',
        'summary': 'Original project kickoff and community discussion',
    },
}

def has_frontmatter(content):
    """Check if content already has YAML frontmatter."""
    return content.strip().startswith('---\n')

def add_metadata_to_file(file_path, metadata):
    """Add YAML frontmatter metadata to a file if it doesn't already have it."""
    if not os.path.exists(file_path):
        print(f"Warning: File not found: {file_path}")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if has_frontmatter(content):
        print(f"Skipping {file_path} - already has frontmatter")
        return False
    
    # Create YAML frontmatter
    frontmatter = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
    
    # Add frontmatter to the beginning of the file
    new_content = f"---\n{frontmatter}---\n\n{content}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Added metadata to {file_path}")
    return True

def main():
    """Add metadata to all documentation files."""
    docs_dir = 'docs'
    
    if not os.path.exists(docs_dir):
        print(f"Error: {docs_dir} directory not found")
        return
    
    added_count = 0
    
    for relative_path, metadata in FILE_METADATA.items():
        file_path = os.path.join(docs_dir, relative_path)
        if add_metadata_to_file(file_path, metadata):
            added_count += 1
    
    print(f"\nCompleted: Added metadata to {added_count} files")
    print("Files with existing frontmatter were skipped")

if __name__ == '__main__':
    main()
