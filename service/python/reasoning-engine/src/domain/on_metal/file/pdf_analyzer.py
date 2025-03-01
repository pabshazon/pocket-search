from typing      import Dict, Any, List
from pathlib     import Path
from dataclasses import dataclass
from jsonpointer import resolve_pointer

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


logger = logging.getLogger(__name__)

class PdfAnalyzer:
    @staticmethod
    def analyze(file_path: str) -> PdfAnalysisResult:
        logger.info(f"> Analyzing PDF file: {file_path}")

        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found {file_path}")

        try:
            pdf_document_tree = FileConverter.pdf_to('json', file_path)
            PdfAnalyzer.process_tree_node(pdf_document_tree["body"], pdf_document_tree)


        except Exception as e:
            raise Exception(f"Failed to analyze PDF: {str(e)}")

    @staticmethod
    def process_tree_node(node, pdf_document_tree):
        print("node")
        print(node)
        node_id = node["id"]

        if "children" in node:
            children_texts = []
            for child_pointer in node["children"]:
                child_node = resolve_pointer(pdf_document_tree, child_pointer)
                print(child_node)
                child_result = PdfAnalyzer.process_tree_node(child_node, pdf_document_tree)
                child_text = child_result




