# Arabic PDF Proofreading Chunker

A Python utility that intelligently processes large Arabic PDFs (mixed text and scanned pages), applies OCR where needed, and splits content into manageable chunks formatted for ChatGPT-assisted proofreading review.

## Features

- **Smart Page Detection**: Automatically detects text-based vs scanned pages
- **Arabic OCR**: Uses Tesseract OCR for scanned pages with Arabic language support
- **Intelligent Chunking**: Splits documents into manageable chunks based on word count and page limits
- **ChatGPT-Ready Output**: Generates markdown files with proofreading instructions
- **Progress Tracking**: Real-time progress reporting and detailed logging

## Prerequisites

### 1. Python 3.8 or higher

### 2. Tesseract-OCR

Tesseract must be installed on your system separately.

#### Windows
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and note the installation path (typically `C:\Program Files\Tesseract-OCR`)
3. Add Tesseract to your PATH, or set it in the script:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

#### macOS
```bash
brew install tesseract
brew install tesseract-lang  # For Arabic support
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-ara  # Arabic language data
sudo apt-get install tesseract-ocr-eng  # English language data
```

#### Verify Installation
```bash
tesseract --version
tesseract --list-langs  # Should show 'ara' and 'eng'
```

### 3. Poppler (for pdf2image)

#### Windows
1. Download from: http://blog.alivate.com.au/poppler-windows/
2. Extract to a folder (e.g., `C:\Program Files\poppler`)
3. Add the `bin` folder to your PATH

#### macOS
```bash
brew install poppler
```

#### Linux
```bash
sudo apt-get install poppler-utils
```

## Installation

1. Clone or download this repository

2. Create and activate a virtual environment (recommended):

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

To deactivate the virtual environment when done:
```bash
deactivate
```

## Usage

### Basic Usage

Place your PDF in the `input/` directory (or provide any path):

```bash
python prepare_proofread_chunks.py input/document.pdf
```

### Advanced Usage

```bash
# Custom word limit per chunk
python prepare_proofread_chunks.py input/document.pdf --max-words 5000

# Custom page limit per chunk
python prepare_proofread_chunks.py input/document.pdf --max-pages 15

# Different OCR language (Arabic only)
python prepare_proofread_chunks.py input/document.pdf --ocr-lang ara

# Combine options
python prepare_proofread_chunks.py input/document.pdf --max-words 4000 --max-pages 12 --ocr-lang ara+eng
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `pdf_path` | Path to input PDF file (required) | - |
| `--max-words` | Maximum words per chunk | 25000 |
| `--max-pages` | Maximum pages per chunk | 80 |
| `--ocr-lang` | Tesseract language code(s) | ara+eng |

## Output Structure

After processing, the following structure will be created:

```
project/
├── input/              # Place your PDF files here
├── output/
│   └── chunks/        # Generated markdown chunks
│       ├── chunk_001_p001-p080.md
│       ├── chunk_002_p081-p160.md
│       └── ...
├── logs/
│   └── page_sources.txt  # Log of TEXT vs OCR for each page
```

### Chunk File Format

Each chunk file contains:

1. **CHUNK_META**: Chunk ID and page range
2. **INSTRUCTIONS_FOR_CHATGPT**: Proofreading guidelines
3. **TEXT**: The actual content with page markers

Example:
```markdown
### CHUNK_META
CHUNK_ID: 001
PAGES: 1-80

### INSTRUCTIONS_FOR_CHATGPT
Review the following Arabic text for proofreading purposes:
- Identify any major spelling, grammar, punctuation, hamza, or spacing errors.
- Note any inconsistencies in formatting or structure.
- Do NOT correct the text directly - I want to make the corrections myself.
- Focus on issues that affect readability or meaning.

Please provide:
1. A summary of the overall quality (good/needs attention/needs significant work).
2. A list of the most common or significant issues you found (with page numbers if possible).
3. Any specific sections that need particular attention.
4. Suggested areas to focus on when proofreading.

### TEXT
---- [Page 1] ----
(page content here)

---- [Page 2] ----
(page content here)
...
```

## Workflow

1. **Run the script** on your PDF
2. **Review the logs** to see which pages used OCR
3. **Open chunk files** from `output/chunks/`
4. **Copy-paste** each chunk into ChatGPT to get issue identification and quality assessment
5. **Review ChatGPT's feedback** on problem areas
6. **Proofread the original PDF yourself**, focusing on the areas ChatGPT highlighted

## Troubleshooting

### "Tesseract not found"
- Ensure Tesseract is installed and in your PATH
- On Windows, you may need to set `pytesseract.pytesseract.tesseract_cmd` explicitly

### "Language 'ara' not found"
- Install Tesseract Arabic language data
- Verify with: `tesseract --list-langs`

### OCR produces poor results
- Check your PDF scan quality (DPI should be 300+ for best results)
- Try adjusting the OCR language parameter
- Consider preprocessing images if they're very low quality

### Script is very slow
- Large PDFs with many scanned pages will take time
- OCR is CPU-intensive; be patient
- Consider processing smaller sections if needed

### Memory issues
- Large PDFs may require significant RAM
- Process on a machine with adequate resources
- Consider splitting the PDF manually first if needed

## Performance Notes

- **Text pages**: Process very quickly (milliseconds per page)
- **Scanned pages**: OCR is slower (several seconds per page)
- **Large PDFs**: A 500-page mixed PDF might take 30-60 minutes depending on the ratio of scanned pages

## Tips

1. **Test first**: Run on a small PDF to verify everything works
2. **Use GPT-4**: The default settings (25,000 words per chunk) are optimized for GPT-4's context window. For GPT-3.5, use `--max-words 8000` instead
3. **Check logs**: Review `logs/page_sources.txt` to see OCR usage
4. **Adjust limits**: Tune `--max-words` and `--max-pages` based on your needs and AI model
5. **Arabic support**: Ensure your text editor/viewer supports RTL text
6. **Backup**: Keep original PDFs safe before processing

## License

This tool is provided as-is for personal and educational use.

## Requirements

See `requirements.txt` for Python package versions.

