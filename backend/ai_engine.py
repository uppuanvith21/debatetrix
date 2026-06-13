from __future__ import annotations

import datetime as dt
import os
import re
from dataclasses import dataclass

from backend.db import find_evidence_candidates
from backend.fact_check_sources import FactCheckSource, trusted_sources_by_region


@dataclass
class AnalysisResult:
    status: str
    verdict: str
    confidence: int
    summary: str
    evidence_assessment: str
    evidence_count: int
    risk_level: str
    timestamp: str
    claims: list[dict[str, str]]
    sources: list[FactCheckSource]
    evidence_matches: list[dict[str, object]]
    transparency: dict[str, object]


RISK_TERMS = {
    "high": ("breaking", "secret", "shocking", "guaranteed", "cure", "fraud", "fake", "everyone", "never", "always"),
    "medium": ("viral", "reportedly", "sources say", "claimed", "alleged", "leaked", "ban", "boycott"),
}


def get_provider_status() -> dict[str, str]:
    if os.getenv("OPENAI_API_KEY"):
        return {"source": "BYOK: OpenAI", "detail": "OpenAI key detected. Extend ai_engine.py to call your preferred model."}
    if os.getenv("GOOGLE_FACT_CHECK_API_KEY"):
        return {"source": "BYOK: Google Fact Check", "detail": "Fact Check API key detected for future live lookup wiring."}
    if os.getenv("LOCAL_MODEL_ENDPOINT"):
        return {"source": "LOCAL", "detail": "Local model endpoint configured."}
    return {"source": "LOCAL", "detail": "Local rules engine. No private claim text is sent outside this app."}


def _split_claims(text: str) -> list[dict[str, str]]:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
    if not parts:
        parts = [text.strip()]
    claims: list[dict[str, str]] = []
    for part in parts[:6]:
        claim_type = "CLAIM"
        lowered = part.lower()
        if any(word in lowered for word in ("think", "believe", "best", "worst", "better")):
            claim_type = "OPINION"
        if any(word in lowered for word in ("will", "might", "could", "predict")):
            claim_type = "PREDICTION"
        if any(word in lowered for word in ("rumor", "unconfirmed", "heard")):
            claim_type = "RUMOR"
        claims.append({"type": claim_type, "text": part})
    return claims


def _risk_score(text: str) -> tuple[str, int]:
    lowered = text.lower()
    high_hits = sum(1 for term in RISK_TERMS["high"] if term in lowered)
    medium_hits = sum(1 for term in RISK_TERMS["medium"] if term in lowered)
    if high_hits >= 2 or re.search(r"\b100%|\b0%|\ball\b|\bnever\b", lowered):
        return "High", 42
    if high_hits or medium_hits >= 2:
        return "Medium", 58
    return "Low", 70


def analyze_claim(claim: str, context: str = "", region: str = "India", language: str = "English") -> AnalysisResult:
    claims = _split_claims(claim)
    risk_level, confidence = _risk_score(f"{claim} {context}")
    sources = trusted_sources_by_region(region)
    evidence_matches, evidence_message = find_evidence_candidates(f"{claim} {context}", region=region, limit=8)
    evidence_count = len(evidence_matches)
    status = "UNVERIFIED"
    if evidence_count >= 2 and risk_level != "High":
        status = "PARTIALLY VERIFIED"
        confidence = min(86, confidence + 12)
    elif risk_level == "Low":
        status = "PARTIALLY VERIFIED"
    if risk_level == "High":
        status = "DISPUTED"

    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = (
        "Current evidence is insufficient to reach a fully reliable conclusion from local analysis alone. "
        "The claim has been structured, risk-scored, and routed to trusted verification sources."
    )
    if status == "DISPUTED":
        summary = (
            "This claim contains strong virality or absolutist language, so treat it as disputed until primary "
            "records or independent fact-checks confirm it."
        )
    if evidence_matches:
        source_names = ", ".join(sorted({str(item["source_name"]) for item in evidence_matches})[:4])
        summary = (
            f"Debatetrix found {evidence_count} candidate evidence item(s) from stored trusted verification data "
            f"including {source_names}. Review the linked articles before treating the claim as verified."
        )

    evidence_assessment = (
        f"{evidence_message} No fabricated citations were generated. Verify against primary records first, then compare "
        "at least two independent fact-checking or wire-service sources. Treat screenshots, anonymous posts, and edited "
        "videos as low-confidence evidence unless original metadata or source records are available."
    )
    transparency = {
        "Model Used": "Debatetrix local rules engine",
        "Inference Source": get_provider_status()["source"],
        "Verification Status": status,
        "Confidence Score": confidence,
        "Sources Used": [source.name for source in sources[:5]],
        "Evidence Count": evidence_count,
        "Language": language,
        "Region": region,
        "Last Updated": timestamp,
    }
    return AnalysisResult(
        status=status,
        verdict=f"Verification Status: {status}",
        confidence=confidence,
        summary=summary,
        evidence_assessment=evidence_assessment,
        evidence_count=0,
        risk_level=risk_level,
        timestamp=timestamp,
        claims=claims,
        sources=sources[:6],
        evidence_matches=evidence_matches,
        transparency=transparency,
    )


def compare_rivals(side_a: str, side_b: str, topic: str, region: str = "India") -> str:
    side_a = side_a.strip() or "Perspective A"
    side_b = side_b.strip() or "Perspective B"
    topic = topic.strip() or "Neutral comparison"
    sources = trusted_sources_by_region(region)[:5]
    source_lines = "\n".join(f"- {source.name}: {source.url}" for source in sources)
    return f"""
### Topic
{topic}

### Executive Summary
This is a neutral debate brief. It separates claims from evidence and avoids declaring a winner unless verified evidence supports it.

### {side_a}
- Arguments: List measurable achievements, official records, direct statements, and timeline-based evidence.
- Strengths: Use primary statistics, official data, and consistent performance indicators.
- Weaknesses: Flag missing context, selection bias, recency bias, or fan-driven claims.

### {side_b}
- Arguments: Apply the same evidence standard used for {side_a}.
- Strengths: Compare like-for-like metrics and era/context adjustments.
- Weaknesses: Avoid viral narratives unless independently verified.

### Neutral Facts
- Prefer official records, court/government documents, league databases, or direct public statements.
- Treat social media posts as claims until independently confirmed.

### Misinformation Check
Current evidence is insufficient to reach a reliable conclusion unless live sources are consulted.

### Trusted Source Routing
{source_lines}

### Verdict
UNVERIFIED until evidence is collected and cross-checked.

### Confidence Score
45%
"""
