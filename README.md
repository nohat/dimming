# Universal Smart Lighting Control - Dimming

Documentation related to plans to improve handling of dimming in Home Assistant and other smart home platforms.

## 📖 Documentation

The complete documentation is available at: **[GitHub Pages Site](https://your-username.github.io/dimming/)**

## 🚀 Local Development

To work with the documentation locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Quick validation check
make docs-check

# Serve the site locally with live reload
make docs-serve
# OR: mkdocs serve
```

The site will be available at `http://localhost:8000`

### �️ Documentation Validation

This project includes multiple layers of protection to prevent broken documentation:

```bash
# Install Git hooks (prevents committing broken docs)
make install-hooks

# Run comprehensive validation
./scripts/validate-docs.sh

# Install advanced pre-commit framework (optional)
make install-pre-commit
```

**Available validation tools:**
- **Git hooks** - Automatic validation before commits
- **Make targets** - Quick validation commands (`make docs-check`)
- **GitHub Actions** - CI validation on PRs and deployment
- **Pre-commit framework** - Advanced formatting and validation

See [`DOC_VALIDATION.md`](DOC_VALIDATION.md) for detailed setup instructions.

## 🔄 Automatic Deployment

This repository uses GitHub Actions for deployment:

- **PR Validation**: All pull requests are validated for documentation integrity
- **Automatic Deployment**: Clean builds are deployed to GitHub Pages from the main branch
- **Strict Mode**: All builds use `--strict` mode to catch warnings as errors
