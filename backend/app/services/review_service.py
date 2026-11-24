import json
import re
from pathlib import Path
from typing import Literal

from app.models.review import (
    AspectScore,
    PaginatedReviewsResponse,
    ReviewCreateRequest,
    ReviewDoc,
    SentimentPolarity,
    SentimentResult,
)
from app.repositories.review_repository import ReviewRepository

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LEXICON_EN_PATH = DATA_DIR / "lexicon_en.json"
LEXICON_BN_PATH = DATA_DIR / "lexicon_bn.json"

NEGATION_WORDS: dict[str, set[str]] = {
    "en": {"not", "no", "never", "don't", "doesn't", "wasn't", "isn't", "weren't"},
    "bn": {"না", "নয়", "নেই", "নি"},
}

ASPECT_KEYWORDS: dict[str, list[str]] = {
    "Food": ["food", "breakfast", "meal", "restaurant", "eat", "খাবার", "নাস্তা", "রেস্তোরাঁ"],
    "Cleanliness": [
        "clean",
        "dirty",
        "hygiene",
        "tidy",
        "wash",
        "smelly",
        "পরিষ্কার",
        "নোংরা",
        "গন্ধ",
        "স্বাস্থ্যকর",
    ],
    "Location": ["location", "near", "far", "beach", "view", "walk", "অবস্থান", "কাছে", "দূরে", "বীচ"],
    "Service": [
        "staff",
        "service",
        "helpful",
        "friendly",
        "rude",
        "slow",
        "delayed",
        "সেবা",
        "স্টাফ",
        "সহায়ক",
        "ধীর",
    ],
    "Price": [
        "price",
        "cheap",
        "expensive",
        "value",
        "cost",
        "affordable",
        "দাম",
        "সস্তা",
        "দামি",
        "সাশ্রয়ী",
    ],
}


def _load_lexicon(lang: Literal["bn", "en"]) -> dict[str, set[str]]:
    path = LEXICON_BN_PATH if lang == "bn" else LEXICON_EN_PATH
    if not path.exists():
        return {"positive": set(), "negative": set()}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        "positive": {w.lower() for w in raw.get("positive", [])},
        "negative": {w.lower() for w in raw.get("negative", [])},
    }


def _detect_aspect_in_context(tokens: list[str], idx: int) -> str | None:
    window = tokens[max(0, idx - 3) : min(len(tokens), idx + 4)]
    for aspect, kw_list in ASPECT_KEYWORDS.items():
        if any(w in kw_list for w in window):
            return aspect
    return None


def analyze_review_sentiment(text: str, lang: Literal["bn", "en"] | None = None) -> SentimentResult:
    """Rule-based lexicon sentiment analyzer with negation handling (docs/ai-spec.md §9)."""
    detected_lang: Literal["bn", "en"] = lang or (
        "bn" if any("\u0980" <= ch <= "\u09ff" for ch in text) else "en"
    )
    lex_en = _load_lexicon("en")
    lex_bn = _load_lexicon("bn")
    pos_words = lex_en["positive"] | lex_bn["positive"]
    neg_words = lex_en["negative"] | lex_bn["negative"]
    negations = NEGATION_WORDS["en"] | NEGATION_WORDS["bn"]

    tokens = [t for t in re.split(r"[\s,।?!.;:()\"']+", text.lower()) if t]
    aspect_counts: dict[str, dict[str, int]] = {
        aspect: {"positive": 0, "negative": 0} for aspect in ASPECT_KEYWORDS
    }

    overall_pos = 0
    overall_neg = 0
    negated = False

    for i, word in enumerate(tokens):
        if word in negations:
            negated = True
            continue

        polarity: SentimentPolarity | None = None
        if word in pos_words:
            polarity = "negative" if negated else "positive"
        elif word in neg_words:
            polarity = "positive" if negated else "negative"

        if polarity is not None:
            # Handle Bengali post-position negation (e.g., "পরিষ্কার না")
            if not negated and i + 1 < len(tokens) and tokens[i + 1] in NEGATION_WORDS["bn"]:
                polarity = "negative" if polarity == "positive" else "positive"

            aspect = _detect_aspect_in_context(tokens, i)
            if aspect:
                aspect_counts[aspect][polarity] += 1

            if polarity == "positive":
                overall_pos += 1
            else:
                overall_neg += 1
            negated = False

    if overall_pos > overall_neg:
        overall: SentimentPolarity = "positive"
    elif overall_neg > overall_pos:
        overall = "negative"
    else:
        overall = "neutral"

    confidence = round(abs(overall_pos - overall_neg) / max(overall_pos + overall_neg, 1), 2)

    aspects_out: dict[str, AspectScore] = {}
    for aspect, counts in aspect_counts.items():
        p_cnt = counts["positive"]
        n_cnt = counts["negative"]
        asp_pol: SentimentPolarity = (
            "positive" if p_cnt > n_cnt else "negative" if n_cnt > p_cnt else "neutral"
        )
        aspects_out[aspect] = AspectScore(sentiment=asp_pol, positive=p_cnt, negative=n_cnt)

    _ = detected_lang
    return SentimentResult(overall=overall, confidence=confidence, aspects=aspects_out)


class ReviewService:
    """Service layer for hotel reviews and lexicon-based sentiment analysis (P1)."""

    def __init__(self, repository: ReviewRepository | None = None) -> None:
        self._repo = repository if repository is not None else ReviewRepository()

    def create_review(
        self,
        hotel_id: str,
        uid: str,
        payload: ReviewCreateRequest,
    ) -> ReviewDoc:
        sentiment = analyze_review_sentiment(payload.comment, payload.lang)
        return self._repo.create(
            hotel_id=hotel_id,
            uid=uid,
            rating=payload.rating,
            comment=payload.comment,
            sentiment=sentiment,
        )

    def list_reviews(
        self,
        hotel_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> PaginatedReviewsResponse:
        all_revs = self._repo.list_by_hotel(hotel_id)
        return PaginatedReviewsResponse(
            items=all_revs[offset : offset + limit],
            total=len(all_revs),
            limit=limit,
            offset=offset,
        )
