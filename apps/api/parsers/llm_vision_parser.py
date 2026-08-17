from parsers.base import BaseDocumentParser
from parsers.local_parser import LocalPdfParser
from schemas.extraction import ExtractionResult

class LlmVisionParser(BaseDocumentParser):
    """
    Swappable VLM (Vision Language Model) implementation behind the exact same interface.
    Falls back to LocalPdfParser if no LLM API key is configured.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._fallback_parser = LocalPdfParser()

    def parse(self, file_bytes: bytes, filename: str, document_type: str) -> ExtractionResult:
        if not self.api_key:
            # Fallback to local parser if API key is not configured
            res = self._fallback_parser.parse(file_bytes, filename, document_type)
            res.parser_version = "vlm-stub-fallback-v1.0"
            return res

        # Placeholder for VLM API call (e.g. Gemini / VLM Vision API)
        return self._fallback_parser.parse(file_bytes, filename, document_type)
