"""Resume metadata and extracted text models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParsedResume:
    filename: str
    file_type: str
    text: str

    def __post_init__(self) -> None:
        if not self.filename or not self.text.strip():
            raise ValueError("A parsed resume requires a filename and non-empty text")
