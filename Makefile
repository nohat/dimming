.PHONY: help docs-check docs-serve docs-build docs-clean install-hooks

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

docs-check: ## Validate documentation in strict mode
	@echo "🔍 Checking MkDocs documentation..."
	@mkdocs build --strict --quiet --site-dir /tmp/mkdocs-check
	@rm -rf /tmp/mkdocs-check
	@echo "✅ Documentation is valid!"

docs-serve: ## Serve documentation locally for development
	@echo "🚀 Starting MkDocs development server..."
	@mkdocs serve

docs-build: ## Build documentation for production
	@echo "🏗️  Building documentation..."
	@mkdocs build --strict --clean

docs-clean: ## Clean built documentation
	@echo "🧹 Cleaning documentation build..."
	@rm -rf site/

install-hooks: ## Install Git hooks for documentation validation
	@echo "⚙️  Installing Git hooks..."
	@git config core.hooksPath .githooks
	@echo "✅ Git hooks installed!"

install-pre-commit: ## Install pre-commit hooks
	@echo "⚙️  Installing pre-commit..."
	@pip install pre-commit
	@pre-commit install
	@echo "✅ Pre-commit hooks installed!"

ci-check: docs-check ## Run all CI checks locally
