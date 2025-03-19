from typing import Dict, Any

from src.service.database.models.hnode          import HNode
from src.domain.on_metal.tasks.pdf.pdf_analyzer import PdfAnalyzer

class Analyzer:
    @staticmethod
    def analyze_file(hnode: HNode) -> Dict[str, Any]:
        file_ext = hnode.fs_file_extension.strip().lower()
        if file_ext == "pdf":
            pdf_analyzer    = PdfAnalyzer()
            pdf_result      = pdf_analyzer.analyze(hnode.fs_full_path)
            pdf_metadata    = pdf_result.metadata
            return pdf_metadata
        else:
            return {}

    @staticmethod
    def analyze_folder(hnode: HNode):
        print("Not implemented yet.")
        pass

