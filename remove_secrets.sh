#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}This script will rewrite Git history to remove API keys.${NC}"
echo -e "${RED}WARNING: This is a destructive operation that will change commit hashes.${NC}"
echo -e "${RED}If you've already pushed this branch, you'll need to force push after this.${NC}"
echo -e "${YELLOW}Make sure you have a backup of your repository before proceeding.${NC}"
echo -e "Press Enter to continue or Ctrl+C to abort..."
read

# Define the pattern to match Anthropic API keys
ANTHROPIC_PATTERN="sk-ant-[a-zA-Z0-9]{4,}"

# Files to check
FILES_TO_CHECK=(
    "backend/.env.example"
    "backend/app/main.py"
    "backend/app/services/biomarker_parser.py"
    "backend/test_pdf_extraction.py"
)

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo -e "${YELLOW}Created temporary directory: ${TEMP_DIR}${NC}"

# Function to clean a file
clean_file() {
    local file=$1
    local temp_file="${TEMP_DIR}/$(basename ${file})"
    
    if [ -f "$file" ]; then
        echo -e "${YELLOW}Cleaning ${file}...${NC}"
        # Replace API keys with placeholder
        cat "$file" | sed -E "s/${ANTHROPIC_PATTERN}/your_anthropic_api_key_here/g" > "$temp_file"
        cp "$temp_file" "$file"
    fi
}

# Use git filter-branch to rewrite history
echo -e "${YELLOW}Rewriting Git history...${NC}"
git filter-branch --force --tree-filter '
    for file in '"${FILES_TO_CHECK[*]}"'; do
        if [ -f "$file" ]; then
            sed -i -E "s/sk-ant-[a-zA-Z0-9]{4,}/your_anthropic_api_key_here/g" "$file"
        fi
    done
' --tag-name-filter cat -- --all

# Clean up
echo -e "${YELLOW}Cleaning up...${NC}"
rm -rf "$TEMP_DIR"

echo -e "${GREEN}Done!${NC}"
echo -e "${YELLOW}If you've already pushed this branch, you'll need to force push:${NC}"
echo -e "${YELLOW}git push --force origin feature/marker_extraction_storage${NC}" 