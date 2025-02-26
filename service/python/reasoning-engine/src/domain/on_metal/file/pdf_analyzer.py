from typing      import Dict, Any, List
from pathlib     import Path
from dataclasses import dataclass

from docling.document_converter import DocumentConverter

import logging


@dataclass
class PdfAnalysisResult:
    metadata: Dict[str, Any]
    structure: Dict[str, Any]
    summary: str
    images: List[Dict[str, Any]]
    semantic_chunks: List[Dict[str, Any]]


class PdfAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze(self, file_path: str) -> PdfAnalysisResult:
        self.logger.info(f"> Analyzing PDF file: {file_path}")

        pdf_path = Path(file_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {file_path}")
            raise FileNotFoundError("PDF file not found")

        try:

            converter = DocumentConverter()
            result = converter.convert(pdf_path)
            print(result.document.export_to_markdown())


        except Exception as e:
            self.logger.error(f"> Failed to analyze PDF: {str(e)}", exc_info=True)
            raise Exception(f"Failed to analyze PDF: {str(e)}")

    def _extract_metadata(self, doc) -> Dict[str, Any]:
        return {
            "num_pages":     len(doc),
            "metadata":      doc.metadata,
            "title":         doc.metadata.get("title", ""),
            "author":        doc.metadata.get("author", ""),
            "creation_date": doc.metadata.get("creationDate", "")
        }
