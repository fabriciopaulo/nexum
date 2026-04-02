import re
from typing import List


class HybridChunker:
    def __init__(self, overlap: int = 0):
        self.overlap = max(0, overlap)

        clausula_patterns = [
            r"^cláusula\s+\d+ª?\b",
            r"^\d+\s*cláusula\b",
            r"^\d+ª?\s*cláusula\b",
            r"^cláusula\s+[ivxlcdm]+\b",
            r"^cláusula\s+(primeira|segunda|terceira|quarta|quinta|sexta|sétima|oitava|nona|décima)\b",
        ]

        secao_patterns = [
            r"^seç[aã]o\b",
            r"^seç[aã]o\s+[ivxlcdm]+\b",
        ]

        paragrafo_patterns = [
            r"^parágrafo\s+único\b",
            r"^parágrafo\b",
        ]

        objeto_patterns = [
            r"^objeto\b",
        ]

        self.high_level_patterns = (
            clausula_patterns
            + secao_patterns
            + paragrafo_patterns
            + objeto_patterns
        )

        self.high_level_trigger = re.compile(
            "|".join(f"({p})" for p in self.high_level_patterns),
            flags=re.IGNORECASE,
        )

        self.number_dot = re.compile(r"^\d+\.\s+")

    def _clean_lines(self, text: str) -> List[str]:
        return [l.strip() for l in text.split("\n") if l.strip()]

    def _is_high_level(self, line: str) -> bool:
        return bool(self.high_level_trigger.match(line))

    def _is_number_dot(self, line: str) -> bool:
        return bool(self.number_dot.match(line))

    def _detect_number_dot_structure(self, lines: List[str]) -> bool:
        numbers = []
        for line in lines:
            m = self.number_dot.match(line)
            if m:
                n = int(m.group(0).split(".")[0])
                numbers.append(n)

        if len(numbers) < 3:
            return False

        distinct = len(set(numbers)) >= 3
        roughly_increasing = sum(
            1 for i in range(1, len(numbers)) if numbers[i] >= numbers[i - 1]
        ) >= max(1, len(numbers) - 2)

        return distinct and roughly_increasing

    def _should_use_number_dot(self, lines: List[str]) -> bool:
        has_high_level = any(self._is_high_level(l) for l in lines)
        has_number_dot_structure = self._detect_number_dot_structure(lines)

        if has_high_level and not has_number_dot_structure:
            return False

        return has_number_dot_structure

    def chunk(self, text: str) -> List[str]:
        lines = self._clean_lines(text)
        if not lines:
            return []

        use_number_dot = self._should_use_number_dot(lines)

        chunks: List[str] = []
        current: List[str] = []

        def flush_current():
            if not current:
                return

            content = "\n".join(current).strip()
            if content:
                chunks.append(content)

        for line in lines:
            is_high_level = self._is_high_level(line)
            is_number_dot = use_number_dot and self._is_number_dot(line)

            if is_high_level or is_number_dot:
                if current:
                    flush_current()

                    if self.overlap > 0:
                        current = current[-self.overlap:]
                    else:
                        current = []

            current.append(line)

        if current:
            flush_current()

        return chunks
