from datetime import datetime

from pydantic import BaseModel


class IndexSourceResponse(BaseModel):
    source_id: int
    chunk_count: int
    collection: str
    indexed_at: datetime

