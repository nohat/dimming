#!/bin/bash

# Markdown Linting Script
# This script provides comprehensive markdown linting for the documentation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if markdownlint-cli2 is installed
check_dependencies() {
    print_status "Checking markdown linting dependencies..."
    
    if ! command -v markdownlint-cli2 &> /dev/null; then
        print_error "markdownlint-cli2 is not installed."
        print_status "Installing markdownlint-cli2..."
        
        if command -v npm &> /dev/null; then
            npm install -g markdownlint-cli2
        elif command -v pip &> /dev/null; then
            pip install markdownlint-cli2
        else
            print_error "Neither npm nor pip is available. Please install markdownlint-cli2 manually."
            exit 1
        fi
    fi
    
    print_success "Dependencies are available."
}

# Run markdown linting
run_markdownlint() {
    print_status "Running markdown linting on documentation..."
    
    cd "$PROJECT_ROOT"
    
    # Check if config file exists
    if [ ! -f ".markdownlint.json" ]; then
        print_error "Markdown lint configuration file (.markdownlint.json) not found!"
        exit 1
    fi
    
    # Run markdownlint with strict settings
    if markdownlint-cli2 "docs/**/*.md" "*.md"; then
        print_success "All markdown files passed linting!"
        return 0
    else
        print_error "Markdown linting failed!"
        return 1
    fi
}

# Fix common markdown issues automatically
auto_fix() {
    print_status "Attempting to auto-fix markdown issues..."
    
    cd "$PROJECT_ROOT"
    
    if markdownlint-cli2 --fix "docs/**/*.md" "*.md"; then
        print_success "Auto-fix completed!"
        print_warning "Please review the changes before committing."
    else
        print_error "Auto-fix encountered issues. Manual intervention may be required."
        return 1
    fi
}

# Show help
show_help() {
    echo "Markdown Linting Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  check     Run markdown linting (default)"
    echo "  fix       Auto-fix common markdown issues"
    echo "  install   Install/update markdown linting dependencies"
    echo "  help      Show this help message"
    echo ""
    echo "Configuration:"
    echo "  - Lint rules: .markdownlint.json"
    echo "  - Ignore patterns: .markdownlintignore"
    echo ""
}

# Main execution
main() {
    local command="${1:-check}"
    
    case "$command" in
        "check")
            check_dependencies
            run_markdownlint
            ;;
        "fix")
            check_dependencies
            auto_fix
            ;;
        "install")
            check_dependencies
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run the main function with all arguments
main "$@"
