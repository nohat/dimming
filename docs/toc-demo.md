---
description: Demonstration of the automatic table of contents generation system using embedded metadata
summary: Example page showing how metadata-driven TOC generation works
---

# Auto-Generated Table of Contents Demo

This page demonstrates the automatic table of contents generation system that reads metadata from each documentation file.

## How It Works

The system supports multiple metadata formats:

### 1. YAML Frontmatter (Recommended)
```yaml
---
description: Your page description here
summary: Short summary for TOC
priority: essential|important|reference
---
```

### 2. HTML Comments (Alternative)
```html
<!-- description: Your page description here -->
<!-- summary: Short summary for TOC -->
```

### 3. Automatic Extraction (Fallback)
If no metadata is found, the system automatically extracts the first meaningful paragraph after the page title.

## Complete Documentation Index

<!-- AUTO_TOC -->

## Benefits of Metadata-Driven TOC

1. **Accurate Descriptions** - Each page controls its own description
2. **Maintainable** - No need to update a central file when content changes
3. **Flexible** - Supports multiple metadata formats
4. **Automatic Fallback** - Works even without explicit metadata
5. **Priority Support** - Can categorize documents by importance

## Adding Metadata to Your Pages

To add a page to the auto-generated TOC with a custom description:

1. Add YAML frontmatter at the top of your markdown file
2. Include a `description` field for the TOC
3. Optionally add `summary` and `priority` fields
4. Place the `<!-- AUTO_TOC -->` marker where you want the TOC to appear

The system will automatically scan all files referenced in the navigation and extract their metadata for the table of contents.
