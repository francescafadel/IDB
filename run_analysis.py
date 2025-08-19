#!/usr/bin/env python3
"""
Quick PDF Analysis Script
Simple script to process all PDF files in the current directory.
"""

import subprocess
import sys
import os

def main():
    """Run the PDF analysis on all PDF files in current directory."""
    print("🐄 IDB Livestock Project Filter")
    print("Processing all PDF files in current directory...")
    print("-" * 50)
    
    # Check if there are any PDF files
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found in current directory.")
        print("📝 To use this tool:")
        print("   1. Drag and drop your PDF files into this folder")
        print("   2. Run this script again: python3 run_analysis.py")
        return
    
    print(f"📋 Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"   - {pdf}")
    
    print("\n🔄 Starting analysis...")
    
    # Run the main processing script
    try:
        result = subprocess.run([
            sys.executable, 'process_local_pdfs.py'
        ], capture_output=True, text=True)
        
        # Print the output
        print(result.stdout)
        
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ Analysis completed successfully!")
            print("📁 Check the 'output' folder for your results.")
        else:
            print(f"\n❌ Analysis failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running analysis: {str(e)}")

if __name__ == "__main__":
    main()
