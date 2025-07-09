# Universal Smart Lighting Control - Dimming

Documentation related to plans to improve handling of dimming in Home Assistant and other smart home platforms.

## 📖 Documentation

The complete documentation is available at: **[GitHub Pages Site](https://your-username.github.io/dimming/)**

## 🚀 Local Development

To work with the documentation locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Quick validation and markdown linting
make docs-check

# Serve the site locally with live reload and auto-linting
make docs-serve
# OR: markdownlint-cli2 --fix **/*.md && mkdocs serve
```

The site will be available at `http://localhost:8000`

### ⚙️ Documentation Validation & Linting

This project includes comprehensive markdown linting and validation:

```bash
# Install Git hooks (prevents committing broken docs)
make install-hooks

# Lint and auto-fix markdown files
make fix-markdown

# Run comprehensive validation
./scripts/validate-docs.sh

# Install advanced pre-commit framework (optional)
make install-pre-commit
```

**Available tools:**

- **Markdown Linting** - Automatic formatting and consistency checks
- **Auto-fixing** - VS Code integration fixes issues on save
- **Git hooks** - Prevents committing invalid markdown or broken docs
- **Make targets** - Quick commands (`make lint-markdown`, `make fix-markdown`)
- **GitHub Actions** - CI validation and auto-fix suggestions
- **Pre-commit framework** - Advanced formatting and validation

See [`MARKDOWN_LINTING.md`](MARKDOWN_LINTING.md) for detailed markdown linting setup and
[`DOC_VALIDATION.md`](DOC_VALIDATION.md) for comprehensive validation instructions.

## 🔄 Automatic Deployment

This repository uses GitHub Actions for deployment:

- **PR Validation**: All pull requests are validated for documentation integrity
- **Automatic Deployment**: Clean builds are deployed to GitHub Pages from the main branch
- **Strict Mode**: All builds use `--strict` mode to catch warnings as errors
