from docling.datamodel.base_models      import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
from docling.document_converter         import DocumentConverter, PdfFormatOption

from src.config.models_config import ModelConfig

import logging


logger                    = logging.getLogger(__name__)
local_docling_models_path = ModelConfig(name="docling").local_path

class FileConverter:
    @staticmethod
    def pdf_to(output_type, pdf_path):
        try:
            doc_converter             = DocumentConverter(
                allowed_formats=[InputFormat.PDF],
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=PdfPipelineOptions(
                            artifacts_path=local_docling_models_path,
                        )
                    )
                }
            )
            docling_doc = doc_converter.convert(pdf_path)
            if output_type == 'json':
                return docling_doc.document.export_to_dict()
            elif output_type == 'markdown':
                return docling_doc.document.export_to_markdown()
            else:
                raise Exception(f"Unknown document type '{output_type}'.")


        except Exception as e:
            raise Exception(f"Failed to convert PDF: {str(e)}")

