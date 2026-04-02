import io
from typing import Any

import pdfplumber

from document.content.content_type import ContentType
from document.models.file_format import FileFormat
from document.models.raw_document import RawDocument
from document.parser.base_parser import BaseParser


class PDFTextParser(BaseParser):
    extensions = ["pdf"]

    def extract(
            self,
            file_path: str | None = None,
            file_data: bytes | None = None,
            **kwargs,
    ) -> RawDocument:
        if file_path is None and file_data is None:
            raise ValueError("Either 'file_path' or 'file_data' must be provided.")

        source = file_path if file_path is not None else io.BytesIO(file_data)

        pages_text: list[str] = []
        metadata: dict[str, Any] = {}

        with pdfplumber.open(source) as pdf:
            metadata = {
                "page_count": len(pdf.pages),
                "pdf_info": pdf.metadata or {},
            }

            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(text.strip())

        return RawDocument(
            text="\n\n".join(pages_text),
            format=FileFormat.PDF,
            content_type=ContentType.TEXT,
            metadata=metadata,
        )
