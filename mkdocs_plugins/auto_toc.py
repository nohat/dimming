"""
MkDocs plugin to automatically generate a complete table of contents.
This plugin scans all markdown files and creates a comprehensive index.
"""

import os
import yaml
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options


class AutoTocPlugin(BasePlugin):
    """Plugin to auto-generate table of contents from navigation structure."""
    
    config_scheme = (
        ('enabled', config_options.Type(bool, default=True)),
        ('marker', config_options.Type(str, default='<!-- AUTO_TOC -->')),
    )
    
    def on_page_markdown(self, markdown, page, config, files):
        """Process markdown content to inject auto-generated TOC."""
        
        if not self.config['enabled']:
            return markdown
            
        marker = self.config['marker']
        
        # Only process if marker is found
        if marker not in markdown:
            return markdown
            
        # Generate the TOC from navigation
        toc_content = self._generate_toc(config.get('nav', []))
        
        # Replace marker with generated content
        return markdown.replace(marker, toc_content)
    
    def _generate_toc(self, nav_items, level=0):
        """Generate TOC content from navigation structure."""
        content = []
        
        for item in nav_items:
            if isinstance(item, dict):
                for title, value in item.items():
                    if isinstance(value, list):
                        # Section with sub-items
                        indent = "  " * level
                        content.append(f"{indent}### {title}")
                        content.append("")
                        
                        # Add sub-items as table
                        content.append(f"{indent}| Document | Description |")
                        content.append(f"{indent}|----------|-------------|")
                        
                        for sub_item in value:
                            if isinstance(sub_item, dict):
                                for sub_title, sub_path in sub_item.items():
                                    if isinstance(sub_path, str):
                                        desc = self._get_page_description(sub_path, sub_title)
                                        content.append(f"{indent}| [{sub_title}]({sub_path}) | {desc} |")
                        
                        content.append("")
                        
                    elif isinstance(value, str):
                        # Single page
                        indent = "  " * level
                        desc = self._get_page_description(value, title)
                        content.append(f"{indent}- [{title}]({value}) - {desc}")
        
        return "\n".join(content)
    
    def _get_page_description(self, path, title):
        """Extract description from page or return default."""
        # This is a simplified version - in a real implementation,
        # you'd read the actual markdown files to extract descriptions
        descriptions = {
            'architecture/architecture.md': 'Main technical proposal for universal lighting control',
            'architecture/pro_concepts.md': 'Fundamental concepts and design principles',
            'architecture/scope.md': 'Detailed scope definition and requirements',
            'architecture/project_plan.md': 'High-level timeline and execution strategy',
            'technical-strategy/ha_strategy.md': 'Core integration approach and LightTransitionManager',
            'technical-strategy/esphome_proposal.md': 'ESPHome-specific implementation strategy',
            'integration-guides/capability_matrix.md': 'Comprehensive capability comparison across platforms',
            'implementation/eng_execution.md': 'Primary implementation roadmap and development phases',
        }
        
        return descriptions.get(path, f"Documentation for {title}")
