from abc import ABC, abstractmethod
from typing import List

from document.models import RawDocument


class BaseParser(ABC):
    extensions: List[str] = []

    @abstractmethod
    def extract(
            self,
            file_path: str | None = None,
            file_data: bytes | None = None,
            **kwargs,
    ) -> RawDocument: ...
