# Documentation Validation Setup

This directory contains tools and configurations to ensure documentation quality and prevent broken docs from being committed.

## Quick Start

### 1. Basic Validation

```bash
# Quick check before committing
make docs-check

# Serve docs locally for development
make docs-serve
```text

### 2. Install Git Hooks (Recommended)

```bash
# Install simple Git hooks
make install-hooks

# Or install advanced pre-commit hooks
make install-pre-commit
```text

### 3. Run Full Validation

```bash
# Run the complete validation script
./scripts/validate-docs.sh

# Or use make target
make ci-check
```text

## Available Tools

### Makefile Targets

- `make docs-check` - Validate docs in strict mode
- `make docs-serve` - Start development server
- `make docs-build` - Build for production
- `make docs-clean` - Clean build artifacts
- `make install-hooks` - Install Git hooks
- `make install-pre-commit` - Install pre-commit framework

### Scripts

- `scripts/validate-docs.sh` - Comprehensive validation script
- `.githooks/pre-commit` - Simple Git pre-commit hook

### Automated Checks

#### GitHub Actions

1. **validate-docs.yml** - Runs on PRs to validate documentation
2. **deploy-docs.yml** - Builds and deploys to GitHub Pages (main branch only)

#### Pre-commit Hooks

The `.pre-commit-config.yaml` includes:

- MkDocs build validation
- YAML syntax checking
- Markdown formatting
- File consistency checks

## Validation Layers

### 1. Local Development

- **Make targets** for quick validation
- **Development server** with live reload
- **Manual script** for comprehensive checking

### 2. Pre-commit Protection

- **Git hooks** prevent committing broken docs
- **Pre-commit framework** for advanced validation
- **Automatic formatting** for consistency

### 3. CI/CD Pipeline

- **PR validation** ensures changes don't break docs
- **Strict mode builds** catch all warnings
- **Deployment verification** before going live

## Common Issues and Solutions

### Broken Links

- Use relative paths: `[text](../other-section/file.md)`
- Check file exists in `docs/` directory
- Run `make docs-check` to validate

### YAML Configuration

- Validate with `python -c "import yaml; yaml.safe_load(open('mkdocs.yml'))"`
- Check indentation and syntax

### Missing Files

- Ensure all files referenced in navigation exist
- Check for typos in file paths

### Build Failures

1. Run `make docs-check` locally
2. Fix reported errors
3. Test with `make docs-serve`
4. Commit and push

## Development Workflow

1. Make documentation changes
2. Run `make docs-serve` for live preview
3. Validate with `make docs-check`
4. Commit (hooks will validate automatically)
5. Push (CI will validate on PR)

## Troubleshooting

### Git Hooks Not Working

```bash
# Reinstall hooks
make install-hooks

# Check Git configuration
git config core.hooksPath
```text

### Pre-commit Issues

```bash
# Install/reinstall pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```text

### MkDocs Build Errors

```bash
# Verbose output for debugging
mkdocs build --strict --verbose

# Check specific warnings
mkdocs build --clean
```text
