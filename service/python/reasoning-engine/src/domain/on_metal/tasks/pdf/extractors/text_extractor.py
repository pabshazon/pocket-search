from typing import List, Dict, Any
import fitz
# import spacy
from dataclasses import dataclass
import logging

@dataclass
class TextBlock:
    text: str
    page_num: int
    bbox: tuple
    block_type: str

class PdfTextExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, doc: fitz.Document) -> List[TextBlock]:
        text_blocks = []
        
        try:
            for page_num, page in enumerate(doc):
                try:
                    blocks = page.get_text("dict")["blocks"]
                    self.logger.debug(f"Found {len(blocks)} blocks on page {page_num}")
                    
                    for block in blocks:
                        if not isinstance(block, dict):
                            self.logger.warning(f"Skipping invalid block on page {page_num}: not a dictionary")
                            continue
                            
                        if block.get("type") != 0:  # Skip non-text blocks
                            self.logger.debug(f"Skipping non-text block type {block.get('type')} on page {page_num}")
                            continue
                            
                        text = block.get("text", "").strip()
                        if not text:
                            self.logger.debug(f"Skipping empty text block on page {page_num}")
                            continue
                            
                        bbox = block.get("bbox")
                        if not bbox:
                            self.logger.warning(f"Skipping block without bbox on page {page_num}")
                            continue
                            
                        text_blocks.append(
                            TextBlock(
                                text=text,
                                page_num=page_num,
                                bbox=bbox,
                                block_type=self._determine_block_type(block)
                            )
                        )
                except Exception as page_error:
                    self.logger.error(f"Error processing page {page_num}: {str(page_error)}")
                    continue

            if not text_blocks:
                self.logger.warning("No text blocks were extracted from the document. Total pages processed: {len(doc)}")
            else:
                self.logger.info(f"Successfully extracted {len(text_blocks)} text blocks from {len(doc)} pages")
                
            return text_blocks
            
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
