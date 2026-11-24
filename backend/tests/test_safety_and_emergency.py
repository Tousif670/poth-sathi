from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.v1.emergency import get_emergency_service
from app.api.v1.safety import get_safety_service
from app.core.cache import TTLCache
from app.models.common import BilingualText
from app.models.kb import KBChunkDoc
from app.models.safety import BeachStatusDoc, SOSEventDoc
from app.services.emergency_service import EmergencyService
from app.services.safety_service import SafetyService, is_beach_status_outdated


class FakeSafetyRepo:
    def __init__(self, zones: list[BeachStatusDoc]) -> None:
        self._zones = zones
        self.logged_sos: list[SOSEventDoc] = []

    def list_beach_status(self) -> list[BeachStatusDoc]:
        return list(self._zones)

    def create_sos_event(
        self,
        trigger_type: str,
        lat: float | None = None,
        lng: float | None = None,
        uid: str | None = None,
    ) -> SOSEventDoc:
        event = SOSEventDoc(
            sos_id="EXAMPLE_sos_101",
            uid=uid,
            trigger_type=trigger_type,  # type: ignore[arg-type]
            lat=lat,
            lng=lng,
            created_at=datetime.now(UTC),
        )
        self.logged_sos.append(event)
        return event


class FakeKBRepo:
    def list_all(self) -> list[KBChunkDoc]:
        return [
            KBChunkDoc(
                chunk_id="EXAMPLE_kb_001",
                category="beach_safety",
                text=BilingualText(bn="লাল পতাকা মানে বিপদ।", en="Red flag means danger."),
            )
        ]


def test_is_beach_status_outdated_threshold_6_hours() -> None:
    now = datetime(2026, 11, 24, 15, 0, 0, tzinfo=UTC)
    fresh_iso = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    stale_iso = (now - timedelta(hours=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    assert is_beach_status_outdated(fresh_iso, now=now) is False
    assert is_beach_status_outdated(stale_iso, now=now) is True


def test_beach_status_multi_zone_and_sos_endpoint(client: TestClient) -> None:
    now = datetime.now(UTC)
    fresh_ts = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    stale_ts = (now - timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%SZ")

    zones = [
        BeachStatusDoc(
            zone_id="kolatoli",
            zone_name=BilingualText(bn="কলাতলী সৈকত", en="Kolatoli Beach"),
            flag_colour="yellow",
            note=BilingualText(bn="মাঝারি ঢেউ", en="Moderate waves"),
            last_updated=fresh_ts,
        ),
        BeachStatusDoc(
            zone_id="sugandha",
            zone_name=BilingualText(bn="সুগন্ধা সৈকত", en="Sugandha Beach"),
            flag_colour="green",
            note=BilingualText(bn="নিরাপদ", en="Safe"),
            last_updated=stale_ts,
        ),
        BeachStatusDoc(
            zone_id="laboni",
            zone_name=BilingualText(bn="লাবণী সৈকত", en="Laboni Beach"),
            flag_colour="red",
            note=BilingualText(bn="উচ্চ বিপদ", en="High hazard"),
            last_updated=fresh_ts,
        ),
    ]

    fake_safety_repo = FakeSafetyRepo(zones)
    fake_safety_service = SafetyService(
        safety_repository=fake_safety_repo,  # type: ignore[arg-type]
        kb_repository=FakeKBRepo(),  # type: ignore[arg-type]
        cache=TTLCache(),
    )
    fake_emergency_service = EmergencyService(
        safety_repository=fake_safety_repo  # type: ignore[arg-type]
    )

    client.app.dependency_overrides[get_safety_service] = lambda: fake_safety_service  # type: ignore[attr-defined]
    client.app.dependency_overrides[get_emergency_service] = lambda: fake_emergency_service  # type: ignore[attr-defined]

    try:
        # 1. All 3 zones returned when zone_id omitted (D23)
        res_all = client.get("/api/v1/safety/beach-status?lang=en")
        assert res_all.status_code == 200
        zones_out = res_all.json()["zones"]
        assert len(zones_out) == 3
        assert zones_out[0]["zone_id"] == "kolatoli"
        assert zones_out[0]["is_outdated"] is False
        assert zones_out[1]["zone_id"] == "sugandha"
        assert zones_out[1]["is_outdated"] is True  # >6h old per D24

        # 2. Single zone filter
        res_one = client.get("/api/v1/safety/beach-status?zone_id=laboni&lang=bn")
        assert res_one.status_code == 200
        assert len(res_one.json()["zones"]) == 1
        assert res_one.json()["zones"][0]["flag"] == "red"

        # 3. Advisories
        adv_res = client.get("/api/v1/safety/advisories?lang=en")
        assert adv_res.status_code == 200
        assert adv_res.json()["count"] == 1

        # 4. Emergency contacts
        contacts_res = client.get("/api/v1/emergency/contacts?lang=en")
        assert contacts_res.status_code == 200
        assert contacts_res.json()["count"] >= 1
        assert contacts_res.json()["items"][0]["number"] == "999"

        # 5. SOS trigger -> 201 Created
        sos_res = client.post(
            "/api/v1/emergency/sos",
            json={"trigger_type": "button", "lat": 21.4167, "lng": 91.9833, "lang": "en"},
        )
        assert sos_res.status_code == 201
        sos_data = sos_res.json()
        assert sos_data["sos_id"] == "EXAMPLE_sos_101"
        assert sos_data["national_emergency"] == "999"
        assert len(fake_safety_repo.logged_sos) == 1
    finally:
        client.app.dependency_overrides.pop(get_safety_service, None)  # type: ignore[attr-defined]
        client.app.dependency_overrides.pop(get_emergency_service, None)  # type: ignore[attr-defined]
