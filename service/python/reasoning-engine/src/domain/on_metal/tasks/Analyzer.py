import os

from src.service.database.models.hnode              import HNode
from src.domain.on_metal.file.pdf_analyzer          import PdfAnalyzer, PdfAnalysisResult
from src.domain.on_metal.nlp.model.text_summarizer  import TextSummarizer

from src.domain.on_metal.logger import get_logger
logger = get_logger(__name__)

class Analyzer:
    @staticmethod
    async def analyze_file(hnode: HNode) -> PdfAnalysisResult | None:  # @todo add interface for results of any file type instead of None.
        file_ext = hnode.fs_file_extension.strip().lower()
        if file_ext == "pdf":
            result = PdfAnalysisResult(
                metadata                = {},
                summary                 = "",
                structure               = {},
                images                  = [{}],
                semantic_chunks         = [{}],
                naive_chunks            = [{}],
                overlapped_fixed_chunks = [{}]
            )
            # @hack below to test quicker
            # pdf_as_md         = PdfAnalyzer.transform_to_md(hnode.fs_full_path)
            pdf_as_md           = PdfAnalyzer.get_md_from_file(hnode.fs_full_path)

            text_summarizer     = TextSummarizer()
            pdf_summary_s2s     = await text_summarizer.summarize_with_seq_to_seq(pdf_as_md)
            # pdf_summary_decoder = text_summarizer.summarize_with_decoder_llm(pdf_as_md)
            pdf_metadata        = PdfAnalyzer.extract_metadata(hnode.fs_full_path)

            result.summary  = pdf_summary_s2s
            result.metadata = pdf_metadata

            logger.info("Final Summary:")
            logger.info(result.summary)
            return result

    @staticmethod
    def analyze_folder(hnode: HNode):
        print("Not implemented yet.")
        pass
