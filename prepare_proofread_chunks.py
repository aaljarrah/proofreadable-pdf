#!/usr/bin/env python3
"""
Arabic PDF Proofreading Chunker
================================

Processes large mixed Arabic PDFs (text + scanned pages), applies OCR where needed,
and splits content into ChatGPT-ready markdown chunks for proofreading.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple
import pypdf
from pdf2image import convert_from_path
import pytesseract
from PIL import Image


class PageContent:
    """Represents the extracted content from a single PDF page."""
    
    def __init__(self, page_num: int, text: str, source_type: str):
        self.page_num = page_num
        self.text = text
        self.source_type = source_type  # "TEXT" or "OCR"
        
    def word_count(self) -> int:
        """Count words in the page text."""
        return len(self.text.split())


class PDFChunker:
    """Main class for processing PDF and creating chunks."""
    
    def __init__(self, pdf_path: str, max_words: int, max_pages: int, ocr_lang: str):
        self.pdf_path = Path(pdf_path)
        self.max_words = max_words
        self.max_pages = max_pages
        self.ocr_lang = ocr_lang
        
        # Create output directories
        self.output_dir = Path("output")
        self.chunks_dir = self.output_dir / "chunks"
        self.logs_dir = Path("logs")
        
        for directory in [self.output_dir, self.chunks_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            "total_pages": 0,
            "text_pages": 0,
            "ocr_pages": 0,
            "total_chunks": 0
        }
        
    def validate_pdf(self) -> bool:
        """Validate that the PDF exists and is readable."""
        if not self.pdf_path.exists():
            print(f"ERROR: PDF file not found: {self.pdf_path}")
            return False
        
        if not self.pdf_path.is_file():
            print(f"ERROR: Path is not a file: {self.pdf_path}")
            return False
        
        try:
            with open(self.pdf_path, 'rb') as f:
                pypdf.PdfReader(f)
            return True
        except Exception as e:
            print(f"ERROR: Cannot read PDF file: {e}")
            return False
    
    def extract_text_from_page(self, pdf_reader: pypdf.PdfReader, page_num: int) -> PageContent:
        """
        Extract text from a single PDF page.
        If text extraction fails or yields too little text, use OCR.
        
        Args:
            pdf_reader: PyPDF reader object
            page_num: Page number (0-indexed)
            
        Returns:
            PageContent object with extracted text
        """
        display_page_num = page_num + 1  # Human-readable page number
        
        try:
            # Try text extraction first
            page = pdf_reader.pages[page_num]
            extracted_text = page.extract_text() or ""
            
            # Check if we have enough text
            if len(extracted_text.strip()) >= 40:
                print(f"  Page {display_page_num}/{self.stats['total_pages']}: TEXT extraction")
                return PageContent(display_page_num, extracted_text.strip(), "TEXT")
            
            # Fall back to OCR
            print(f"  Page {display_page_num}/{self.stats['total_pages']}: Running OCR...")
            ocr_text = self._ocr_page(page_num)
            return PageContent(display_page_num, ocr_text, "OCR")
            
        except Exception as e:
            print(f"  WARNING: Error processing page {display_page_num}: {e}")
            print(f"  Attempting OCR as fallback...")
            try:
                ocr_text = self._ocr_page(page_num)
                return PageContent(display_page_num, ocr_text, "OCR")
            except Exception as ocr_error:
                print(f"  ERROR: OCR also failed for page {display_page_num}: {ocr_error}")
                return PageContent(display_page_num, "", "ERROR")
    
    def _ocr_page(self, page_num: int) -> str:
        """
        Convert a PDF page to image and run OCR on it.
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            OCR-extracted text
        """
        try:
            # Convert single page to image
            images = convert_from_path(
                self.pdf_path,
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=300  # Higher DPI for better OCR accuracy
            )
            
            if not images:
                return ""
            
            # Run OCR on the image
            image = images[0]
            ocr_text = pytesseract.image_to_string(image, lang=self.ocr_lang)
            
            return ocr_text.strip()
            
        except Exception as e:
            raise Exception(f"OCR failed: {e}")
    
    def process_pdf(self) -> List[PageContent]:
        """
        Process all pages in the PDF.
        
        Returns:
            List of PageContent objects
        """
        print(f"\nProcessing PDF: {self.pdf_path}")
        print(f"Configuration:")
        print(f"  Max words per chunk: {self.max_words}")
        print(f"  Max pages per chunk: {self.max_pages}")
        print(f"  OCR language: {self.ocr_lang}")
        print()
        
        pages_content = []
        
        with open(self.pdf_path, 'rb') as pdf_file:
            pdf_reader = pypdf.PdfReader(pdf_file)
            self.stats["total_pages"] = len(pdf_reader.pages)
            
            print(f"Total pages: {self.stats['total_pages']}\n")
            
            # Process each page
            for page_num in range(self.stats["total_pages"]):
                page_content = self.extract_text_from_page(pdf_reader, page_num)
                pages_content.append(page_content)
                
                # Update statistics
                if page_content.source_type == "TEXT":
                    self.stats["text_pages"] += 1
                elif page_content.source_type == "OCR":
                    self.stats["ocr_pages"] += 1
        
        return pages_content
    
    def create_chunks(self, pages_content: List[PageContent]) -> List[List[PageContent]]:
        """
        Group pages into chunks based on max_words and max_pages limits.
        
        Args:
            pages_content: List of all page contents
            
        Returns:
            List of chunks, where each chunk is a list of PageContent objects
        """
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for page_content in pages_content:
            page_words = page_content.word_count()
            
            # Check if adding this page would exceed limits
            if current_chunk:
                would_exceed_words = (current_word_count + page_words) > self.max_words
                would_exceed_pages = len(current_chunk) >= self.max_pages
                
                if would_exceed_words or would_exceed_pages:
                    # Save current chunk and start new one
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_word_count = 0
            
            # Add page to current chunk
            current_chunk.append(page_content)
            current_word_count += page_words
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def write_chunk_file(self, chunk_index: int, chunk_pages: List[PageContent]) -> None:
        """
        Write a chunk to a markdown file.
        
        Args:
            chunk_index: Index of the chunk (0-based)
            chunk_pages: List of PageContent objects in this chunk
        """
        start_page = chunk_pages[0].page_num
        end_page = chunk_pages[-1].page_num
        
        filename = f"chunk_{chunk_index + 1:03d}_p{start_page:03d}-p{end_page:03d}.md"
        filepath = self.chunks_dir / filename
        
        # Build the page text section
        text_sections = []
        for page in chunk_pages:
            text_sections.append(f"---- [Page {page.page_num}] ----\n{page.text}\n")
        
        combined_text = "\n".join(text_sections)
        
        # Create the full markdown content
        content = f"""### CHUNK_META
