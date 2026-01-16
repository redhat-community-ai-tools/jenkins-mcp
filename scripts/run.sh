#!/bin/bash

# Dashboard Build Analyzer Runner
# Simple script to run the analyzer with proper configuration

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if .env file exists in project root, if so load it
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment from .env file..."
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

# Check required environment variables
if [ -z "$JENKINS_TOKEN" ]; then
    echo "Error: JENKINS_TOKEN environment variable is required"
    echo "Please set it in .env file or export it:"
    echo "  export JENKINS_TOKEN='your-token-here'"
    exit 1
fi

# Default to run-now mode if no argument provided
MODE=${1:-run-now}

echo "Starting Dashboard Build Analyzer..."
echo "Mode: $MODE"
echo ""

# Run the analyzer from project root
cd "$PROJECT_ROOT"
python3 scripts/nightly_analyzer.py --mode "$MODE"
