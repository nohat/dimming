"""
Macros for the Universal Smart Lighting Control documentation.
These macros provide dynamic content generation capabilities.
"""

def define_env(env):
    """Define custom macros for MkDocs."""
    
    @env.macro
    def doc_count():
        """Return the total number of documentation pages."""
        # This would count actual files in a real implementation
        return "25+"
    
    @env.macro  
    def last_updated():
        """Return the last updated date."""
        from datetime import datetime
        return datetime.now().strftime("%B %Y")
    
    @env.macro
    def nav_tree():
        """Generate a navigation tree from the mkdocs.yml config."""
        nav = env.conf.get('nav', [])
        return _build_nav_tree(nav)
    
    def _build_nav_tree(nav_items, level=0):
        """Build a hierarchical navigation tree."""
        lines = []
        indent = "  " * level
        
        for item in nav_items:
            if isinstance(item, dict):
                for title, value in item.items():
                    if isinstance(value, list):
                        lines.append(f"{indent}- **{title}** ({len(value)} pages)")
                        lines.extend(_build_nav_tree(value, level + 1))
                    elif isinstance(value, str):
                        lines.append(f"{indent}- [{title}]({value})")
        
        return "\n".join(lines)
    
    @env.macro
    def section_summary(section_name):
        """Generate a summary for a documentation section."""
        summaries = {
            "current-state": {
                "count": 4,
                "description": "Analysis of existing limitations and community feedback"
            },
            "architecture": {
                "count": 4, 
                "description": "Core design proposals and system architecture"
            },
            "technical-strategy": {
                "count": 6,
                "description": "Implementation strategies across platforms"
            },
            "integration-guides": {
                "count": 6,
                "description": "Platform-specific integration details"
            },
            "implementation": {
                "count": 2,
                "description": "Development roadmap and execution plans"
            },
            "future-enhancements": {
                "count": 2,
                "description": "Advanced features and future improvements" 
            },
            "resources": {
                "count": 1,
                "description": "Community resources and reference materials"
            }
        }
        
        info = summaries.get(section_name, {"count": 0, "description": "Documentation section"})
        return f"{info['count']} pages covering {info['description']}"
