from typing import Dict, Any, List, Tuple
import fitz
import numpy as np
from dataclasses import dataclass

@dataclass
class LayoutElement:
    element_type: str
    bbox: Tuple[float, float, float, float]
    confidence: float
    properties: Dict[str, Any]

class LayoutAnalyzer:
    def __init__(self):
        self.min_column_gap = 20  # Minimum pixels between columns
        self.min_heading_size = 12  # Minimum font size for headings
        
    def analyze(self, doc: fitz.Document) -> Dict[str, Any]:
        layout_info = {
            "pages": [],
            "document_structure": {}
        }
        
        for page_num, page in enumerate(doc):
            page_layout = self._analyze_page(page)
            layout_info["pages"].append(page_layout)
            
        # Analyze document-level structure based on individual pages
        layout_info["document_structure"] = self._analyze_document_structure(layout_info["pages"])
        
        return layout_info
    
    def _analyze_page(self, page: fitz.Page) -> Dict[str, Any]:
        page_dict = page.get_text("dict")
        
        # Analyze page layout
        columns = self._detect_columns(page_dict["blocks"])
        elements = self._analyze_elements(page_dict["blocks"])
        
        return {
            "page_number": page.number,
            "dimensions": page.rect,
            "columns": columns,
            "elements": elements,
            "margins": self._detect_margins(page_dict["blocks"]),
            "headers_footers": self._detect_headers_footers(page_dict["blocks"])
        }
    
    def _detect_columns(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Group text blocks into columns based on their x-coordinate positions
        x_coords = [block["bbox"][0] for block in blocks if block["type"] == 0]
        if not x_coords:
            return [{"bbox": None, "confidence": 1.0}]
            
        columns = []
        current_x = None
        current_blocks = []
        
        for block in sorted(blocks, key=lambda b: b["bbox"][0]):
            if block["type"] != 0:
                continue  # Skip non-text blocks
                
            if current_x is None:
                current_x = block["bbox"][0]
                current_blocks.append(block)
            elif abs(block["bbox"][0] - current_x) < self.min_column_gap:
                current_blocks.append(block)
            else:
                # New column found
                columns.append(self._create_column_dict(current_blocks))
                current_x = block["bbox"][0]
                current_blocks = [block]
                
        if current_blocks:
            columns.append(self._create_column_dict(current_blocks))
            
        return columns
    
    def _create_column_dict(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        x0 = min(block["bbox"][0] for block in blocks)
        x1 = max(block["bbox"][2] for block in blocks)
        y0 = min(block["bbox"][1] for block in blocks)
        y1 = max(block["bbox"][3] for block in blocks)
        
        return {
            "bbox": (x0, y0, x1, y1),
            "confidence": 1.0
        }
    
    def _analyze_elements(self, blocks: List[Dict[str, Any]]) -> List[LayoutElement]:
        elements = []
        
        for block in blocks:
            element_type = self._determine_element_type(block)
            if element_type:
                elements.append(LayoutElement(
                    element_type=element_type,
                    bbox=block["bbox"],
                    confidence=0.9,  # Confidence can be enhanced with ML-based approaches
                    properties=self._extract_element_properties(block)
                ))
                
        return elements
    
    def _determine_element_type(self, block: Dict[str, Any]) -> str:
        if block["type"] == 0:  # Text block
            if self._is_heading(block):
                return "heading"
            return "paragraph"
        elif block["type"] == 1:  # Image block
            return "image"
        return "unknown"
    
    def _is_heading(self, block: Dict[str, Any]) -> bool:
        # Simple heuristic: check if the first span's font size is above our heading threshold
        if "lines" in block and block["lines"]:
            spans = block["lines"][0]["spans"]
            if spans and spans[0]["size"] >= self.min_heading_size:
                return True
        return False
    
    def _extract_element_properties(self, block: Dict[str, Any]) -> Dict[str, Any]:
        properties = {
            "font_info": [],
            "text_alignment": "left"  # Default alignment
        }
        
        if block["type"] == 0 and "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    properties["font_info"].append({
                        "font": span.get("font", ""),
                        "size": span.get("size", 0),
                        "color": span.get("color", 0)
                    })
        
        return properties
    
    def _detect_margins(self, blocks: List[Dict[str, Any]]) -> Dict[str, float]:
        # Estimate document margins based on the lowest and highest positions of content blocks
        if not blocks:
            return {"top": 0, "bottom": 0, "left": 0, "right": 0}
            
        left = min(block["bbox"][0] for block in blocks)
        right = max(block["bbox"][2] for block in blocks)
        top = min(block["bbox"][1] for block in blocks)
        bottom = max(block["bbox"][3] for block in blocks)
        
        return {
            "top": top,
            "bottom": bottom,
            "left": left,
            "right": right
        }
    
    def _detect_headers_footers(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Using heuristics, headers/footers may be identified by their recurring position at page boundaries
        return {
            "header": None,
            "footer": None
        }
    
    def _analyze_document_structure(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Analyze overall document consistency based on individual page structures
        return {
            "num_pages": len(pages),
            "consistent_columns": self._check_column_consistency(pages),
            "consistent_margins": self._check_margin_consistency(pages)
        }
    
    def _check_column_consistency(self, pages: List[Dict[str, Any]]) -> bool:
        # Check if the number of columns is consistent across pages
        if not pages:
            return True
            
        num_columns = len(pages[0]["columns"])
        return all(len(page["columns"]) == num_columns for page in pages)
    
    def _check_margin_consistency(self, pages: List[Dict[str, Any]]) -> bool:
        # Check if page margins are consistent across the document
        if not pages:
            return True
            
        margin_tolerance = 5  # Allowable pixel difference
        first_margins = pages[0]["margins"]
        
        return all(
            abs(page["margins"]["left"] - first_margins["left"]) <= margin_tolerance and
            abs(page["margins"]["right"] - first_margins["right"]) <= margin_tolerance
            for page in pages
        )
