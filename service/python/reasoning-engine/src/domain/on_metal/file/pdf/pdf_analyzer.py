from typing         import Dict, Any, List
from pathlib        import Path
from dataclasses    import dataclass
import fitz  # PyMuPDF
import logging

from src.domain.on_metal.tasks.pdf.extractors.text_extractor import PdfTextExtractor
from src.domain.on_metal.tasks.pdf.summarizer                import PdfSummarizer
from src.domain.on_metal.tasks.pdf.document_type_classifier  import DocumentTypeClassifier
from src.domain.on_metal.nlp.model.document_descriptor       import TextDescriptor
from src.domain.on_metal.nlp.model.text_summarizer           import TextSummarizer

@dataclass
class PdfAnalysisResult:
    pdf_metadata:    Dict[str, Any]
    summary:         str
    description:     str
    doc_type:        str
    doc_subtype:     str


class PdfAnalyzer:
    def __init__(self):
        self.text_extractor         = PdfTextExtractor()
        self.doc_type_classifier    = DocumentTypeClassifier()
        self.doc_subtype_classifier = DocumentTypeClassifier()
        self.summarizer             = TextSummarizer()
        self.document_descriptor    = TextDescriptor()
        self.logger                 = logging.getLogger(__name__)


    def analyze(self, file_path: str) -> PdfAnalysisResult:
        self.logger.debug(f"> Analyzing PDF file: {file_path}")

        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            pdf_doc       = fitz.open(pdf_path)
            pdf_metadata  = self._extract_metadata(pdf_doc)
            text_contents = self.text_extractor.extract_all_text(pdf_doc)
            
            pdf_doc_type, pdf_doc_subtype = self.doc_type_classifier.classify(text_contents)
            self.logger.info(f"> PDF Document Type: {pdf_doc_type}")
            self.logger.info(f"> PDF Document Subtype: {pdf_doc_subtype}")

            pdf_summary = self.summarizer.summarize(text_contents)
            self.logger.info(f"> Summary: {pdf_summary}")

            pdf_description = self.document_descriptor.describe(text_contents)
            self.logger.info(f"> Summary: {pdf_description}")

            return PdfAnalysisResult(
                pdf_metadata = pdf_metadata,
                summary      = pdf_summary,
                description  = pdf_description,
                doc_type     = pdf_doc_type,
                doc_subtype  = pdf_doc_subtype
            )

        except Exception as e:
            self.logger.error(f"> Failed to analyze PDF: {str(e)}", exc_info=True)
            raise Exception(f"Failed to analyze PDF: {str(e)}")

    @staticmethod
    def _extract_metadata(doc) -> Dict[str, Any]:
        return {
            "num_pages":     len(doc),
            "metadata":      doc.metadata,
            "title":         doc.metadata.get("title", ""),
            "author":        doc.metadata.get("author", ""),
            "creation_date": doc.metadata.get("creationDate", "")
        }
