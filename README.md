# 🐄 IDB Livestock Project Filter

A Python application that processes PDF files containing project data and identifies projects related to livestock and agriculture using keyword matching.

## Features

- **PDF Processing**: Extract text from PDF files containing project information
- **Keyword Matching**: Identify livestock-related projects using a comprehensive keyword list
- **Text Normalization**: Case-insensitive matching with Unicode normalization and whitespace handling
- **Streamlit Interface**: User-friendly web interface for uploading and processing files
- **Export Options**: Download results in CSV or Excel format
- **Filtering**: View all projects or filter by keyword matches

## Keywords Searched

The application searches for the following livestock and agriculture-related terms:

- **Animals**: animal, beef, goat, lamb, livestock, pork, poultry
- **Dairy Products**: butter, cheese, cream, dairy, milk, yogurt
- **Feed & Nutrition**: feed, fodder, forage, grains, supplements, protein
- **Animal Products**: egg, eggs, meat, mutton
- **Farm Management**: efficiency, genetics, grazing, health, herd, flock, pasture, vet
- **Environmental**: deforestation, disease, drought, manure, waste, resilience
- **Trade**: export, import, market
- **Health**: zoonotic

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/francescafadel/IDB.git
   cd IDB
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

## Usage

### Running the Application

Start the Streamlit application:

```bash
python3 -m streamlit run filter_livestock_projects.py
```

The application will open in your web browser at `http://localhost:8501`.

### Using the Interface

1. **Upload PDF**: Use the file uploader to select a PDF file containing project data
2. **Review Results**: View the extracted projects with keyword matches highlighted
3. **Filter Projects**: Use the dropdown to filter results by:
   - All projects
   - Projects with keyword matches in name
   - Projects with keyword matches in description
   - Projects with any keyword matches
4. **Download Results**: Export filtered results as CSV or Excel files

### Expected PDF Format

The PDF should contain project information with the following structure:
- **Project Name**: The name/title of the project
- **Project Description**: Detailed description of the project

The application will extract this information and add two new columns:
- **Keywords Found in Project Name**: List of livestock keywords found in the project name
- **Keywords Found in Project Description**: List of livestock keywords found in the project description

## File Structure

```
IDB/
├── filter_livestock_projects.py    # Main Streamlit application
├── keywords.txt                     # List of livestock-related keywords
├── requirements.txt                 # Python dependencies
├── .gitignore                      # Git ignore patterns
├── README.md                       # This file
└── .env.example                    # Environment variables template
```

## Features in Detail

### Text Processing
- **Case-insensitive matching**: Keywords are matched regardless of case
- **Unicode normalization**: Handles special characters and accents
- **Whitespace handling**: Removes extra spaces and non-breaking spaces
- **Duplicate removal**: Eliminates duplicate keyword matches

### Output Columns
- **Keywords Found in Project Name**: Comma-separated list of matched keywords from the project name
- **Keywords Found in Project Description**: Comma-separated list of matched keywords from the project description
- Both columns show "None" if no keywords are found

### Export Options
- **CSV Format**: Simple comma-separated values for basic analysis
- **Excel Format**: Multi-sheet workbook with both filtered and complete results

## Customization

### Adding Keywords
Edit the `keywords.txt` file to add or remove keywords. Each keyword should be on a separate line.

### Modifying PDF Parsing
The PDF parsing logic in the `parse_pdf_to_dataframe()` function can be customized based on your specific PDF format.

## Dependencies

- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **PyPDF2**: PDF file processing
- **openpyxl**: Excel file handling
- **unicodedata2**: Unicode text normalization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions, please create an issue on the [GitHub repository](https://github.com/francescafadel/IDB/issues).

---

**Inter-American Development Bank (IDB) Project Classification Tool**  
Developed to help identify and categorize livestock and agriculture-related development projects.
