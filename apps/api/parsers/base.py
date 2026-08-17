from abc import ABC, abstractmethod
from schemas.extraction import ExtractionResult

class BaseDocumentParser(ABC):
    """Abstract interface for all document parsers (local/rule-based and VLM/LLM)."""

    @abstractmethod
    def parse(self, file_bytes: bytes, filename: str, document_type: str) -> ExtractionResult:
        """
        Parses document binary and returns a Pydantic-validated ExtractionResult
        with per-field confidence and provenance location.
        """
        pass
