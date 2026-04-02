from dataclasses import dataclass


@dataclass
class DetectionConfig:
    sample_pages: int = 3
    magic_bytes_length: int = 8