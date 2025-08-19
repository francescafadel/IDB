#!/usr/bin/env python3
"""
Local PDF Processor for Livestock Keywords
Processes PDF files in the current directory and creates output files with keyword analysis.
"""

import pandas as pd
import PyPDF2
import re
import unicodedata
from typing import List, Set, Tuple
import os
import glob
from pathlib import Path
from datetime import datetime
import argparse

class LivestockProjectFilter:
    """Class to filter projects based on livestock-related keywords."""
    
    def __init__(self, keywords_file: str = "keywords.txt"):
        """Initialize with keywords from file."""
        self.keywords = self._load_keywords(keywords_file)
        self.compiled_patterns = self._compile_patterns()
    
    def _load_keywords(self, keywords_file: str) -> List[str]:
        """Load keywords from file."""
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                keywords = [line.strip().lower() for line in f if line.strip()]
            return keywords
        except FileNotFoundError:
            print(f"ERROR: Keywords file '{keywords_file}' not found!")
            return []
    
    def _compile_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for efficient matching."""
        patterns = []
        for keyword in self.keywords:
            # Create word boundary pattern for case-insensitive matching
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            patterns.append(pattern)
        return patterns
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by handling unicode, spaces, and formatting."""
        if pd.isna(text) or text is None:
            return ""
        
        # Convert to string
        text = str(text)
        
        # Unicode normalization (NFKD decomposes characters)
        text = unicodedata.normalize('NFKD', text)
        
        # Replace non-breaking spaces with regular spaces
        text = text.replace('\u00A0', ' ')  # Non-breaking space
        text = text.replace('\u2007', ' ')  # Figure space
        text = text.replace('\u2009', ' ')  # Thin space
        text = text.replace('\u200A', ' ')  # Hair space
        
        # Collapse multiple spaces into single spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading and trailing whitespace
        text = text.strip()
        
        return text
    
    def find_keywords_in_text(self, text: str) -> List[str]:
        """Find all matching keywords in the given text."""
        if not text:
            return []
        
        # Normalize the text
        normalized_text = self._normalize_text(text)
        
        found_keywords = []
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(normalized_text):
                found_keywords.append(self.keywords[i])
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(found_keywords))
    
    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process DataFrame to add keyword columns."""
        # Make a copy to avoid modifying original
        result_df = df.copy()
        
        # Check if required columns exist
        if 'Project Name' not in df.columns:
            print("WARNING: Column 'Project Name' not found in the data!")
            return result_df
        
        if 'Project Description' not in df.columns:
            print("WARNING: Column 'Project Description' not found in the data!")
            return result_df
        
        # Find keywords in Project Name
        result_df['Keywords Found in Project Name'] = result_df['Project Name'].apply(
            lambda x: ', '.join(self.find_keywords_in_text(x)) if self.find_keywords_in_text(x) else 'None'
        )
        
        # Find keywords in Project Description
        result_df['Keywords Found in Project Description'] = result_df['Project Description'].apply(
            lambda x: ', '.join(self.find_keywords_in_text(x)) if self.find_keywords_in_text(x) else 'None'
        )
        
        return result_df


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"ERROR reading PDF {pdf_path}: {str(e)}")
        return ""


def parse_pdf_to_dataframe(pdf_text: str, pdf_filename: str) -> pd.DataFrame:
    """
    Parse PDF text to extract project data.
    Enhanced parser with multiple detection strategies.
    """
    lines = [line.strip() for line in pdf_text.split('\n') if line.strip()]
    
    projects = []
    current_project = {}
    
    # Strategy 1: Look for structured project data
    for i, line in enumerate(lines):
        # Project name patterns
        if any(pattern in line.lower() for pattern in ['project:', 'project name:', 'title:', 'nombre del proyecto:']):
            if current_project:
                projects.append(current_project)
            current_project = {'Project Name': line.split(':', 1)[1].strip() if ':' in line else line.strip()}
        
        # Description patterns  
        elif any(pattern in line.lower() for pattern in ['description:', 'project description:', 'summary:', 'descripción:']):
            if current_project:
                desc = line.split(':', 1)[1].strip() if ':' in line else line.strip()
                # Look ahead for continuation lines
                j = i + 1
                while j < len(lines) and not any(stop_word in lines[j].lower() for stop_word in ['project:', 'title:', 'budget:', 'cost:', 'date:']):
                    if lines[j].strip():
                        desc += ' ' + lines[j].strip()
                    j += 1
                current_project['Project Description'] = desc
    
    # Add the last project
    if current_project:
        projects.append(current_project)
    
    # Strategy 2: If no structured data found, try table-like parsing
    if not projects:
        print(f"No structured project data found in {pdf_filename}. Trying alternative parsing...")
        
        # Look for table headers
        header_line = -1
        for i, line in enumerate(lines):
            if 'project' in line.lower() and ('name' in line.lower() or 'title' in line.lower()):
                header_line = i
                break
        
        if header_line != -1:
            # Try to parse as table data
            for i in range(header_line + 1, len(lines)):
                line = lines[i]
                if line and len(line.split()) >= 2:  # At least project name and some description
                    parts = line.split(None, 1)  # Split into at most 2 parts
                    projects.append({
                        'Project Name': parts[0],
                        'Project Description': parts[1] if len(parts) > 1 else ''
                    })
    
    # Strategy 3: If still no data, create sections based on content
    if not projects:
        print(f"Creating content-based analysis for {pdf_filename}...")
        
        # Split text into chunks and treat each substantial chunk as a potential project
        chunks = []
        current_chunk = []
        
        for line in lines:
            if len(line) > 50:  # Substantial content line
                current_chunk.append(line)
            elif current_chunk:
                if len(' '.join(current_chunk)) > 100:  # Minimum chunk size
                    chunks.append(' '.join(current_chunk))
                current_chunk = []
        
        # Add last chunk
        if current_chunk and len(' '.join(current_chunk)) > 100:
            chunks.append(' '.join(current_chunk))
        
        # Create projects from chunks
        for i, chunk in enumerate(chunks[:10]):  # Limit to first 10 chunks
            # Try to extract a title (first sentence or first line)
            sentences = chunk.split('.')
            title = sentences[0].strip()[:100]  # First 100 chars as title
            
            projects.append({
                'Project Name': f"Section {i+1}: {title}",
                'Project Description': chunk
            })
    
    # Fallback: Create at least one entry with full text
    if not projects:
        projects = [{
            'Project Name': f"Full Document Analysis - {pdf_filename}",
            'Project Description': pdf_text[:2000]  # First 2000 characters
        }]
    
    return pd.DataFrame(projects)


def process_single_pdf(pdf_path: str, filter_instance: LivestockProjectFilter, output_dir: str = "output") -> bool:
    """Process a single PDF file and create output files."""
    pdf_filename = os.path.basename(pdf_path)
    print(f"\n📄 Processing: {pdf_filename}")
    
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(pdf_path)
    
    if not pdf_text.strip():
        print(f"❌ Could not extract text from {pdf_filename}")
        return False
    
    # Parse PDF to DataFrame
    df = parse_pdf_to_dataframe(pdf_text, pdf_filename)
    
    if df.empty:
        print(f"❌ No project data found in {pdf_filename}")
        return False
    
    print(f"✅ Extracted {len(df)} project(s) from {pdf_filename}")
    
    # Process the DataFrame with keyword matching
    processed_df = filter_instance.process_dataframe(df)
    
    # Calculate statistics
    name_matches = len(processed_df[processed_df['Keywords Found in Project Name'] != 'None'])
    desc_matches = len(processed_df[processed_df['Keywords Found in Project Description'] != 'None'])
    total_matches = len(processed_df[
        (processed_df['Keywords Found in Project Name'] != 'None') |
        (processed_df['Keywords Found in Project Description'] != 'None')
    ])
    
    print(f"🔍 Keyword Analysis Results:")
    print(f"   - Projects with name matches: {name_matches}")
    print(f"   - Projects with description matches: {desc_matches}")
    print(f"   - Total projects with any matches: {total_matches}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filenames
    base_name = os.path.splitext(pdf_filename)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    csv_filename = f"{base_name}_livestock_analysis_{timestamp}.csv"
    excel_filename = f"{base_name}_livestock_analysis_{timestamp}.xlsx"
    
    csv_path = os.path.join(output_dir, csv_filename)
    excel_path = os.path.join(output_dir, excel_filename)
    
    # Save as CSV
    processed_df.to_csv(csv_path, index=False)
    print(f"💾 Saved CSV: {csv_path}")
    
    # Save as Excel with multiple sheets
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # All projects
        processed_df.to_excel(writer, sheet_name='All Projects', index=False)
        
        # Only projects with matches
        matched_df = processed_df[
            (processed_df['Keywords Found in Project Name'] != 'None') |
            (processed_df['Keywords Found in Project Description'] != 'None')
        ]
        
        if not matched_df.empty:
            matched_df.to_excel(writer, sheet_name='Livestock Projects', index=False)
        
        # Summary statistics
        summary_data = {
            'Metric': [
                'Total Projects',
                'Projects with Name Matches',
                'Projects with Description Matches', 
                'Projects with Any Matches',
                'Processing Date',
                'Source File'
            ],
            'Value': [
                len(processed_df),
                name_matches,
                desc_matches,
                total_matches,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                pdf_filename
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"💾 Saved Excel: {excel_path}")
    return True


def main():
    """Main function to process PDF files in the current directory."""
    parser = argparse.ArgumentParser(description='Process PDF files for livestock keyword analysis')
    parser.add_argument('--input-dir', '-i', default='.', help='Input directory containing PDF files (default: current directory)')
    parser.add_argument('--output-dir', '-o', default='output', help='Output directory for results (default: output)')
    parser.add_argument('--keywords-file', '-k', default='keywords.txt', help='Keywords file (default: keywords.txt)')
    parser.add_argument('--file', '-f', help='Process specific PDF file instead of all PDFs in directory')
    
    args = parser.parse_args()
    
    print("🐄 IDB Livestock Project Filter - Local Processing")
    print("=" * 50)
    
    # Initialize the filter
    filter_instance = LivestockProjectFilter(args.keywords_file)
    
    if not filter_instance.keywords:
        print("❌ No keywords loaded. Exiting.")
        return
    
    print(f"✅ Loaded {len(filter_instance.keywords)} keywords")
    print(f"📁 Input directory: {os.path.abspath(args.input_dir)}")
    print(f"📁 Output directory: {os.path.abspath(args.output_dir)}")
    
    # Find PDF files to process
    if args.file:
        # Process specific file
        pdf_files = [args.file] if os.path.exists(args.file) else []
        if not pdf_files:
            print(f"❌ File not found: {args.file}")
            return
    else:
        # Find all PDF files in input directory
        search_pattern = os.path.join(args.input_dir, "*.pdf")
        pdf_files = glob.glob(search_pattern)
    
    if not pdf_files:
        print(f"❌ No PDF files found in {args.input_dir}")
        print("📝 Instructions:")
        print("   1. Place your PDF files in this directory")
        print("   2. Run this script again")
        print("   3. Or specify a different directory with --input-dir")
        return
    
    print(f"\n📋 Found {len(pdf_files)} PDF file(s) to process:")
    for pdf_file in pdf_files:
        print(f"   - {os.path.basename(pdf_file)}")
    
    # Process each PDF file
    processed_count = 0
    for pdf_file in pdf_files:
        try:
            if process_single_pdf(pdf_file, filter_instance, args.output_dir):
                processed_count += 1
        except Exception as e:
            print(f"❌ Error processing {pdf_file}: {str(e)}")
    
    print(f"\n🎉 Processing complete!")
    print(f"✅ Successfully processed: {processed_count}/{len(pdf_files)} files")
    print(f"📁 Results saved in: {os.path.abspath(args.output_dir)}")
    
    if processed_count > 0:
        print(f"\n📊 Next steps:")
        print(f"   - Check the '{args.output_dir}' folder for CSV and Excel files")
        print(f"   - Each file contains keyword analysis results")
        print(f"   - Excel files have multiple sheets: All Projects, Livestock Projects, Summary")


if __name__ == "__main__":
    main()
