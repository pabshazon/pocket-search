from typing      import Dict, Any, List
from pathlib     import Path
from dataclasses import dataclass
# import pprint

import logging

from src.domain.on_metal.file.converter import FileConverter


@dataclass
class PdfAnalysisResult:
    metadata:        Dict[str, Any]
    structure:       Dict[str, Any]
    summary:         str
    images:          List[Dict[str, Any]]
    naive_chunks:    List[Dict[str, Any]]
    semantic_chunks: List[Dict[str, Any]]


class PdfAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze(self, file_path: str) -> PdfAnalysisResult:
        self.logger.info(f"> Analyzing PDF file: {file_path}")

        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found {file_path}")

        try:
            json_file_tree = FileConverter.pdf_to('json', file_path)
            # pprint.pprint(json_file_tree, indent=4)

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
