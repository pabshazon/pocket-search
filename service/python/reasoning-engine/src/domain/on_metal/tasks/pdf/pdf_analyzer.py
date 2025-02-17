from typing import Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
import fitz  # PyMuPDF
from src.domain.on_metal.tasks.pdf.extractors.text_extractor    import PdfTextExtractor
from src.domain.on_metal.tasks.pdf.extractors.image_extractor   import PdfImageExtractor
from src.domain.on_metal.tasks.pdf.analyzers.semantic_analyzer  import SemanticAnalyzer
from src.domain.on_metal.tasks.pdf.analyzers.layout_analyzer    import LayoutAnalyzer
from src.domain.on_metal.tasks.pdf.summarizer                   import PdfSummarizer
from src.domain.on_metal.nlp.models.embeddings                  import DocumentEmbedder

@dataclass
class PdfAnalysisResult:
    metadata: Dict[str, Any]
    structure: Dict[str, Any]
    summary: str
    images: List[Dict[str, Any]]
    semantic_chunks: List[Dict[str, Any]]

class PdfAnalyzer:
    def __init__(self):
        print("Initializing PDF analyzer...")
        self.text_extractor     = PdfTextExtractor()
        print("Text extractor initialized.")
        self.image_extractor    = PdfImageExtractor()
        print("Image extractor initialized.")
        self.semantic_analyzer  = SemanticAnalyzer()
        print("Semantic analyzer initialized.")
        self.layout_analyzer    = LayoutAnalyzer()
        print("Layout analyzer initialized.")
        self.summarizer         = PdfSummarizer()
        print("Summarizer initialized.")
        self.document_embedder  = DocumentEmbedder.create_default()

    def analyze(self, file_path: str) -> PdfAnalysisResult:
        print(f"Analyzing PDF file: {file_path}")
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError("PDF file not found")
            
        try:
            doc = fitz.open(pdf_path)
            
            metadata = self._extract_metadata(doc)
            print(f"Metadata: {metadata}")
            
            text_content = self.text_extractor.extract(doc)
            print(f"Text content extracted.")
            # Create properly structured semantic chunks placeholder
            semantic_chunks = [{
                "content": "Sample placeholder content",
                "chunk_type": "paragraph",  # Ensuring valid chunk_type for summarizer
                "position": {"page": 1, "top": 0, "bottom": 0}
            }]
            
            layout_info = {"status": "placeholder", "message": "Layout analysis not implemented yet"}
            images = []  # Empty list as placeholder
            
            summary = self.summarizer.summarize(semantic_chunks)
            print(f"Summary: {summary}")
            return PdfAnalysisResult(
                metadata=metadata,
                structure=layout_info,
                summary=summary,
                images=images,
                semantic_chunks=semantic_chunks
            )
                
        except Exception as e:
            raise Exception(f"Failed to analyze PDF: {str(e)}")

    def _extract_metadata(self, doc) -> Dict[str, Any]:
        return {
            "num_pages":        len(doc),
            "metadata":         doc.metadata,
            "title":            doc.metadata.get("title", ""),
            "author":           doc.metadata.get("author", ""),
            "creation_date":    doc.metadata.get("creationDate", "")
        }
