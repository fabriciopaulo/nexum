from dataclasses import dataclass

from config.nexus_config import NexumConfig


@dataclass
class PDFImageConfig(NexumConfig):
    language: str = "por"
    dpi: int = 300
    psm: int = 3
    skip_pages: int = 0