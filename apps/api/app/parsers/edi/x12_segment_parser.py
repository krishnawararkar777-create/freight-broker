"""
Pure Python X12 structural segment tokenizer and helper utilities.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class X12Segment:
    """Represents a single X12 EDI segment with 1-based element indexing."""
    tag: str
    elements: List[str] = field(default_factory=list)

    def get(self, index: int, default: str = "") -> str:
        """
        Safely retrieve element value at 1-based index (elements[1] = first data element).
        elements[0] is the segment identifier/tag.
        """
        if 0 <= index < len(self.elements):
            val = self.elements[index]
            return val.strip() if val is not None else default
        return default

    def __repr__(self) -> str:
        return f"X12Segment({self.tag}: {'*'.join(self.elements[1:])})"


def detect_delimiters(raw_content: str) -> tuple[str, str]:
    """
    Detect element separator and segment terminator from EDI stream.
    Defaults to element separator '*' and segment terminator '~'.
    """
    element_sep = "*"
    segment_term = "~"

    clean_start = raw_content.strip()
    if clean_start.startswith("ISA") and len(clean_start) >= 106:
        # In standard X12, ISA element delimiter is at index 3
        element_sep = clean_start[3]
        # ISA segment terminator is at index 105
        segment_term = clean_start[105]
    elif "~" in raw_content:
        segment_term = "~"
        if "*" in raw_content:
            element_sep = "*"
    elif "\n" in raw_content:
        segment_term = "\n"
        if "*" in raw_content:
            element_sep = "*"

    return element_sep, segment_term


def tokenize_x12(raw_content: str) -> List[X12Segment]:
    """
    Tokenize raw EDI X12 message text into a list of X12Segment objects.
    Handles various segment delimiters (~, newline, etc.) and element delimiters (*).
    """
    if not raw_content or not raw_content.strip():
        return []

    element_sep, segment_term = detect_delimiters(raw_content)

    # Split by segment terminator
    raw_segments = raw_content.split(segment_term)
    parsed_segments: List[X12Segment] = []

    for raw_seg in raw_segments:
        # Strip extraneous newlines/spaces
        cleaned_seg = raw_seg.strip()
        if not cleaned_seg:
            continue

        # If newline still separates segments (e.g. if ~ was terminator followed by \n)
        lines = [line.strip() for line in cleaned_seg.splitlines() if line.strip()]
        for line in lines:
            elements = [el.strip() for el in line.split(element_sep)]
            if not elements or not elements[0]:
                continue
            tag = elements[0].upper()
            parsed_segments.append(X12Segment(tag=tag, elements=elements))

    return parsed_segments


def find_segments(segments: List[X12Segment], tag: str) -> List[X12Segment]:
    """Return all segments matching the given tag (case-insensitive)."""
    target = tag.strip().upper()
    return [s for s in segments if s.tag == target]


def find_first_segment(segments: List[X12Segment], tag: str) -> Optional[X12Segment]:
    """Return the first segment matching the given tag, or None."""
    target = tag.strip().upper()
    for s in segments:
        if s.tag == target:
            return s
    return None
