from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


class AiResponseValidationError(ValueError):
    pass


_FORBIDDEN_CLAIMS = [
    "publication readiness passed",
    "publication ready",
    "certified",
    "scientifically verified",
    "score is now",
    "replacement score",
    "deterministic score changed",
]


@dataclass(frozen=True)
class AiAnalysis:
    summary: str
    key_findings: list[str]
    limitations: list[str]
    suggested_next_steps: list[str]
    model_name: str
    provider: str
    generated_at: str
    input_summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL)
    return match.group(1).strip() if match else stripped


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AiResponseValidationError("AI response contains duplicate keys.")
        result[key] = value
    return result


def _load_object(raw: str) -> dict[str, Any]:
    if not raw.strip():
        raise AiResponseValidationError("AI response was empty.")
    try:
        payload = json.loads(
            _strip_markdown_fence(raw),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                AiResponseValidationError(f"AI response used invalid number {value}.")
            ),
        )
    except AiResponseValidationError:
        raise
    except Exception as exc:
        raise AiResponseValidationError("AI response was not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise AiResponseValidationError("AI response must be a JSON object.")
    return payload


def _string(payload: dict[str, Any], key: str, max_len: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AiResponseValidationError(f"AI response field {key} must be a string.")
    value = value.strip()
    if len(value) > max_len:
        raise AiResponseValidationError(f"AI response field {key} is too long.")
    return value


def _string_list(
    payload: dict[str, Any], key: str, max_items: int = 8, max_len: int = 500
) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise AiResponseValidationError(f"AI response field {key} must be a list.")
    if len(value) > max_items:
        raise AiResponseValidationError(f"AI response field {key} has too many items.")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise AiResponseValidationError(f"AI response field {key} must contain strings.")
        item = item.strip()
        if item and len(item) <= max_len:
            items.append(item)
        elif len(item) > max_len:
            raise AiResponseValidationError(f"AI response field {key} contains an overlong item.")
    return items


def _all_text(values: list[str]) -> str:
    return "\n".join(values).lower()


def _validate_consistency(
    payload: dict[str, Any],
    report_json: dict[str, Any],
    known_columns: set[str],
) -> None:
    text = _all_text(
        [
            str(payload.get("summary", "")),
            *[str(item) for key in ("key_findings", "limitations", "suggested_next_steps", "warnings") for item in payload.get(key, []) if isinstance(payload.get(key), list)],
        ]
    )
    for claim in _FORBIDDEN_CLAIMS:
        if claim in text:
            raise AiResponseValidationError("AI response made an unsupported claim.")
    for column_ref in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b", text):
        if column_ref.endswith("_column") and column_ref not in known_columns:
            raise AiResponseValidationError("AI response referenced a nonexistent column.")
    if re.search(r"\bscore\s+(?:is|=|now|changed)", text):
        raise AiResponseValidationError("AI response attempted to alter score.")
    if "publication readiness" in text and not report_json.get("analysis", {}).get("completeness", {}).get("publication_readiness_claimed"):
        raise AiResponseValidationError("AI response claimed publication readiness was assessed.")


def parse_ai_analysis(
    raw: str,
    *,
    provider: str,
    model_name: str,
    input_summary: dict[str, Any],
    report_json: dict[str, Any],
    known_columns: set[str],
) -> AiAnalysis:
    payload = _load_object(raw)
    expected = {"summary", "key_findings", "limitations", "suggested_next_steps", "warnings"}
    unexpected = set(payload) - expected
    if unexpected:
        raise AiResponseValidationError("AI response contained unexpected fields.")
    missing = expected - set(payload)
    if missing:
        raise AiResponseValidationError("AI response omitted required fields.")
    _validate_consistency(payload, report_json, known_columns)
    return AiAnalysis(
        summary=_string(payload, "summary", 1500),
        key_findings=_string_list(payload, "key_findings"),
        limitations=_string_list(payload, "limitations"),
        suggested_next_steps=_string_list(payload, "suggested_next_steps"),
        warnings=_string_list(payload, "warnings"),
        model_name=model_name,
        provider=provider,
        generated_at=datetime.now(timezone.utc).isoformat(),
        input_summary=input_summary,
    )
