from __future__ import annotations

import io
from typing import Any

import pdfplumber
import pytesseract

from document.content.content_type import ContentType
from document.models.file_format import FileFormat
from document.models.raw_document import RawDocument
from document.parser.base_parser import BaseParser

from config.pdf_image_config import PDFImageConfig



class PDFImageParser(BaseParser):
    extensions = ["pdf"]

    def __init__(self, config: PDFImageConfig = PDFImageConfig()) -> None:
        self.config = config

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
                "ocr_language": self.config.language,
                "ocr_dpi": self.config.dpi,
            }

            for page_number, page in enumerate(pdf.pages):
                if page_number < self.config.skip_pages:
                    continue
                image = page.to_image(resolution=self.config.dpi).original
                text = pytesseract.image_to_string(
                    image,
                    lang=self.config.language,
                    config="--psm 1"
                )
                if text and text.strip():
                    pages_text.append(text.strip())

        return RawDocument(
            text="\n\n".join(pages_text),
            format=FileFormat.PDF,
            content_type=ContentType.IMAGE,
            metadata=metadata,
        )