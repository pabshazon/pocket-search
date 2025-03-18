from typing import List, Dict, Any
import fitz
# import spacy
from dataclasses import dataclass
from src.domain.on_metal.logger import get_logger
logger = get_logger(__name__)


class PdfTextExtractor:
    def extract_all_text(self, doc: fitz.Document) -> str:
        try:
            full_text = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                full_text.append(text)
            
            return "\n".join(full_text)
                
        except Exception as e:
            self.logger.error(f"PDF text extraction failed: {str(e)}")
            raise Exception(f"PDF text extraction failed: {str(e)}")
    
    def _determine_block_type(self, block: Dict[str, Any]) -> str:
        """Determine the type of text block based on its properties."""
        # Check for common block characteristics
        if "lines" not in block:
            return "unknown"
            
        lines = block.get("lines", [])
        if not lines:
            return "empty"
            
        # Get the font information from the first span of the first line
        try:
            first_line = lines[0]
            spans = first_line.get("spans", [])
            if spans:
                first_span = spans[0]
                font_size = first_span.get("size", 0)
                flags = first_span.get("flags", 0)
                
                # Basic heuristics for block type determination
                if font_size > 14:
                    return "heading"
                elif flags & 16:  # Check if bold
                    return "subheading"
                elif len(lines) == 1:
                    return "single_line"
            
        except (IndexError, KeyError, AttributeError) as e:
            self.logger.debug(f"Error determining block type: {str(e)}")
            
        return "paragraph"
