"""
MkDocs plugin to automatically generate a complete table of contents.
This plugin scans all markdown files and extracts metadata for descriptions.
"""

import os
import re
import yaml
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options


class AutoTocPlugin(BasePlugin):
    """Plugin to auto-generate table of contents from navigation structure and file metadata."""
    
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
        toc_content = self._generate_toc(config.get('nav', []), config['docs_dir'])
        
        # Replace marker with generated content
        return markdown.replace(marker, toc_content)
    
    def _generate_toc(self, nav_items, docs_dir, level=0):
        """Generate TOC content from navigation structure and file metadata."""
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
                                        desc = self._get_page_description(sub_path, sub_title, docs_dir)
                                        content.append(f"{indent}| [{sub_title}]({sub_path}) | {desc} |")
                        
                        content.append("")
                        
                    elif isinstance(value, str):
                        # Single page
                        indent = "  " * level
                        desc = self._get_page_description(value, title, docs_dir)
                        content.append(f"{indent}- [{title}]({value}) - {desc}")
        
        return "\n".join(content)
    
    def _get_page_description(self, path, title, docs_dir):
        """Extract description from page metadata or return default."""
        file_path = os.path.join(docs_dir, path)
        
        if not os.path.exists(file_path):
            return f"Documentation for {title}"
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Try to extract frontmatter first
            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if frontmatter_match:
                try:
                    frontmatter = yaml.safe_load(frontmatter_match.group(1))
                    if isinstance(frontmatter, dict):
                        # Check for various description fields
                        for field in ['description', 'summary', 'abstract', 'desc']:
                            if field in frontmatter:
                                return frontmatter[field]
                except yaml.YAMLError:
                    pass
            
            # Look for description metadata comment
            desc_match = re.search(r'<!--\s*description:\s*(.+?)\s*-->', content, re.IGNORECASE)
            if desc_match:
                return desc_match.group(1).strip()
                
            # Look for summary metadata comment  
            summary_match = re.search(r'<!--\s*summary:\s*(.+?)\s*-->', content, re.IGNORECASE)
            if summary_match:
                return summary_match.group(1).strip()
                
            # Fallback: extract first paragraph after title
            lines = content.split('\n')
            in_content = False
            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    in_content = True
                    continue
                if in_content and line and not line.startswith('#') and not line.startswith('<!--'):
                    # Clean up markdown formatting
                    clean_line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)  # Remove links
                    clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_line)  # Remove bold
                    clean_line = re.sub(r'\*([^*]+)\*', r'\1', clean_line)      # Remove italic
                    if len(clean_line) > 20:  # Only use substantial descriptions
                        return clean_line[:100] + ('...' if len(clean_line) > 100 else '')
                        
        except Exception as e:
            print(f"Warning: Could not read metadata from {file_path}: {e}")
            
        return f"Documentation for {title}"
