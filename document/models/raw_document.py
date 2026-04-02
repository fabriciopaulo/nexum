from dataclasses import dataclass
from typing import Any

from document.content.content_type import ContentType
from document.models.file_format import FileFormat


@dataclass
class RawDocument:
    text: str
    format: FileFormat
    content_type: ContentType
    metadata: dict[str, Any]