import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

import requests


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


def tokenize_search_query(query: str) -> list[str]:
    return sorted({token.lower() for token in TOKEN_PATTERN.findall(query or "") if len(token) > 1})


def _count_term_matches(text: str, term: str) -> int:
    return len(re.findall(rf"\b{re.escape(term)}\b", text.lower()))


def _normalize_reviews(reviews: Iterable[dict]) -> str:
    return " ".join((review.get("text") or "") for review in reviews)


def _score_candidate(query_terms: list[str], name: str, types: list[str], reviews: list[dict]) -> tuple[int, int, set[str]]:
    normalized_name = (name or "").lower()
    normalized_types = " ".join(types or []).lower()
    review_text = _normalize_reviews(reviews).lower()

    review_score = 0
    name_score = 0
    matched_terms: set[str] = set()

    for term in query_terms:
        review_hits = _count_term_matches(review_text, term)
        name_hits = _count_term_matches(normalized_name, term) + _count_term_matches(normalized_types, term)
        review_score += review_hits
        name_score += name_hits
        if review_hits > 0 or name_hits > 0:
            matched_terms.add(term)

    return review_score, name_score, matched_terms


def rank_and_filter_restaurants(candidates: list[dict], query: str, required_terms: list[str] | None = None) -> tuple[list[dict], list[dict]]:
    query_terms = tokenize_search_query(query)
    required = {term.lower() for term in (required_terms or [])}
    ranked: list[dict] = []

    for candidate in candidates:
        reviews = candidate.get("reviews", [])
        review_score, name_score, matched_terms = _score_candidate(
            query_terms=query_terms,
            name=candidate.get("name", ""),
            types=candidate.get("types", []),
            reviews=reviews,
        )
        has_reviews = bool(_normalize_reviews(reviews).strip())
        include = (review_score > 0) or (name_score > 0 and not has_reviews)
        if required and not required.issubset(matched_terms):
            include = False

        if include:
            rating = float(candidate.get("rating") or 0)
            total_score = (review_score * 3) + name_score + (rating / 10)
            ranked.append(
                {
                    **candidate,
                    "review_match_score": review_score,
                    "name_match_score": name_score,
                    "total_score": total_score,
                    "matched_terms": sorted(matched_terms),
                }
            )

    ranked.sort(
        key=lambda item: (
            item["total_score"],
            float(item.get("rating") or 0),
            int(item.get("user_ratings_total") or 0),
            item.get("name", "").lower(),
        ),
        reverse=True,
    )

    filter_counts = Counter(term for restaurant in ranked for term in restaurant["matched_terms"])
    filter_list = [{"term": term, "count": count} for term, count in filter_counts.most_common()]
    return ranked, filter_list


@dataclass
class GooglePlacesClient:
    api_key: str

    @classmethod
    def from_env(cls) -> "GooglePlacesClient":
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is required")
        return cls(api_key=api_key)

    def _get(self, endpoint: str, params: dict) -> dict:
        params = {**params, "key": self.api_key}
        response = requests.get(endpoint, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
        status = payload.get("status", "")
        if status and status not in {"OK", "ZERO_RESULTS"}:
            raise RuntimeError(payload.get("error_message") or f"Google Maps API returned {status}")
        return payload

    def search_restaurants(self, query: str, location: str | None = None, max_results: int = 20) -> list[dict]:
        text_query = f"{query} restaurant"
        if location:
            text_query = f"{text_query} in {location}"

        search_payload = self._get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            {"query": text_query},
        )
        results = search_payload.get("results", [])[:max_results]

        restaurants: list[dict] = []
        for result in results:
            place_id = result.get("place_id")
            if not place_id:
                continue
            details_payload = self._get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                {
                    "place_id": place_id,
                    "fields": ",".join(
                        [
                            "place_id",
                            "name",
                            "formatted_address",
                            "rating",
                            "user_ratings_total",
                            "url",
                            "website",
                            "types",
                            "reviews",
                        ]
                    ),
                },
            )
            details = details_payload.get("result", {})
            restaurants.append(
                {
                    "place_id": details.get("place_id"),
                    "name": details.get("name", result.get("name", "")),
                    "formatted_address": details.get("formatted_address", result.get("formatted_address", "")),
                    "rating": details.get("rating", result.get("rating")),
                    "user_ratings_total": details.get("user_ratings_total", result.get("user_ratings_total")),
                    "url": details.get("url"),
                    "website": details.get("website"),
                    "types": details.get("types", result.get("types", [])),
                    "reviews": details.get("reviews", []),
                }
            )
        return restaurants
