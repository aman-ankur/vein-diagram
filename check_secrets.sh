#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking for potential secrets in staged files...${NC}"

# Check for Anthropic API keys in added lines only (not in removed lines)
ANTHROPIC_PATTERN="sk-ant-[a-zA-Z0-9]{4,}"
echo -e "${YELLOW}Checking for Anthropic API keys...${NC}"
ANTHROPIC_MATCHES=$(git diff --cached -U0 | grep -n "^\+" | grep "$ANTHROPIC_PATTERN" 2>/dev/null)
if [ -n "$ANTHROPIC_MATCHES" ]; then
    echo -e "${RED}Found potential Anthropic API keys:${NC}"
    echo "$ANTHROPIC_MATCHES"
fi

# Check for other common API keys and secrets in added lines only
GENERIC_API_PATTERN="(api[_-]?key|apikey|secret|password|credential)[\"']?\s*[:=]\s*[\"'][a-zA-Z0-9_\-]{16,}[\"']"
echo -e "${YELLOW}Checking for generic API keys and secrets...${NC}"
GENERIC_MATCHES=$(git diff --cached -U0 | grep -n "^\+" | grep -E "$GENERIC_API_PATTERN" 2>/dev/null)
if [ -n "$GENERIC_MATCHES" ]; then
    echo -e "${RED}Found potential generic API keys or secrets:${NC}"
    echo "$GENERIC_MATCHES"
fi

# Check if any matches were found
if [ -n "$ANTHROPIC_MATCHES" ] || [ -n "$GENERIC_MATCHES" ]; then
    echo -e "${RED}Potential secrets found in staged changes.${NC}"
    echo -e "${YELLOW}Please remove these secrets before committing.${NC}"
    echo -e "Consider using environment variables instead of hardcoded secrets."
    exit 1
else
    echo -e "${GREEN}No potential secrets found in staged files.${NC}"
    exit 0
fi 