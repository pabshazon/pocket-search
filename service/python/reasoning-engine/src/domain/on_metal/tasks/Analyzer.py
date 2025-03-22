from src.service.database.sqlite.models.hnode import HNode
from src.domain.on_metal.file.pdf                  import PdfFile, PdfAnalysisResults
from src.domain.on_metal.nlp.model.text_summarizer import TextSummarizer

from src.domain.on_metal.logger import get_logger
logger = get_logger(__name__)

class Analyzer:
    @staticmethod
    async def analyze_file(hnode: HNode) -> PdfAnalysisResults | None:  # @todo add interface for results of any file type instead of None.
        file_ext = hnode.fs_file_extension.strip().lower()
        if file_ext == "pdf":
            result = PdfAnalysisResults(
                metadata                = {},
                summary                 = "",
                structure               = {},
                images                  = [{}],
                semantic_chunks         = [{}],
                naive_chunks            = [{}],
                overlapped_fixed_chunks = [{}]
            )
            # @hack below to test quicker @todo remove
            # pdf_as_md         = PdfAnalyzer.transform_to_md(hnode.fs_full_path)
            logger.info(f"> Start Analysis task for {hnode.fs_full_path}")
            pdf_as_md           = PdfFile.get_md_from_file(hnode.fs_full_path)

            text_summarizer     = TextSummarizer()
            pdf_summary_s2s     = await text_summarizer.summarize_with_seq_to_seq(pdf_as_md)
            pdf_metadata        = PdfFile.extract_metadata(hnode.fs_full_path)

            result.summary  = pdf_summary_s2s
            result.metadata = pdf_metadata

            logger.info("> Final Summary & Metadata:")
            logger.info(result.summary)
            logger.info(result.metadata)

            # Store hnode metadata
            # cs_hnode_summary will contain the summary
            # cs_hnode_title?
            # cs_what_is_fs_file_about
            # cs_explain_contains
            # cs_what_info_can_be_found
            # cs_tags_obvious
            # cs_tags_extended




    @staticmethod
    def analyze_folder(hnode: HNode):
        print("Not implemented yet.")
        pass
