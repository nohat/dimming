# Markdown Linting Setup

This repository is configured with comprehensive markdown linting to ensure consistent, high-quality
documentation. The setup includes automatic fixing, pre-commit hooks, and development server integration.

## 🚀 Quick Start

### Automatic Mode (Recommended)

The development server automatically lints and fixes markdown files:

```bash
# Start dev server with auto-linting
make docs-serve
# OR use VS Code task: "Dev Server with Auto-lint"
```text

### Manual Commands

```bash
# Check markdown files for issues
make lint-markdown

# Auto-fix markdown issues
make fix-markdown

# Run all CI checks locally
make ci-check
```text

## 🔧 Configuration

### Linting Rules

- **Configuration file**: `.markdownlint.json`
- **Ignore patterns**: `.markdownlintignore`
- **Strict settings**: Line length 120 chars, consistent formatting, heading structure

### Key Rules Enforced

- ✅ Consistent heading styles (ATX: `# Heading`)
- ✅ Proper list formatting with 4-space indentation
- ✅ Line length limits (120 characters)
- ✅ Consistent emphasis styles (underscore for `_emphasis_`)
- ✅ Proper spacing around headings and lists
- ✅ No trailing punctuation in headings
- ✅ Fenced code blocks with backticks

## 🔄 Development Workflow

### VS Code Integration

The setup includes VS Code integration for seamless development:

- **Auto-fix on save**: Markdown files are automatically fixed when saved
- **Real-time linting**: Issues are highlighted as you type
- **Tasks available**:
    - `Lint Markdown` - Check for issues
    - `Fix Markdown` - Auto-fix issues
    - `Dev Server with Auto-lint` - Start development with auto-fixing

### Pre-commit Hooks

Git hooks ensure all commits contain properly formatted markdown:

1. **Auto-fix attempt**: Tries to fix issues automatically
2. **Strict validation**: Ensures no linting errors remain
3. **Build validation**: Verifies MkDocs can build the documentation

```bash
# Install pre-commit hooks (already done in setup)
pre-commit install

# Test pre-commit hooks
pre-commit run --all-files
```bash

## 🛠️ Tools and Dependencies

### Primary Tools

- **markdownlint-cli2**: Fast, configurable markdown linter
- **pre-commit**: Git hook framework for quality checks
- **VS Code extension**: `DavidAnson.vscode-markdownlint`

### Installation

All dependencies are managed automatically:

```bash
# Python dependencies (includes pre-commit)
pip install -r requirements.txt

# Node.js tool (installed globally)
npm install -g markdownlint-cli2

# VS Code extensions (auto-installed)
# - markdownlint
# - markdown-all-in-one
```text

## 📋 Manual Operations

### Check Specific Files

```bash
# Check single file
markdownlint-cli2 docs/index.md

# Check specific directory
markdownlint-cli2 docs/architecture/**/*.md

# Check with verbose output
markdownlint-cli2 --verbose **/*.md
```text

### Fix Specific Issues

```bash
# Auto-fix all files
markdownlint-cli2 --fix **/*.md

# Fix specific file
markdownlint-cli2 --fix docs/index.md

# Fix and then check
markdownlint-cli2 --fix **/*.md && markdownlint-cli2 **/*.md
```text

### Custom Configuration

To modify linting rules, edit `.markdownlint.json`:

```json
{
  "MD013": {
    "line_length": 100,  // Change line length limit
    "code_blocks": false // Don't check code blocks
  },
  "MD033": {
    "allowed_elements": ["br", "img"] // Allow specific HTML
  }
}
```text

## 🚨 Troubleshooting

### Common Issues

**Issue**: VS Code not showing markdown errors
**Solution**:

1. Ensure `DavidAnson.vscode-markdownlint` extension is installed
2. Check `.vscode/settings.json` has correct configuration
3. Reload VS Code window

**Issue**: Pre-commit hooks not running
**Solution**:

```bash
# Reinstall hooks
pre-commit clean
pre-commit install
```text

**Issue**: Line length errors on long URLs
**Solution**: URLs in code blocks are automatically ignored, or add to `.markdownlintignore`

**Issue**: Build fails due to markdown errors
**Solution**:

```bash
# Auto-fix and rebuild
make fix-markdown
make docs-build
```text

### Override Specific Rules

For specific files that need rule exceptions, add to `.markdownlintignore`:

```bash
# Ignore generated files
docs/api/generated/**
site/**

# Ignore specific problematic files
docs/legacy-content.md
```text

## 📊 Continuous Integration

### GitHub Actions

- **Workflow**: `.github/workflows/markdown-lint.yml`
- **Triggers**: Push/PR to main/develop branches with markdown changes
- **Actions**:
  1. Lint all markdown files
  2. Show auto-fixable issues if linting fails
  3. Provide fix suggestions in PR comments

### Local CI Simulation

```bash
# Run same checks as CI
make ci-check

# Run pre-commit on all files
pre-commit run --all-files
```text

## 🎯 Best Practices

### Writing Markdown

1. **Use consistent heading hierarchy**: Don't skip levels (h1 → h2 → h3)
2. **Keep lines under 120 characters**: Break long lines naturally
3. **Use fenced code blocks**: Always specify language for syntax highlighting
4. **Consistent list formatting**: Use 4-space indentation for nested items
5. **No trailing punctuation in headings**: Avoid `:` `.` `!` in headings

### Development Workflow

1. **Start with auto-lint server**: Use `Dev Server with Auto-lint` task
2. **Save frequently**: Auto-fix on save catches issues early
3. **Check before commit**: `make lint-markdown` before major commits
4. **Review auto-fixes**: Always verify automatic changes are correct

### Performance Tips

- **Use ignore patterns**: Add non-documentation files to `.markdownlintignore`
- **Lint incrementally**: Use file-specific commands for large repositories
- **Batch fixes**: Run `make fix-markdown` after major content changes

---

This setup ensures consistent, high-quality markdown documentation while providing a smooth development
experience with automatic fixing and comprehensive validation.
