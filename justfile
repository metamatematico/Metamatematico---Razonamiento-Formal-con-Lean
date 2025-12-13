# AI Mathematician - Lean 4 Project Commands
# Run `just --list` to see all available commands

# Default recipe: build the project
default: build

# Build the project
build:
    lake build

# Update dependencies (fetches Mathlib cache)
update:
    lake update

# Clean build artifacts and rebuild from scratch
clean:
    rm -rf .lake lake-manifest.json
    lake update
    lake build

# Run the executable
run:
    lake exe ai_mathematician

# Check a specific file without full build
check file:
    lake env lean {{file}}

# Build with verbose output
build-verbose:
    lake build --verbose

# Download/update Mathlib cache only
cache:
    lake exe cache get

# Show project info
info:
    @echo "Project: ai_mathematician"
    @echo "Toolchain: $(cat lean-toolchain)"
    @lake --version

# Watch for changes and rebuild (requires fswatch)
watch:
    fswatch -o **/*.lean | xargs -n1 -I{} lake build

# Format check (if lean4-format is installed)
fmt:
    find . -name "*.lean" -not -path "./.lake/*" | xargs -I{} lean4-format {}

# List all Lean files in the project
files:
    @find . -name "*.lean" -not -path "./.lake/*"

# Quick rebuild (incremental)
rebuild:
    lake build

# Full clean rebuild with fresh Mathlib
fresh: clean
    @echo "Fresh build complete!"
