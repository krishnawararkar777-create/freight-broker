from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field

class BoundingBox(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    page_number: int = 1
    x_min: float = 0.0
    y_min: float = 0.0
    x_max: float = 0.0
    y_max: float = 0.0

class ExtractedField(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    field_name: str
    value_json: Optional[Dict[str, Any]] = None
    source_text: Optional[str] = None
    page_number: int = 1
    bbox: Optional[BoundingBox] = None
    confidence: float = 1.0
    extraction_method: str = "LocalPdfParser"

class ExtractionResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    document_type: str
    filename: str
    parser_version: str = "v1.0"
    status: str = "processed"
    raw_text: Optional[str] = None
    fields: List[ExtractedField] = Field(default_factory=list)
