from typing import Literal

from pydantic import model_validator

from app.models.common import BilingualText, MetadataMixin


class PlaceDoc(MetadataMixin):
    id: str = ""
    place_id: str = ""
    name: BilingualText
    category: Literal["hospital", "pharmacy", "atm", "mosque", "police"]
    description: BilingualText | None = None
    address: BilingualText | None = None
    phone: str | None = None
    opening_hours: str | None = None
    lat: float
    lon: float
    geohash: str = ""

    @model_validator(mode="after")
    def sync_id_and_place_id(self) -> "PlaceDoc":
        if not self.id and self.place_id:
            self.id = self.place_id
        elif not self.place_id and self.id:
            self.place_id = self.id
        return self
