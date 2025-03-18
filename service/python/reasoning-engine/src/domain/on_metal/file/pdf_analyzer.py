from typing      import Dict, Any, List
from pathlib     import Path
from dataclasses import dataclass
from jsonpointer import resolve_pointer

# import pprint

from src.domain.on_metal.logger import get_logger
logger = get_logger(__name__)

from src.domain.on_metal.file.converter      import FileConverter
from src.domain.on_metal.nlp.text_embeddings import TextEmbeddings
from src.domain.on_metal.nlp.text_summarizer import TextSummarizer


@dataclass
class PdfAnalysisResult:
    metadata:        Dict[str, Any]
    structure:       Dict[str, Any]
    summary:         str
    images:          List[Dict[str, Any]]
    naive_chunks:    List[Dict[str, Any]]
    semantic_chunks: List[Dict[str, Any]]

class PdfAnalyzer:
    @staticmethod
    def analyze(file_path: str) -> PdfAnalysisResult:
        logger.info(f"> Analyzing PDF file: {file_path}")

        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found {file_path}")

        try:
            results                     = {}
            pdf_document_tree           = FileConverter.pdf_to('json', file_path)
            pdf_processed_document_tree = PdfAnalyzer.process_tree_node(pdf_document_tree["body"], pdf_document_tree, results)
            print(pdf_processed_document_tree)

        except Exception as e:
            raise Exception(f"Failed to analyze PDF: {str(e)}")

    @staticmethod
    def process_tree_node(node, pdf_document_tree, results):
        node_id = node["self_ref"]

        try:
            if "children" in node:  # @todo move to process_non-leaf node
                children_texts = []
                for child_pointer in node["children"]:
                    child_ref    = child_pointer["$ref"]
                    child_node   = resolve_pointer(pdf_document_tree, child_ref)
                    child_result = PdfAnalyzer.process_tree_node(child_node, pdf_document_tree, results)
                    child_text   = child_result["raw_text"] if child_result["raw_text"] else child_result["children_summary"]
                    if child_text:
                        children_texts.append(child_text)

                children_summary = TextSummarizer.summarize(children_texts) if children_texts else ""
                result = {
                    "raw_text":                     None,
                    "children_summary":             children_summary,
                    "embeddings_raw":               None,
                    "embeddings_children_summary":  TextEmbeddings.embed(children_summary) if children_summary else None
                }
            else:  # @todo move to process_leaf node
                raw_text         = node.get("text", None)
                children_summary = None  # @todo tbc if use "" instead
                result           = {
                    "raw_text":                     raw_text,
                    "children_summary":             children_summary,
                    "embeddings_raw":               TextEmbeddings.embed(raw_text) if raw_text else None,
                    "embeddings_children_summary":  None
                }

        except Exception as e:
            raise Exception(f"Failed to process pdf tree: {str(e)}")

        results[node_id] = result
        return results








