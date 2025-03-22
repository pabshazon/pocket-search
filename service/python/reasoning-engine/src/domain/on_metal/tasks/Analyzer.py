from src.service.database.chroma.models.hnode      import HnodeCollection
from src.service.database.sqlite.models.hnode      import HNode
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

            data = {
                "summary":  pdf_summary_s2s,
                "metadata": pdf_metadata,
            }

            logger.info(data)
            logger.info(type(data))
            HnodeCollection.upsert_hnode_by_id(hnode.id, data)


    @staticmethod
    def analyze_folder(hnode: HNode):
        print("Not implemented yet.")
        pass
