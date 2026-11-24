from typing import Literal

from pydantic import Field, model_validator

from app.models.common import BilingualText, MetadataMixin


class HotelDoc(MetadataMixin):
    id: str = ""
    hotel_id: str = ""
    name: BilingualText
    area: Literal["kolatoli", "sugandha", "laboni"]
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
