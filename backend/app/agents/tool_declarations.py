from typing import Any

TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "search_hotels",
        "description": (
            "Search the verified Cox's Bazar hotel database. Filter by area, max_price_bdt, "
            "and amenities. Returns hotel cards with names, prices, ratings, and locations."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "area": {
                    "type": "STRING",
                    "enum": ["kolatoli", "sugandha", "laboni"],
                    "description": "Beach zone area",
                },
                "max_price_bdt": {
                    "type": "INTEGER",
                    "description": "Maximum nightly tariff budget in BDT (D27)",
                },
                "amenities": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Required amenities such as ['wifi', 'pool', 'ac']",
                },
            },
        },
    },
    {
        "name": "find_nearby",
        "description": (
            "Find nearby essential places in Cox's Bazar by category (hospital, pharmacy, "
            "atm, mosque, police)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "enum": ["hospital", "pharmacy", "atm", "mosque", "police"],
                    "description": "Essential place category",
                },
                "latitude": {"type": "NUMBER", "description": "Optional user latitude"},
                "longitude": {"type": "NUMBER", "description": "Optional user longitude"},
                "limit": {"type": "INTEGER", "description": "Max results (default 5)"},
            },
            "required": ["category"],
        },
    },
    {
        "name": "calculate_fare",
        "description": (
            "Calculate estimated local transport fare between origin and destination in "
            "Cox's Bazar (D22)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "origin": {"type": "STRING", "description": "Starting location"},
                "destination": {"type": "STRING", "description": "Destination location"},
                "mode": {
                    "type": "STRING",
                    "description": "Optional vehicle mode (cng, tomtom, rickshaw)",
                },
                "passengers": {
                    "type": "INTEGER",
                    "description": "Optional passenger count (multiplies fare when per_person)",
                },
            },
            "required": ["origin", "destination"],
        },
    },
    {
        "name": "get_beach_status",
        "description": (
            "Get current beach safety flag status across Cox's Bazar zones (kolatoli, "
            "sugandha, laboni; D23)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "zone": {
                    "type": "STRING",
                    "enum": ["kolatoli", "sugandha", "laboni"],
                    "description": "Optional beach zone; returns all 3 zones if omitted.",
                }
            },
        },
    },
    {
        "name": "search_knowledge",
        "description": (
            "Search the curated Cox's Bazar knowledge base for safety tips, cultural "
            "etiquette, food guide, and transport advice."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Search query in Bengali or English",
                }
            },
            "required": ["query"],
        },
    },
]
