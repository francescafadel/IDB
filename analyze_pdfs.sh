#!/bin/bash

# IDB Livestock Project Filter - Quick Analysis Script
# Double-click this file to analyze all PDF files in the folder

echo "🐄 IDB Livestock Project Filter"
echo "================================"

# Change to the script directory
cd "$(dirname "$0")"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    read -p "Press any key to exit..."
    exit 1
fi

# Run the analysis
python3 run_analysis.py

echo ""
echo "Press any key to exit..."
read -n 1
