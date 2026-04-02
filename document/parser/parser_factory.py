from typing import Type

from document.parser.base_parser import BaseParser
from document.models import ContentType
from document.content.detection_result import DetectionResult
from document.models import FileFormat
from config.nexus_config import NexumConfig


class ParserNotRegisteredError(Exception):
    """Raised when no parser is registered for the given format and content type."""


class ParserFactory:
    _registry: dict[tuple[FileFormat, ContentType], Type[BaseParser]] = {}

    @classmethod
    def register(
            cls,
            file_format: FileFormat,
            content_type: ContentType,
            parser: Type[BaseParser],
    ) -> None:
        cls._registry[(file_format, content_type)] = parser

    @classmethod
    def from_detection(cls, detection: DetectionResult, config: NexumConfig = None) -> BaseParser:
        key = (detection.format, detection.content_type)
        parser_cls = cls._registry.get(key)

        if parser_cls is None:
            raise ParserNotRegisteredError(
                f"No parser registered for format='{detection.format.value}' "
                f"and content_type='{detection.content_type.value}'."
            )

        if config:
            return parser_cls(config=config)

        return parser_cls()
