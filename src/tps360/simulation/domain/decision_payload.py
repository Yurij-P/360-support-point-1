from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

SUPPORTED_LEGO_SCHEMA_VERSION = "participant-decision-lego-1.0"
LEGACY_STRUCTURED_PLACEHOLDER_KIND = "structured_decision_placeholder"


class DecisionBlockType(StrEnum):
    ACTION = "action"
    OBJECT = "object"
    RESPONSIBLE = "responsible"
    RESOURCE = "resource"
    PRIORITY = "priority"
    TIMING = "timing"
    GEO_AREA = "geo_area"
    PUBLIC_MESSAGE = "public_message"
    ASSISTANCE_REQUEST = "assistance_request"
    CONDITION = "condition"
    RATIONALE = "rationale"
    EXPECTED_RESULT = "expected_result"


class DecisionLinkRelation(StrEnum):
    THEN = "then"
    PARALLEL_WITH = "parallel_with"
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"
    SUPPORTS = "supports"


class DecisionBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_id: str = Field(min_length=1)
    block_type: DecisionBlockType
    label: str = Field(min_length=1)
    data: dict[str, Any] = Field(default_factory=dict)


class DecisionLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(min_length=1)
    from_block_id: str = Field(min_length=1)
    to_block_id: str = Field(min_length=1)
    relation: DecisionLinkRelation


class LegoDecisionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    forbidden_metadata_keys: ClassVar[set[str]] = {
        "system_truth",
        "systemtruth",
        "hidden_scenario_data",
        "hiddenscenariodata",
        "hidden_scenario",
        "hiddenscenario",
        "target_role_ids",
        "targetroles",
        "target_roles",
        "targetparticipantids",
        "target_participant_ids",
        "facilitator_token",
        "facilitatortoken",
        "participant_token",
        "participanttoken",
    }

    schema_version: Literal["participant-decision-lego-1.0"]
    kind: Literal["lego_decision"]
    blocks: list[DecisionBlock] = Field(min_length=1)
    links: list[DecisionLink] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def reject_hidden_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        forbidden = cls._find_forbidden_metadata_keys(value)
        if forbidden:
            keys = ", ".join(sorted(forbidden))
            raise ValueError(f"LEGO decision metadata contains forbidden keys: {keys}")
        return value

    @model_validator(mode="after")
    def validate_block_graph(self) -> Self:
        block_ids = [block.block_id for block in self.blocks]
        duplicate_ids = {block_id for block_id in block_ids if block_ids.count(block_id) > 1}
        if duplicate_ids:
            ids = ", ".join(sorted(duplicate_ids))
            raise ValueError(f"LEGO decision block_id values must be unique: {ids}")

        known_block_ids = set(block_ids)
        missing_refs = {
            ref
            for link in self.links
            for ref in (link.from_block_id, link.to_block_id)
            if ref not in known_block_ids
        }
        if missing_refs:
            refs = ", ".join(sorted(missing_refs))
            raise ValueError(f"LEGO decision links reference unknown block_id values: {refs}")
        return self

    @classmethod
    def _find_forbidden_metadata_keys(cls, value: Any) -> set[str]:
        if isinstance(value, dict):
            found: set[str] = set()
            for key, nested in value.items():
                normalized = str(key).replace("-", "_").replace(" ", "_").lower()
                compact = normalized.replace("_", "")
                if normalized in cls.forbidden_metadata_keys or compact in cls.forbidden_metadata_keys:
                    found.add(str(key))
                found.update(cls._find_forbidden_metadata_keys(nested))
            return found
        if isinstance(value, list):
            list_found: set[str] = set()
            for item in value:
                list_found.update(cls._find_forbidden_metadata_keys(item))
            return list_found
        return set()


def validate_decision_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if _declares_lego_payload(payload):
        try:
            return LegoDecisionPayload.model_validate(payload).model_dump(mode="json")
        except ValidationError as exc:
            details = _validation_error_summary(exc)
            raise ValueError(f"Invalid LEGO decision payload: {details}") from exc
    return dict(payload)


def _declares_lego_payload(payload: dict[str, Any]) -> bool:
    return (
        payload.get("kind") == "lego_decision"
        or payload.get("schema_version") == SUPPORTED_LEGO_SCHEMA_VERSION
    )


def _validation_error_summary(exc: ValidationError) -> str:
    messages: list[str] = []
    for error in exc.errors(include_input=False, include_url=False):
        location = ".".join(str(part) for part in error["loc"])
        context = error.get("ctx")
        if isinstance(context, dict) and isinstance(context.get("error"), ValueError):
            message = str(context["error"])
        else:
            message = str(error["msg"])
        messages.append(f"{location}: {message}" if location else message)
    return "; ".join(messages)