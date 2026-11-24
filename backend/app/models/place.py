from typing import Literal

from pydantic import BaseModel, model_validator

from app.models.common import BilingualText, MetadataMixin

PlaceCategory = Literal["hospital", "pharmacy", "atm", "mosque", "police"]
PlaceFilterCategory = Literal["hospital", "pharmacy", "atm", "mosque", "police", "all"]


class PlaceDoc(MetadataMixin):
    id: str = ""
    place_id: str = ""
    name: BilingualText
    category: PlaceCategory
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


class PlaceListItem(MetadataMixin):
    place_id: str
    name: str
    name_bilingual: BilingualText
    category: PlaceCategory
    description: str | None = None
    description_bilingual: BilingualText | None = None
    address: str | None = None
    address_bilingual: BilingualText | None = None
    phone: str | None = None
    opening_hours: str | None = None
    lat: float
    lon: float
    distance_km: float | None = None


class NearbyResponse(BaseModel):
    items: list[PlaceListItem]
    count: int
