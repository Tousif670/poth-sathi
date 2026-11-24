import json
from pathlib import Path
from typing import Literal

from app.models.chat import ChatCard, ChatResponse, ChatSource
from app.models.safety import SafetyRuleItem, SafetyRulesDoc

SAFETY_RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "safety_rules.json"

EXTRA_BANGLISH_SYNONYMS: dict[str, list[str]] = {
    "drowning_rip_current": ["dube jacchi", "dube jachchi", "ডুবে যাচ্ছি"],
    "medical_emergency": ["ambulance", "অ্যাম্বুলেন্স", "হাসপাতাল দরকার"],
    "theft_harassment": ["lost wallet", "মানিব্যাগ হারিয়ে", "ছিনতাই হয়েছে"],
    "lost_person_child": ["haraye geche", "হারিয়ে গেছে"],
    "fire": ["fire service", "ফায়ার সার্ভিস"],
    "other_danger": ["help", "sos", "999", "৯৯৯"],
}

PREWRITTEN_RESPONSES: dict[str, dict[Literal["bn", "en"], str]] = {
    "emergency_drowning": {
        "bn": (
            "🚨 জরুরি সমুদ্র উদ্ধার সতর্কতা! অবিলম্বে জাতীয় জরুরি সেবা ৯৯৯ (TO VERIFY) এ কল করুন এবং নিকটস্থ "
            "লাইফগার্ড বা কোস্ট গার্ডকে জানান। রিপ কারেন্টে পড়লে আতঙ্কিত না হয়ে তীরের সমান্তরালে সাঁতার কাটুন।"
        ),
        "en": (
            "🚨 EMERGENCY SEA RESCUE! Call National Emergency 999 (TO VERIFY) immediately and "
            "alert nearby lifeguards or Coast Guard. Swim parallel to the shore in a rip current."
        ),
    },
    "emergency_medical": {
        "bn": (
            "🚨 জরুরি চিকিৎসা সহায়তা! অবিলম্বে ৯৯৯ (TO VERIFY) এ কল করুন অথবা রোগীকে নিকটস্থ কক্সবাজার জেলা "
            "সদর হাসপাতালে নিয়ে যান। এটি কেবল ভ্রমণ নির্দেশিকা, চিকিৎসকের পরামর্শ নয়।"
        ),
        "en": (
            "🚨 MEDICAL EMERGENCY! Call 999 (TO VERIFY) immediately or proceed to Cox's Bazar "
            "District Sadar Hospital. This is travel guidance only, not medical advice."
        ),
    },
    "emergency_theft": {
        "bn": (
            "🚨 চুরি বা হয়রানি সহায়তা! অবিলম্বে জাতীয় জরুরি সেবা ৯৯৯ বা ট্যুরিস্ট পুলিশ কক্সবাজার (TO VERIFY) এ "
            "যোগাযোগ করুন এবং নিকটস্থ ট্যুরিস্ট পুলিশ ফাঁড়িতে অভিযোগ জানান।"
        ),
        "en": (
            "🚨 THEFT / HARASSMENT ALERT! Call National Emergency 999 or Tourist Police "
            "(TO VERIFY) immediately and report to the nearest Tourist Police outpost."
        ),
    },
    "emergency_lost": {
        "bn": (
            "⚠️ হারানো ব্যক্তি বা বস্তু সহায়তা! অবিলম্বে নিকটস্থ ট্যুরিস্ট পুলিশ ফাঁড়ি (লাবণী/সুগন্ধা/কলাতলী) এবং "
            "৯৯৯ (TO VERIFY) এ যোগাযোগ করুন।"
        ),
        "en": (
            "⚠️ MISSING PERSON / LOST ITEM! Contact the nearest Tourist Police outpost "
            "(Laboni/Sugandha/Kolatoli) and call 999 (TO VERIFY) immediately."
        ),
    },
    "emergency_fire": {
        "bn": (
            "🚨 অগ্নি দুর্ঘটনা সতর্কতা! অবিলম্বে ৯৯৯ বা ফায়ার সার্ভিস ১৯৯ (TO VERIFY) এ কল করুন এবং নিরাপদ খোলা "
            "স্থানে সরে যান।"
        ),
        "en": (
            "🚨 FIRE EMERGENCY! Call 999 or Fire Service 199 (TO VERIFY) immediately and evacuate "
            "to an open assembly area."
        ),
    },
    "emergency_other": {
        "bn": (
            "🚨 জরুরি সহায়তা! অবিলম্বে জাতীয় জরুরি সেবা ৯৯৯ (TO VERIFY) বা ট্যুরিস্ট পুলিশ কক্সবাজারের সাথে "
            "যোগাযোগ করুন।"
        ),
        "en": (
            "🚨 EMERGENCY ASSISTANCE! Call National Emergency 999 (TO VERIFY) or contact Tourist "
            "Police Cox's Bazar immediately."
        ),
    },
}


class SafetyRuleEngine:
    """Pre-LLM zero-latency emergency keyword matcher (bn, en, Banglish; docs/ai-spec.md §4)."""

    def __init__(self, rules_path: Path = SAFETY_RULES_PATH) -> None:
        self._rules = self._load_rules(rules_path)

    @staticmethod
    def _load_rules(path: Path) -> list[SafetyRuleItem]:
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        doc = SafetyRulesDoc.model_validate(raw)
        # Ensure EMERGENCY rules are checked before URGENT rules
        return sorted(doc.rules, key=lambda r: 0 if r.action == "EMERGENCY" else 1)

    def evaluate(
        self,
        user_message: str,
        lang: Literal["bn", "en"] = "bn",
        session_id: str | None = None,
    ) -> ChatResponse | None:
        lower_msg = user_message.lower()

        for rule in self._rules:
            extra = EXTRA_BANGLISH_SYNONYMS.get(rule.category, [])
            all_keywords = rule.keywords_bn + rule.keywords_en + rule.keywords_banglish + extra
            for kw in all_keywords:
                if kw.lower() in lower_msg:
                    templates = PREWRITTEN_RESPONSES.get(
                        rule.response_key,
                        PREWRITTEN_RESPONSES["emergency_other"],
                    )
                    answer = templates.get(lang, templates["en"])
                    return ChatResponse(
                        answer_text=answer,
                        language=lang,
                        session_id=session_id,
                        cards=[
                            ChatCard(
                                type="place",
                                data={
                                    "name": (
                                        "জাতীয় জরুরি সেবা ৯৯৯ ও ট্যুরিস্ট পুলিশ"
                                        if lang == "bn"
                                        else "National Emergency 999 & Tourist Police"
                                    ),
                                    "category": rule.category,
                                    "phone": "999",
                                    "status": "TO_VERIFY",
                                },
                            )
                        ],
                        sources=[
                            ChatSource(
                                label="Safety Rule Engine (Pre-written emergency directory)",
                                source_id=f"safety_rules/{rule.category}",
                                is_verified=False,
                            )
                        ],
                        severity="error" if rule.action == "EMERGENCY" else "warning",
                        tool_calls_used=[],
                        fallback_used=False,
                        safety_triggered=True,
                        is_ai_resting=False,
                    )

        return None
