#!/usr/bin/env python3
"""
PDF Project Filter for Livestock Keywords
Processes PDF files containing project data and identifies livestock-related projects.
"""

import pandas as pd
import streamlit as st
import PyPDF2
import re
import unicodedata
from typing import List, Set, Tuple
import io
import os
from pathlib import Path

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
            st.error(f"Keywords file '{keywords_file}' not found!")
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
            st.error("Column 'Project Name' not found in the data!")
            return result_df
        
        if 'Project Description' not in df.columns:
            st.error("Column 'Project Description' not found in the data!")
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


def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""


def parse_pdf_to_dataframe(pdf_text: str) -> pd.DataFrame:
    """
    Parse PDF text to extract project data.
    This is a basic implementation - you may need to customize based on your PDF format.
    """
    # This is a simplified parser - you'll need to adapt this based on your actual PDF structure
    lines = pdf_text.split('\n')
    
    projects = []
    current_project = {}
    
    # Simple heuristic parsing - adapt based on your PDF format
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for project name patterns (customize as needed)
        if line.startswith('Project:') or line.startswith('Project Name:'):
            if current_project:
                projects.append(current_project)
            current_project = {'Project Name': line.split(':', 1)[1].strip()}
        
        elif line.startswith('Description:') or line.startswith('Project Description:'):
            if current_project:
                current_project['Project Description'] = line.split(':', 1)[1].strip()
        
        elif 'Project Name' in current_project and 'Project Description' not in current_project:
            # Accumulate description if it spans multiple lines
            current_project['Project Description'] = current_project.get('Project Description', '') + ' ' + line
    
    # Add the last project
    if current_project:
        projects.append(current_project)
    
    if not projects:
        # If no structured data found, create a sample format for demonstration
        st.warning("No structured project data found in PDF. Creating sample format for demonstration.")
        projects = [
            {
                'Project Name': 'Sample Project - Dairy Farm Development',
                'Project Description': 'Development of sustainable dairy farming practices including cattle health management and milk production efficiency.'
            }
        ]
    
    return pd.DataFrame(projects)


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="IDB Livestock Project Filter",
        page_icon="🐄",
        layout="wide"
    )
    
    st.title("🐄 IDB Livestock Project Filter")
    st.markdown("""
    This application processes PDF files containing project data and identifies projects related to livestock and agriculture.
    Upload a PDF file with columns 'Project Name' and 'Project Description' to get started.
    """)
    
    # Initialize the filter
    filter_instance = LivestockProjectFilter()
    
    if not filter_instance.keywords:
        st.error("No keywords loaded. Please ensure keywords.txt file exists.")
        return
    
    st.sidebar.header("Configuration")
    st.sidebar.write(f"**Keywords loaded:** {len(filter_instance.keywords)}")
    
    with st.sidebar.expander("View Keywords"):
        st.write(", ".join(filter_instance.keywords))
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload PDF file with project data",
        type=['pdf'],
        help="Upload a PDF file containing project information with 'Project Name' and 'Project Description' columns"
    )
    
    if uploaded_file is not None:
        with st.spinner("Processing PDF..."):
            # Extract text from PDF
            pdf_text = extract_text_from_pdf(uploaded_file)
            
            if pdf_text:
                # Parse PDF to DataFrame
                df = parse_pdf_to_dataframe(pdf_text)
                
                if not df.empty:
                    st.success(f"Extracted {len(df)} projects from PDF")
                    
                    # Process the DataFrame
                    processed_df = filter_instance.process_dataframe(df)
                    
                    # Display results
                    st.header("📊 Processing Results")
                    
                    # Show summary statistics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        total_projects = len(processed_df)
                        st.metric("Total Projects", total_projects)
                    
                    with col2:
                        name_matches = len(processed_df[processed_df['Keywords Found in Project Name'] != 'None'])
                        st.metric("Projects with Name Matches", name_matches)
                    
                    with col3:
                        desc_matches = len(processed_df[processed_df['Keywords Found in Project Description'] != 'None'])
                        st.metric("Projects with Description Matches", desc_matches)
                    
                    # Display the processed data
                    st.subheader("🔍 Processed Project Data")
                    st.dataframe(processed_df, use_container_width=True)
                    
                    # Filter options
                    st.subheader("🎯 Filter Results")
                    
                    filter_option = st.selectbox(
                        "Show projects with:",
                        ["All projects", "Keyword matches in name", "Keyword matches in description", "Any keyword matches"]
                    )
                    
                    filtered_df = processed_df.copy()
                    
                    if filter_option == "Keyword matches in name":
                        filtered_df = processed_df[processed_df['Keywords Found in Project Name'] != 'None']
                    elif filter_option == "Keyword matches in description":
                        filtered_df = processed_df[processed_df['Keywords Found in Project Description'] != 'None']
                    elif filter_option == "Any keyword matches":
                        filtered_df = processed_df[
                            (processed_df['Keywords Found in Project Name'] != 'None') |
                            (processed_df['Keywords Found in Project Description'] != 'None')
                        ]
                    
                    st.dataframe(filtered_df, use_container_width=True)
                    
                    # Download options
                    st.subheader("💾 Download Results")
                    
                    # Convert to CSV for download
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="Download filtered results as CSV",
                        data=csv,
                        file_name="livestock_projects_filtered.csv",
                        mime="text/csv"
                    )
                    
                    # Convert to Excel for download
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        filtered_df.to_excel(writer, sheet_name='Filtered Projects', index=False)
                        processed_df.to_excel(writer, sheet_name='All Projects', index=False)
                    
                    st.download_button(
                        label="Download results as Excel",
                        data=excel_buffer.getvalue(),
                        file_name="livestock_projects_analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                else:
                    st.error("No project data could be extracted from the PDF.")
            else:
                st.error("Could not extract text from the PDF file.")
    
    # Instructions
    st.header("📖 Instructions")
    st.markdown("""
    1. **Upload a PDF file** containing project data with 'Project Name' and 'Project Description' columns
    2. **Review the results** showing which keywords were found in each project
    3. **Filter the results** to focus on livestock-related projects
    4. **Download the processed data** in CSV or Excel format
    
    **Keywords being searched:**
    The application searches for livestock-related terms including: animal, beef, butter, cheese, cream, dairy, 
    deforestation, disease, drought, egg, eggs, efficiency, export, feed, flock, fodder, forage, genetics, goat, 
    grains, grazing, health, herd, import, lamb, livestock, manure, market, meat, milk, mutton, pasture, pork, 
    poultry, protein, resilience, supplements, vet, waste, yogurt, zoonotic.
    
    **Text Processing:**
    - Case-insensitive matching
    - Unicode normalization for special characters
    - Removal of extra whitespace and non-breaking spaces
    - Duplicate keyword removal
    """)


if __name__ == "__main__":
    main()