CHUNK_ID: {chunk_index + 1:03d}
PAGES: {start_page}-{end_page}

### INSTRUCTIONS_FOR_CHATGPT
Proofread the following Arabic text:
- Correct spelling, grammar, punctuation, hamza, and spacing.
- Preserve the exact meaning and tone.
- Preserve headings, bullet points, numbering, and formatting as much as possible.
- Do NOT summarize, shorten, or remove content.
- Do NOT add explanations inside the text.
- Return:
  1. The fully corrected text only.
  2. A short bullet list of recurring issues you fixed (in Arabic).

### TEXT
{combined_text}"""
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Created: {filename} (Pages {start_page}-{end_page}, {len(chunk_pages)} pages)")
    
    def write_log(self, pages_content: List[PageContent]) -> None:
        """
        Write the page source log file.
        
        Args:
            pages_content: List of all page contents
        """
        log_file = self.logs_dir / "page_sources.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("Page Number | Source Type\n")
            f.write("-" * 30 + "\n")
            
            for page in pages_content:
                f.write(f"{page.page_num:6d}      | {page.source_type}\n")
        
        print(f"\nLog written to: {log_file}")
    
    def run(self) -> bool:
        """
        Main execution method.
        
        Returns:
            True if successful, False otherwise
        """
        # Validate PDF
        if not self.validate_pdf():
            return False
        
        # Process all pages
        try:
            pages_content = self.process_pdf()
        except Exception as e:
            print(f"\nERROR: Failed to process PDF: {e}")
            return False
        
        # Create chunks
        print(f"\n{'='*60}")
        print("Creating chunks...")
        print('='*60)
        
        chunks = self.create_chunks(pages_content)
        self.stats["total_chunks"] = len(chunks)
        
        # Write chunk files
        for chunk_index, chunk_pages in enumerate(chunks):
            self.write_chunk_file(chunk_index, chunk_pages)
        
        # Write log
        self.write_log(pages_content)
        
        # Print summary
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print('='*60)
        print(f"Total pages processed: {self.stats['total_pages']}")
        print(f"  - Text-based pages: {self.stats['text_pages']}")
        print(f"  - OCR-processed pages: {self.stats['ocr_pages']}")
        print(f"Total chunks created: {self.stats['total_chunks']}")
        print(f"\nChunks saved to: {self.chunks_dir}")
        print('='*60)
        
        return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process large Arabic PDFs and create ChatGPT-ready chunks for proofreading.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input/document.pdf
  %(prog)s input/document.pdf --max-words 5000 --max-pages 15
  %(prog)s input/document.pdf --ocr-lang ara
        """
    )
    
    parser.add_argument(
        'pdf_path',
        help="Path to the input PDF file"
    )
    
    parser.add_argument(
        '--max-words',
        type=int,
        default=3500,
        help="Maximum words per chunk (default: 3500)"
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=10,
        help="Maximum pages per chunk (default: 10)"
    )
    
    parser.add_argument(
        '--ocr-lang',
        type=str,
        default='ara+eng',
        help="OCR language(s) for Tesseract (default: ara+eng)"
    )
    
    args = parser.parse_args()
    
    # Create and run the chunker
    chunker = PDFChunker(
        pdf_path=args.pdf_path,
        max_words=args.max_words,
        max_pages=args.max_pages,
        ocr_lang=args.ocr_lang
    )
    
    success = chunker.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

