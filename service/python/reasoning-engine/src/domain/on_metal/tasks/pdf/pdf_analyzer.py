from typing import Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
import fitz  # PyMuPDF
import logging

from src.domain.on_metal.tasks.pdf.extractors.text_extractor    import PdfTextExtractor
from src.domain.on_metal.tasks.pdf.summarizer                   import PdfSummarizer
from src.domain.on_metal.tasks.pdf.document_type_classifier     import DocumentTypeClassifier
from src.domain.on_metal.nlp.model.context_estimator           import ContextEstimator


@dataclass
class PdfAnalysisResult:
    metadata: Dict[str, Any]
    structure: Dict[str, Any]
    summary: str
    images: List[Dict[str, Any]]
    semantic_chunks: List[Dict[str, Any]]

class PdfAnalyzer:
    def __init__(self):
        self.text_extractor      = PdfTextExtractor()
        self.image_extractor     = None
        self.semantic_analyzer   = None
        self.layout_analyzer     = None
        self.doc_type_classifier = DocumentTypeClassifier()
        self.summarizer          = PdfSummarizer()
        # self.document_embedder   = DocumentEmbedder.create_default()
        self.logger = logging.getLogger(__name__)

    def analyze(self, file_path: str) -> PdfAnalysisResult:
        self.logger.info(f"> Analyzing PDF file: {file_path}")
        context_estimator = ContextEstimator()
        context_related_info = context_estimator.estimate_model_contexts()
        self.logger.debug(f"> HW & Context info: {context_related_info}")
        
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {file_path}")
            raise FileNotFoundError("PDF file not found")
            
        try:
            doc = fitz.open(pdf_path)
            
            metadata = self._extract_metadata(doc)
            self.logger.debug(f"> PDF Metadata extracted: {metadata}")
            
            text_content = self.text_extractor.extract_all_text(doc)
            self.logger.debug(f"> Text content extracted with length: {len(text_content)}")
            
            pdf_doc_type, pdf_doc_subtype = self.doc_type_classifier.classify(text_content)
            self.logger.info(f"> PDF Document Type: {pdf_doc_type}")
            self.logger.info(f"> PDF Document Subtype: {pdf_doc_subtype}")
            summary = self.summarizer.summarize(text_content)
            self.logger.info(f"> Summary: {summary}")
            
            return PdfAnalysisResult(
                metadata=metadata,
                summary=summary,
                structure={},
                images=[{}],
                semantic_chunks=[{}]
            )
                
        except Exception as e:
            self.logger.error(f"> Failed to analyze PDF: {str(e)}", exc_info=True)
            raise Exception(f"Failed to analyze PDF: {str(e)}")

    def _extract_metadata(self, doc) -> Dict[str, Any]:
        return {
            "num_pages":        len(doc),
            "metadata":         doc.metadata,
            "title":            doc.metadata.get("title", ""),
            "author":           doc.metadata.get("author", ""),
            "creation_date":    doc.metadata.get("creationDate", "")
        }
