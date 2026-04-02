from dataclasses import dataclass

from document.content.content_type import ContentType
from document.models.file_format import FileFormat


@dataclass
class DetectionResult:
    format: FileFormat
    content_type: ContentType