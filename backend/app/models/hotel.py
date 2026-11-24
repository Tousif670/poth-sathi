from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.common import BilingualText, MetadataMixin

HotelArea = Literal["kolatoli", "sugandha", "laboni"]
HotelSort = Literal["match", "price_asc", "price_desc", "rating"]


class HotelDoc(MetadataMixin):
    id: str = ""
    hotel_id: str = ""
    name: BilingualText
    area: HotelArea
    description: BilingualText | None = None
    price_min_bdt: int | float
    price_max_bdt: int | float
    amenities: list[str] = Field(default_factory=list)
    rating: float | None = 0.0
    address: BilingualText | None = None
    phone: str | None = None
    lat: float
    lon: float
    geohash: str = ""
    image_url: str = ""

    @model_validator(mode="after")
    def sync_id_and_hotel_id(self) -> "HotelDoc":
        if not self.id and self.hotel_id:
            self.id = self.hotel_id
        elif not self.hotel_id and self.id:
            self.hotel_id = self.id
        return self


class HotelListItem(MetadataMixin):
    hotel_id: str
    name: str
    name_bilingual: BilingualText
    area: HotelArea
    description: str | None = None
    description_bilingual: BilingualText | None = None
    address: str | None = None
    address_bilingual: BilingualText | None = None
    price_min_bdt: int | float
    price_max_bdt: int | float
    amenities: list[str] = Field(default_factory=list)
    rating: float
    phone: str | None = None
    lat: float
    lon: float
    image_url: str = ""
    match_score: float = 1.0


class HotelListResponse(BaseModel):
    items: list[HotelListItem]
    total: int
    limit: int
    offset: int
