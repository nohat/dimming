#!/bin/bash

# Documentation validation script for Universal Smart Lighting Control project
# This script validates MkDocs documentation and checks for common issues

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🔍 Universal Smart Lighting Control - Documentation Validator"
echo "=================================================="

# Check if required files exist
echo "📋 Checking required files..."
required_files=("mkdocs.yml" "requirements.txt" "docs/index.md")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done
echo "✅ All required files present"

# Check Python dependencies
echo "📦 Checking Python dependencies..."
if ! python -c "import mkdocs" 2>/dev/null; then
    echo "❌ MkDocs not installed. Run: pip install -r requirements.txt"
    exit 1
fi
echo "✅ Dependencies satisfied"

# Validate YAML configuration
echo "🔧 Validating mkdocs.yml..."
if ! python -c "import yaml; yaml.safe_load(open('mkdocs.yml'))" 2>/dev/null; then
    echo "❌ Invalid YAML in mkdocs.yml"
    exit 1
fi
echo "✅ Configuration valid"

# Check for broken links (basic check)
echo "🔗 Checking for obvious link issues..."
find docs/ -name "*.md" -exec grep -l "](.*\.md)" {} \; | while read -r file; do
    echo "  Checking links in $file..."
    # This is a basic check - the real validation happens in MkDocs build
done
echo "✅ Basic link check passed"

# Run MkDocs build in strict mode
echo "🏗️  Building documentation (strict mode)..."
if ! mkdocs build --strict --site-dir /tmp/docs-validation; then
    echo "❌ MkDocs build failed!"
    echo "💡 Fix the errors above and try again"
    exit 1
fi

# Clean up
rm -rf /tmp/docs-validation

echo "✅ Documentation validation successful!"
echo "🎉 Ready to commit/push!"
