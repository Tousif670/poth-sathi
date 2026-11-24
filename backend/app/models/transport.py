from typing import Literal

from pydantic import BaseModel, model_validator

from app.models.common import BilingualText, MetadataMixin

FareBasis = Literal["per_vehicle", "per_person"]


class RouteDoc(MetadataMixin):
    id: str = ""
    route_id: str = ""
    origin: BilingualText
    destination: BilingualText
    vehicle_type: str
    fare_basis: FareBasis  # D22
    fare_min_bdt: int | float
    fare_max_bdt: int | float
    distance_km: float | None = None
    notes: BilingualText | None = None

    @model_validator(mode="after")
    def sync_id_and_route_id(self) -> "RouteDoc":
        if not self.id and self.route_id:
            self.id = self.route_id
        elif not self.route_id and self.id:
            self.route_id = self.id
        return self


class FareRouteItem(MetadataMixin):
    route_id: str
    origin: str
    origin_bilingual: BilingualText
    destination: str
    destination_bilingual: BilingualText
    vehicle_type: str
    fare_basis: FareBasis
    fare_min_bdt: int | float
    fare_max_bdt: int | float
    distance_km: float | None = None
    notes: str | None = None
    notes_bilingual: BilingualText | None = None


class FareRouteListResponse(BaseModel):
    items: list[FareRouteItem]
    count: int


class FareCalculationResponse(MetadataMixin):
    origin: str
    destination: str
    mode: str
    passengers: int
    fare_basis: FareBasis
    min_fare_bdt: int | float
    max_fare_bdt: int | float
    estimated_time_min: int
    distance_km: float
    route_id: str
    notes: str | None = None
