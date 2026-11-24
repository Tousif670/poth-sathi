from fastapi.testclient import TestClient

from app.api.v1.nearby import get_nearby_service
from app.api.v1.transport import get_transport_service
from app.core.cache import TTLCache
from app.models.common import BilingualText
from app.models.place import PlaceDoc
from app.models.transport import RouteDoc
from app.services.nearby_service import NearbyService
from app.services.transport_service import TransportService


class FakePlaceRepo:
    def __init__(self, docs: list[PlaceDoc]) -> None:
        self._docs = docs

    def list_all(self) -> list[PlaceDoc]:
        return list(self._docs)


class FakeTransportRepo:
    def __init__(self, docs: list[RouteDoc]) -> None:
        self._docs = docs

    def list_all(self) -> list[RouteDoc]:
        return list(self._docs)


def _sample_places() -> list[PlaceDoc]:
    return [
        PlaceDoc(
            place_id="EXAMPLE_place_near",
            name=BilingualText(bn="EXAMPLE ফার্মেসি", en="EXAMPLE Pharmacy"),
            category="pharmacy",
            lat=21.4180,
            lon=91.9800,
            phone="EXAMPLE_PHONE",
            opening_hours="08:00-23:00",
        ),
        PlaceDoc(
            place_id="EXAMPLE_place_far",
            name=BilingualText(bn="EXAMPLE সদর হাসপাতাল", en="EXAMPLE Sadar Hospital"),
            category="hospital",
            lat=21.4380,
            lon=91.9820,
            phone="EXAMPLE_PHONE",
            opening_hours="24/7",
        ),
    ]


def _sample_routes() -> list[RouteDoc]:
    return [
        RouteDoc(
            route_id="EXAMPLE_route_cng",
            origin=BilingualText(bn="কলাতলী মোড়", en="Kolatoli More"),
            destination=BilingualText(bn="লাবণী পয়েন্ট", en="Laboni Point"),
            vehicle_type="cng_auto",
            fare_basis="per_vehicle",
            fare_min_bdt=120,
            fare_max_bdt=150,
            distance_km=3.5,
            notes=BilingualText(bn="EXAMPLE রিজার্ভ সিএনজি", en="EXAMPLE reserved CNG"),
        ),
        RouteDoc(
            route_id="EXAMPLE_route_tomtom",
            origin=BilingualText(bn="সুগন্ধা পয়েন্ট", en="Sugandha Point"),
            destination=BilingualText(bn="লাবণী পয়েন্ট", en="Laboni Point"),
            vehicle_type="tomtom",
            fare_basis="per_person",
            fare_min_bdt=15,
            fare_max_bdt=20,
            distance_km=1.8,
            notes=BilingualText(bn="EXAMPLE জনপ্রতি টমটম", en="EXAMPLE per person tomtom"),
        ),
    ]


def test_nearby_radius_filtering_and_distance_sort(client: TestClient) -> None:
    fake_service = NearbyService(
        repository=FakePlaceRepo(_sample_places()),  # type: ignore[arg-type]
        cache=TTLCache(),
    )
    client.app.dependency_overrides[get_nearby_service] = lambda: fake_service  # type: ignore[attr-defined]

    try:
        # 1.0 km around Kolatoli (21.4167, 91.9833) includes only EXAMPLE_place_near
        res = client.get("/api/v1/nearby?lat=21.4167&lng=91.9833&radius_km=1.0&lang=en")
        assert res.status_code == 200
        body = res.json()
        assert body["count"] == 1
        assert body["items"][0]["place_id"] == "EXAMPLE_place_near"
        assert body["items"][0]["distance_km"] < 1.0

        # Invalid latitude returns 400 INVALID_COORDINATES
        bad = client.get("/api/v1/nearby?lat=120.0&lng=91.9833")
        assert bad.status_code == 400
        assert bad.json()["error"]["code"] == "INVALID_COORDINATES"
    finally:
        client.app.dependency_overrides.pop(get_nearby_service, None)  # type: ignore[attr-defined]


def test_transport_fare_calculation_per_person_vs_per_vehicle(client: TestClient) -> None:
    fake_service = TransportService(
        repository=FakeTransportRepo(_sample_routes()),  # type: ignore[arg-type]
        cache=TTLCache(),
    )
    client.app.dependency_overrides[get_transport_service] = lambda: fake_service  # type: ignore[attr-defined]

    try:
        # per_person multiplies by passengers (2 * [15..20] = [30..40])
        res_person = client.get(
            "/api/v1/transport/calculate"
            "?origin=sugandha&destination=laboni&mode=tomtom&passengers=2&lang=en"
        )
        assert res_person.status_code == 200
        data_person = res_person.json()
        assert data_person["fare_basis"] == "per_person"
        assert data_person["min_fare_bdt"] == 30
        assert data_person["max_fare_bdt"] == 40

        # per_vehicle does NOT multiply by passengers (3 passengers still [120..150])
        res_vehicle = client.get(
            "/api/v1/transport/calculate"
            "?origin=kolatoli&destination=laboni&mode=cng&passengers=3&lang=en"
        )
        assert res_vehicle.status_code == 200
        data_vehicle = res_vehicle.json()
        assert data_vehicle["fare_basis"] == "per_vehicle"
        assert data_vehicle["min_fare_bdt"] == 120
        assert data_vehicle["max_fare_bdt"] == 150

        # Unknown route returns 400 ROUTE_NOT_FOUND
        missing = client.get("/api/v1/transport/calculate?origin=dhaka&destination=sylhet")
        assert missing.status_code == 400
        assert missing.json()["error"]["code"] == "ROUTE_NOT_FOUND"
    finally:
        client.app.dependency_overrides.pop(get_transport_service, None)  # type: ignore[attr-defined]
