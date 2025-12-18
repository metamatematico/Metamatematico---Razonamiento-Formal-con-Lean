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

# ============================================
# Documentation Pipeline (Markdown → HTML/PDF)
# ============================================

# Directory for research documents
research_dir := "research"
diagrams_dir := "research/diagrams"

# Convert all Mermaid diagrams to PNG
diagrams:
    @echo "Converting Mermaid diagrams to PNG..."
    @mkdir -p {{diagrams_dir}}
    @for f in {{diagrams_dir}}/*.mmd; do \
        if [ -f "$f" ]; then \
            mmdc -i "$f" -o "${f%.mmd}.png" -b white; \
        fi \
    done
    @echo "Diagrams converted!"

# Preprocess markdown: replace mermaid blocks with image references
_preprocess file:
    #!/usr/bin/env bash
    awk ' \
      BEGIN { in_mermaid=0; diagram=1 } \
      /^```mermaid/ { in_mermaid=1; print "![Diagram " diagram "](diagrams/diagram" diagram ".png)"; diagram++; next } \
      /^```$/ && in_mermaid { in_mermaid=0; next } \
      !in_mermaid { print } \
    ' {{file}} > /tmp/proposal_clean.md

# Generate HTML from markdown (with MathJax for LaTeX)
html file="research/PROJECT_PROPOSAL.md": (_preprocess file)
    @echo "Generating HTML from {{file}}..."
    pandoc /tmp/proposal_clean.md \
        -o "{{without_extension(file)}}.html" \
        --standalone \
        --mathjax \
        --toc \
        --toc-depth=2 \
        --metadata title="Metamathematics.ai"
    @echo "HTML generated: {{without_extension(file)}}.html"

# Generate PDF from markdown (with XeLaTeX for Unicode support)
pdf file="research/PROJECT_PROPOSAL.md": diagrams (_preprocess file)
    @echo "Generating PDF from {{file}}..."
    cd research && pandoc /tmp/proposal_clean.md \
        -o "PROJECT_PROPOSAL.pdf" \
        --pdf-engine=xelatex \
        --toc \
        --toc-depth=2 \
        -V geometry:margin=1in \
        --metadata title="Metamathematics.ai"
    @echo "PDF generated: {{without_extension(file)}}.pdf"

# Full documentation pipeline: diagrams → HTML + PDF
docs: diagrams
    @echo "Running full documentation pipeline..."
    just html research/PROJECT_PROPOSAL.md
    just pdf research/PROJECT_PROPOSAL.md
    @echo "Documentation ready!"
    @echo "  HTML: research/PROJECT_PROPOSAL.html"
    @echo "  PDF:  research/PROJECT_PROPOSAL.pdf"

# Create a new Mermaid diagram file
new-diagram name:
    @echo "Creating new diagram: {{diagrams_dir}}/{{name}}.mmd"
    @mkdir -p {{diagrams_dir}}
    @echo "graph TD\n    A[Start] --> B[End]" > {{diagrams_dir}}/{{name}}.mmd
    @echo "Edit {{diagrams_dir}}/{{name}}.mmd then run 'just diagrams'"

# Clean generated documentation files
clean-docs:
    rm -f {{research_dir}}/*.html
    rm -f {{diagrams_dir}}/*.png
    @echo "Documentation artifacts cleaned!"

# Watch research docs and regenerate on change (requires fswatch)
watch-docs:
    fswatch -o {{research_dir}}/*.md {{diagrams_dir}}/*.mmd | xargs -n1 -I{} just docs
