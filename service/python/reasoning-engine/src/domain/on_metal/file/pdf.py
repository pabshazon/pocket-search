import json
import time

import os
from typing      import Dict, Any, List, Optional
from pathlib     import Path
from dataclasses import dataclass

import fitz  # PyMuPDF
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

from src.domain.on_metal.logger import get_logger
from src.config.repository_config import DOCS_REPOSITORY_PATH

logger = get_logger(__name__)


@dataclass
class PdfAnalysisResults:
    metadata:        Dict[str, Any]
    structure:       Dict[str, Any]
    summary:         str
    images:          List[Dict[str, Any]]
    naive_chunks:    List[Dict[str, Any]]
    semantic_chunks: List[Dict[str, Any]]
    overlapped_fixed_chunks: List[Dict[str, Any]]

class PdfFile:
    @staticmethod
    def transform_to_md(file_path: str, persist: bool =True):
        logger.info(f"> Transforming PDF file to MD: {file_path}")
        try:
            input_doc_path = os.path.abspath(str(file_path))

            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.do_table_structure = True
            pipeline_options.table_structure_options.do_cell_matching = True
            pipeline_options.ocr_options.lang = ["es"]
            pipeline_options.accelerator_options = AcceleratorOptions(
                num_threads=4, device=AcceleratorDevice.AUTO
            )

            doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            start_time = time.time()
            conv_result = doc_converter.convert(input_doc_path)
            end_time = time.time() - start_time

            logger.debug(f"Document converted to docling in {end_time:.2f} seconds.")

            output_dir = DOCS_REPOSITORY_PATH
            output_dir.mkdir(parents=True, exist_ok=True)
            
            doc_filename = conv_result.input.file.stem
            markdown_doc = conv_result.document.export_to_markdown()
            if persist:
                # @todo review what happens with below async
                PdfAnalyzer._persist_file_intermediate_forms_in_local_repo(conv_result, output_dir, doc_filename)

            return markdown_doc

        except Exception as e:
            logger.error(f"Failed to transform_to_md a PDF: {file_path}", exc_info=True)
            raise Exception(f"Failed to transform_to_md a PDF: {str(e)}") from e

    @staticmethod
    async def _persist_file_intermediate_forms_in_local_repo(conv_result, output_dir: Path, doc_filename: str) -> str:
        # Export Deep Search document JSON format
        with (output_dir / f"{doc_filename}.json").open("w", encoding="utf-8") as fp:
            fp.write(json.dumps(conv_result.document.export_to_dict()))
        
        # Export Text format
        with (output_dir / f"{doc_filename}.txt").open("w", encoding="utf-8") as fp:
            fp.write(conv_result.document.export_to_text())
        
        # Export Markdown format and generate summary
        with (output_dir / f"{doc_filename}.md").open("w", encoding="utf-8") as fp:
            fp.write(conv_result.document.export_to_markdown())
        
        # Export Document Tags format
        with (output_dir / f"{doc_filename}.doctags").open("w", encoding="utf-8") as fp:
            fp.write(conv_result.document.export_to_document_tokens())

    @staticmethod
    def extract_metadata(pdf_path) -> Dict[str, Any]:
        # @todo tbc if we need fitz for this, or if docling already provides the metadata we need.
        pdf_doc = fitz.open(pdf_path)
        return {
            "num_pages":     len(pdf_doc),
            **pdf_doc.metadata,
        }

    @staticmethod
    def get_md_from_file(pdf_path: str) -> Optional[str]:
        try:
            path = Path(pdf_path)
            doc_filename = path.stem
            md_path = DOCS_REPOSITORY_PATH / f"{doc_filename}.md"
            
            if not md_path.exists():
                logger.warning(f"Markdown file not found for PDF: {pdf_path}")
                return None
                
            with md_path.open("r", encoding="utf-8") as fp:
                return fp.read()
                
        except Exception as e:
            logger.error(f"Error reading markdown file for PDF {pdf_path}: {str(e)}")
            return None



