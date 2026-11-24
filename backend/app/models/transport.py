from typing import Literal

from pydantic import model_validator

from app.models.common import BilingualText, MetadataMixin


class RouteDoc(MetadataMixin):
    id: str = ""
    route_id: str = ""
    origin: BilingualText
    destination: BilingualText
    vehicle_type: str
    fare_basis: Literal["per_vehicle", "per_person"]  # D22
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
