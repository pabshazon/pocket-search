from src.service.database.models.hnode import HNode
from src.domain.on_metal.tasks.pdf.pdf_analyzer import PdfAnalyzer
from typing import Dict, Any


class Analyzer:
    @staticmethod
    def analyze_file(hnode: HNode) -> Dict[str, Any]:
        file_ext = hnode.fs_file_extension.strip().lower()
        if file_ext == "pdf":
            print(f"PDF file {hnode.fs_full_path}")
            pdf_analyzer    = PdfAnalyzer()
            print("PDF analyzer initialized.")
            pdf_result      = pdf_analyzer.analyze(hnode.fs_full_path)
            print("PDF result obtained.")
            pdf_metadata    = pdf_result.metadata
            print("PDF metadata obtained.")
            return pdf_metadata
        else:
            print(f"Unknown file type {hnode.fs_file_extension}")
            return {}

    @staticmethod
    def analyze_folder(hnode: HNode):
        print("Not implemented yet.")
        pass
