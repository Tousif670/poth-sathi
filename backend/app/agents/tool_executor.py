from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.llm_client import LLMToolCall
from app.models.chat import ChatCard, ChatSource
from app.services.hotel_service import HotelService
from app.services.nearby_service import NearbyService
from app.services.safety_service import SafetyService
from app.services.transport_service import RouteNotFoundError, TransportService


@dataclass
class ToolExecutionResult:
    cards: list[ChatCard] = field(default_factory=list)
    sources: list[ChatSource] = field(default_factory=list)
    summary_lines: list[str] = field(default_factory=list)
    tool_names: list[str] = field(default_factory=list)


class ToolExecutor:
    """Dispatches Gemini function-calling tool requests to Services (docs/ai-spec.md §5)."""

    def __init__(
        self,
        hotel_service: HotelService | None = None,
        nearby_service: NearbyService | None = None,
        transport_service: TransportService | None = None,
        safety_service: SafetyService | None = None,
        rag_service: Any | None = None,
    ) -> None:
        self._hotels = hotel_service if hotel_service is not None else HotelService()
        self._nearby = nearby_service if nearby_service is not None else NearbyService()
        self._transport = (
            transport_service if transport_service is not None else TransportService()
        )
        self._safety = safety_service if safety_service is not None else SafetyService()
        self._rag = rag_service

    def execute_all(
        self,
        tool_calls: list[LLMToolCall],
        lang: Literal["bn", "en"] = "bn",
    ) -> ToolExecutionResult:
        out = ToolExecutionResult()

        for tc in tool_calls:
            out.tool_names.append(tc.name)
            args = tc.args or {}

            if tc.name == "search_hotels":
                area = args.get("area")
                if area not in ("kolatoli", "sugandha", "laboni"):
                    area = None
                max_price = args.get("max_price_bdt")
                max_price_val = float(max_price) if isinstance(max_price, (int, float)) else None
                raw_amenities = args.get("amenities")
                amenities = (
                    [str(a) for a in raw_amenities] if isinstance(raw_amenities, list) else []
                )

                res = self._hotels.search_hotels(
                    area=area,  # type: ignore[arg-type]
                    max_price_bdt=max_price_val,
                    amenities=amenities,
                    lang=lang,
                    limit=5,
                )
                for h in res.items:
                    out.cards.append(
                        ChatCard(
                            type="hotel",
                            data={
                                "hotel_id": h.hotel_id,
                                "name": h.name,
                                "area": h.area,
                                "price_min_bdt": h.price_min_bdt,
                                "price_max_bdt": h.price_max_bdt,
                                "amenities": h.amenities,
                                "rating": h.rating,
                                "match_score": h.match_score,
                                "is_verified": h.is_verified,
                            },
                        )
                    )
                    out.sources.append(
                        ChatSource(
                            label="Verified hotel data" if h.is_verified else "Sample hotel data",
                            source_id=f"hotels/{h.hotel_id}",
                            is_verified=h.is_verified,
                        )
                    )
                    out.summary_lines.append(
                        f"{h.name} ({h.area}): ৳{h.price_min_bdt}–৳{h.price_max_bdt}"
                    )

            elif tc.name == "find_nearby":
                category = str(args.get("category", "all"))
                if category not in ("hospital", "pharmacy", "atm", "mosque", "police", "all"):
                    category = "all"
                lat = args.get("latitude")
                lng = args.get("longitude")
                lat_val = float(lat) if isinstance(lat, (int, float)) else None
                lng_val = float(lng) if isinstance(lng, (int, float)) else None
                limit = int(args.get("limit", 5))

                res = self._nearby.find_nearby(
                    category=category,  # type: ignore[arg-type]
                    lat=lat_val,
                    lng=lng_val,
                    lang=lang,
                    limit=max(1, min(limit, 10)),
                )
                for p in res.items:
                    out.cards.append(
                        ChatCard(
                            type="place",
                            data={
                                "place_id": p.place_id,
                                "name": p.name,
                                "category": p.category,
                                "address": p.address,
                                "phone": p.phone,
                                "distance_km": p.distance_km,
                                "is_verified": p.is_verified,
                            },
                        )
                    )
                    out.sources.append(
                        ChatSource(
                            label="Verified places data" if p.is_verified else "Sample place data",
                            source_id=f"places/{p.place_id}",
                            is_verified=p.is_verified,
                        )
                    )
                    out.summary_lines.append(f"{p.name} ({p.category}) - {p.phone}")

            elif tc.name == "calculate_fare":
                origin = str(args.get("origin", "kolatoli"))
                destination = str(args.get("destination", "laboni"))
                mode = str(args["mode"]) if args.get("mode") else None
                passengers = int(args.get("passengers", 1))
                try:
                    calc = self._transport.calculate_fare(
                        origin=origin,
                        destination=destination,
                        mode=mode,
                        passengers=max(1, passengers),
                        lang=lang,
                    )
                    out.cards.append(
                        ChatCard(
                            type="fare",
                            data={
                                "route_id": calc.route_id,
                                "origin": calc.origin,
                                "destination": calc.destination,
                                "mode": calc.mode,
                                "fare_basis": calc.fare_basis,
                                "passengers": calc.passengers,
                                "min_fare_bdt": calc.min_fare_bdt,
                                "max_fare_bdt": calc.max_fare_bdt,
                                "is_verified": calc.is_verified,
                            },
                        )
                    )
                    out.sources.append(
                        ChatSource(
                            label="Transport fare database",
                            source_id=f"transport_routes/{calc.route_id}",
                            is_verified=calc.is_verified,
                        )
                    )
                    out.summary_lines.append(
                        f"{calc.origin} → {calc.destination} ({calc.mode}): "
                        f"৳{calc.min_fare_bdt}–৳{calc.max_fare_bdt} ({calc.fare_basis})"
                    )
                except RouteNotFoundError:
                    pass

            elif tc.name == "get_beach_status":
                zone = args.get("zone")
                if zone not in ("kolatoli", "sugandha", "laboni"):
                    zone = None
                res = self._safety.get_beach_status(
                    zone_id=zone,  # type: ignore[arg-type]
                    lang=lang,
                )
                for z in res.zones:
                    out.cards.append(
                        ChatCard(
                            type="beach_status",
                            data={
                                "zone_id": z.zone_id,
                                "zone_name": z.zone_name,
                                "flag": z.flag,
                                "flag_meaning": z.flag_meaning,
                                "last_updated": z.last_updated,
                                "is_outdated": z.is_outdated,
                            },
                        )
                    )
                    out.sources.append(
                        ChatSource(
                            label="Beach safety status",
                            source_id=f"beach_status/{z.zone_id}",
                            is_verified=z.is_verified,
                        )
                    )
                    out.summary_lines.append(
                        f"{z.zone_name}: {z.flag.upper()} ({z.flag_meaning})"
                    )

            elif tc.name == "search_knowledge" and self._rag is not None:
                query = str(args.get("query", ""))
                chunks = self._rag.search(query=query, lang=lang, top_k=3)
                for ch in chunks:
                    out.sources.append(
                        ChatSource(
                            label=f"Knowledge Base ({ch.category})",
                            source_id=f"kb_chunks/{ch.chunk_id}",
                            is_verified=ch.is_verified,
                        )
                    )
                    out.summary_lines.append(ch.text)

        return out
