import io

import pdfplumber

from document.content.content_type import ContentType
from config.detection_config import DetectionConfig
from document.content.detection_result import DetectionResult
from document.models.file_format import FileFormat

_MAGIC_BYTES: list[tuple[bytes, FileFormat]] = [
    (b"%PDF",     FileFormat.PDF),
    (b"\xD0\xCF", FileFormat.DOC),
    (b"{\rtf",    FileFormat.RTF),
    (b"\x89PNG",  FileFormat.PNG),
    (b"\xFF\xD8", FileFormat.JPG),
    (b"II*\x00",  FileFormat.TIFF),
    (b"MM\x00*",  FileFormat.TIFF),
]

_IMAGE_FORMATS = {FileFormat.PNG, FileFormat.JPG, FileFormat.TIFF}
_TEXT_FORMATS  = {FileFormat.DOCX, FileFormat.DOC, FileFormat.ODT,
                  FileFormat.RTF,  FileFormat.TXT, FileFormat.HTML}


class UnknownFormatError(Exception):
    """Raised when the file format cannot be determined."""


class ConflictingFormatError(Exception):
    """Raised when magic bytes and extension disagree."""


class Detector:
    def __init__(self, config: DetectionConfig = DetectionConfig()) -> None:
        self.config = config

    def detect(
            self,
            file_path: str | None = None,
            file_data: bytes | None = None,
    ) -> DetectionResult:
        if file_path is None and file_data is None:
            raise ValueError("Either 'file_path' or 'file_data' must be provided.")

        header = self._read_header(file_path, file_data)

        file_format = self._detect_format(header, file_path)
        content_type = self._detect_content_type(file_format, file_path, file_data)

        return DetectionResult(format=file_format, content_type=content_type)


    def _read_header(self, file_path: str | None, file_data: bytes | None) -> bytes:
        if file_data is not None:
            return file_data[: self.config.magic_bytes_length]
        with open(file_path, "rb") as f:
            return f.read(self.config.magic_bytes_length)

    def _detect_format(self, header: bytes, file_path: str | None) -> FileFormat:
        detected: FileFormat | None = None

        for magic, fmt in _MAGIC_BYTES:
            if header.startswith(magic):
                detected = fmt
                break

        if detected is None:
            if file_path is None:
                raise UnknownFormatError(
                    "Cannot determine format: no magic bytes matched and no file_path provided."
                )
            import os
            ext = os.path.splitext(file_path)[1].lower()
            ext_map = {
                ".docx": FileFormat.DOCX,
                ".odt": FileFormat.ODT,
                ".txt": FileFormat.TXT,
                ".html": FileFormat.HTML,
                ".htm": FileFormat.HTML,
                ".rtf": FileFormat.RTF,
            }
            if ext not in ext_map:
                raise UnknownFormatError(f"Unsupported or unrecognized format: '{ext}'")
            detected = ext_map[ext]

        if file_path is not None:
            import os
            ext = os.path.splitext(file_path)[1].lower()
            ext_map = {
                ".pdf": FileFormat.PDF,
                ".docx": FileFormat.DOCX,
                ".doc": FileFormat.DOC,
                ".odt": FileFormat.ODT,
                ".rtf": FileFormat.RTF,
                ".txt": FileFormat.TXT,
                ".html": FileFormat.HTML,
                ".htm": FileFormat.HTML,
                ".png": FileFormat.PNG,
                ".jpg": FileFormat.JPG,
                ".jpeg": FileFormat.JPG,
                ".tiff": FileFormat.TIFF,
                ".tif": FileFormat.TIFF,
            }
            expected = ext_map.get(ext)
            if expected is not None and expected != detected:
                raise ConflictingFormatError(
                    f"Magic bytes indicate '{detected.value}' but extension is '{ext}'."
                )

        return detected

    def _detect_content_type(
            self,
            file_format: FileFormat,
            file_path: str | None,
            file_data: bytes | None,
    ) -> ContentType:
        if file_format in _IMAGE_FORMATS:
            return ContentType.IMAGE

        if file_format in _TEXT_FORMATS:
            return ContentType.TEXT

        if file_format == FileFormat.PDF:
            return self._detect_pdf_content_type(file_path, file_data)

        raise UnknownFormatError(f"Cannot determine content type for format '{file_format}'.")

    def _detect_pdf_content_type(
            self,
            file_path: str | None,
            file_data: bytes | None,
    ) -> ContentType:
        source = file_path if file_path is not None else io.BytesIO(file_data)

        with pdfplumber.open(source) as pdf:
            total = len(pdf.pages)
            indices = self._sample_indices(total)
            results = [self._page_has_text(pdf.pages[i]) for i in indices]

        has_text = any(results)
        has_image = not all(results)

        if has_text and has_image:
            return ContentType.MIXED
        if has_text:
            return ContentType.TEXT
        return ContentType.IMAGE

    def _sample_indices(self, total: int) -> list[int]:
        if total <= self.config.sample_pages:
            return list(range(total))

        step = (total - 1) / (self.config.sample_pages - 1)
        return sorted({round(i * step) for i in range(self.config.sample_pages)})

    @staticmethod
    def _page_has_text(page) -> bool:
        text = page.extract_text()
        return bool(text and text.strip())