from pydantic import model_validator

from app.models.common import BilingualText, MetadataMixin


class KBChunkDoc(MetadataMixin):
    id: str = ""
    chunk_id: str = ""
    text: BilingualText
    category: str
    source: str = "own_writing"
    embedding: list[float] | None = None
    language: str = "both"

    @model_validator(mode="after")
    def sync_id_and_chunk_id(self) -> "KBChunkDoc":
        if not self.id and self.chunk_id:
            self.id = self.chunk_id
        elif not self.chunk_id and self.id:
            self.chunk_id = self.id
        return self
