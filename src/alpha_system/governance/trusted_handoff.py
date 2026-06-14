"""Trusted-rerun gap reporting for EXPLORATORY strategy-shaped probes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from alpha_system.governance.alpha_spec import ALPHA_SPEC_REQUIRED_FIELDS
from alpha_system.governance.feature_request import FEATURE_REQUEST_REQUIRED_FIELDS
from alpha_system.governance.label_spec import LABEL_SPEC_REQUIRED_FIELDS
from alpha_system.governance.mechanism_card import (
    EXPLORATORY_STAMP,
    validate_mechanism_card,
)
from alpha_system.governance.promotion import (
    EXPLORATORY_PROMOTION_REFUSAL_CODE,
    reject_exploratory_promotion_artifact,
)
from alpha_system.governance.serialization import JsonValue, canonical_serialize, content_hash
from alpha_system.governance.setup_spec import validate_setup_spec
from alpha_system.governance.study_spec import STUDY_SPEC_REQUIRED_FIELDS
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
)

TRUSTED_HANDOFF_SCHEMA = "alpha_system.governance.trusted_handoff_gap_report.v1"
TRUSTED_HANDOFF_STATUS = "TRUSTED_RERUN_GAPS_ONLY"
MISSING_FOR_TRUSTED_RERUN = "MISSING_FOR_TRUSTED_RERUN"
PARTIAL_FOR_TRUSTED_RERUN = "PARTIAL_FOR_TRUSTED_RERUN"
PRESENT_FOR_HUMAN_REVIEW = "PRESENT_FOR_HUMAN_REVIEW"

TRUSTED_SPEC_REQUIRED_FIELDS: Mapping[str, tuple[str, ...]] = {
    "AlphaSpec": ALPHA_SPEC_REQUIRED_FIELDS,
    "StudySpec": STUDY_SPEC_REQUIRED_FIELDS,
    "FeatureRequest": FEATURE_REQUEST_REQUIRED_FIELDS,
    "LabelSpec": LABEL_SPEC_REQUIRED_FIELDS,
}
_CANDIDATE_SPEC_KEYS = {
    "AlphaSpec": ("alpha_spec",),
    "StudySpec": ("study_spec",),
    "FeatureRequest": ("feature_request", "feature_requests"),
    "LabelSpec": ("label_spec",),
}


@dataclass(frozen=True, slots=True)
class TrustedSpecGap:
    """Missing trusted-lane object/field report for one target spec class."""

    object_name: str
    object_identifier: str
    object_present: bool
    required_fields: tuple[str, ...]
    present_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    source_links: tuple[dict[str, JsonValue], ...]

    @property
    def status(self) -> str:
        """Return the object gap status without creating a lifecycle state."""

        if not self.object_present:
            return MISSING_FOR_TRUSTED_RERUN
        if self.missing_fields:
            return PARTIAL_FOR_TRUSTED_RERUN
        return PRESENT_FOR_HUMAN_REVIEW

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-compatible gap report for this trusted-lane target."""

        return {
            "object_name": self.object_name,
            "object_identifier": self.object_identifier,
            "object_present": self.object_present,
            "status": self.status,
            "required_fields": list(self.required_fields),
            "present_fields": list(self.present_fields),
            "missing_fields": list(self.missing_fields),
            "source_links": [dict(link) for link in self.source_links],
        }


@dataclass(frozen=True, slots=True)
class TrustedHandoffGapReport:
    """Value-free handoff from EXPLORATORY probe to trusted-rerun spec gaps."""

    trusted_handoff_id: str
    schema: str
    status: str
    stamp: str
    source_provenance: dict[str, JsonValue]
    required_trusted_objects: tuple[TrustedSpecGap, ...]
    checklist: tuple[str, ...]
    trusted_rerun_required: bool = True
    promotion_eligible: bool = False
    promotion_evidence: bool = False

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-compatible handoff artifact."""

        return {
            "trusted_handoff_id": self.trusted_handoff_id,
            "schema": self.schema,
            "status": self.status,
            "stamp": self.stamp,
            "source_provenance": dict(self.source_provenance),
            "required_trusted_objects": [
                gap.to_dict() for gap in self.required_trusted_objects
            ],
            "checklist": list(self.checklist),
            "trusted_rerun_required": self.trusted_rerun_required,
            "promotion_eligible": self.promotion_eligible,
            "promotion_evidence": self.promotion_evidence,
        }

    def to_canonical_json(self) -> str:
        """Serialize the report deterministically for audit or docs."""

        return canonical_serialize(self.to_dict())


def create_trusted_handoff_gap_report(
    probe_artifact: Mapping[str, Any],
) -> TrustedHandoffGapReport:
    """Emit trusted-rerun spec gaps from an EXPLORATORY probe artifact.

    The scaffold reads declaration metadata and required-field contracts only. It
    does not build trusted-lane specs, create promotion evidence, or change the
    artifact's EXPLORATORY provenance.
    """

    payload = require_mapping(probe_artifact, object_name="trusted handoff probe artifact")
    _require_exploratory_provenance(payload)
    setup_spec = _optional_mapping(payload, "setup_spec")
    mechanism_card = _optional_mapping(payload, "mechanism_card")
    if setup_spec is not None:
        validate_setup_spec(setup_spec)
    if mechanism_card is not None:
        validate_mechanism_card(mechanism_card)

    source_provenance = _source_provenance(payload, setup_spec, mechanism_card)
    gaps = tuple(
        _build_gap(
            object_name=object_name,
            payload=payload,
            setup_spec=setup_spec,
            mechanism_card=mechanism_card,
        )
        for object_name in TRUSTED_SPEC_REQUIRED_FIELDS
    )
    base_report: dict[str, JsonValue] = {
        "schema": TRUSTED_HANDOFF_SCHEMA,
        "status": TRUSTED_HANDOFF_STATUS,
        "stamp": EXPLORATORY_STAMP,
        "source_provenance": source_provenance,
        "required_trusted_objects": [gap.to_dict() for gap in gaps],
        "checklist": _checklist(),
        "trusted_rerun_required": True,
        "promotion_eligible": False,
        "promotion_evidence": False,
    }
    return TrustedHandoffGapReport(
        trusted_handoff_id=_trusted_handoff_id(base_report),
        schema=TRUSTED_HANDOFF_SCHEMA,
        status=TRUSTED_HANDOFF_STATUS,
        stamp=EXPLORATORY_STAMP,
        source_provenance=source_provenance,
        required_trusted_objects=gaps,
        checklist=tuple(_checklist()),
    )


def _require_exploratory_provenance(payload: Mapping[str, Any]) -> None:
    try:
        reject_exploratory_promotion_artifact(payload, field="probe_artifact")
    except GovernanceValidationError as exc:
        if all(
            issue.code == EXPLORATORY_PROMOTION_REFUSAL_CODE for issue in exc.issues
        ):
            return
        raise
    raise GovernanceValidationError(
        ValidationIssue(
            field="probe_artifact.stamp",
            code="missing_exploratory_stamp",
            message="trusted handoff requires an EXPLORATORY probe artifact",
            expected=EXPLORATORY_STAMP,
            actual="missing",
        )
    )


def _build_gap(
    *,
    object_name: str,
    payload: Mapping[str, Any],
    setup_spec: Mapping[str, Any] | None,
    mechanism_card: Mapping[str, Any] | None,
) -> TrustedSpecGap:
    required_fields = TRUSTED_SPEC_REQUIRED_FIELDS[object_name]
    candidate = _candidate_spec_mapping(payload, object_name)
    present_fields = (
        tuple(field for field in required_fields if field in candidate)
        if candidate is not None
        else ()
    )
    missing_fields = tuple(field for field in required_fields if field not in present_fields)
    return TrustedSpecGap(
        object_name=object_name,
        object_identifier=_missing_object_identifier(object_name, setup_spec, payload),
        object_present=candidate is not None,
        required_fields=required_fields,
        present_fields=present_fields,
        missing_fields=missing_fields,
        source_links=_source_links(object_name, setup_spec, mechanism_card),
    )


def _candidate_spec_mapping(
    payload: Mapping[str, Any],
    object_name: str,
) -> Mapping[str, Any] | None:
    trusted_lane_specs = _optional_mapping(payload, "trusted_lane_specs")
    for key in _CANDIDATE_SPEC_KEYS[object_name]:
        value = None
        if trusted_lane_specs is not None and key in trusted_lane_specs:
            value = trusted_lane_specs[key]
        elif key in payload:
            value = payload[key]
        if value is None:
            continue
        if isinstance(value, list):
            value = value[0] if value else None
        if value is None:
            continue
        if not isinstance(value, Mapping):
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"trusted_lane_specs.{key}",
                    code="invalid_field_type",
                    message=f"{object_name} candidate must be a mapping when present",
                    expected="mapping",
                    actual=type(value).__name__,
                )
            )
        return value
    return None


def _source_provenance(
    payload: Mapping[str, Any],
    setup_spec: Mapping[str, Any] | None,
    mechanism_card: Mapping[str, Any] | None,
) -> dict[str, JsonValue]:
    provenance: dict[str, JsonValue] = {
        "stamp": EXPLORATORY_STAMP,
        "source_schema": _text_or_empty(payload.get("schema")),
        "source_phase_id": _text_or_empty(payload.get("phase_id")),
        "source_artifact_id": _first_text(
            payload,
            ("evidence_id", "probe_id", "readout_id", "artifact_id"),
        ),
    }
    if setup_spec is not None:
        provenance["setup_spec_id"] = _text_or_empty(setup_spec.get("setup_spec_id"))
        provenance["path_label"] = _text_or_empty(setup_spec.get("path_label"))
        provenance["horizon"] = _text_or_empty(setup_spec.get("horizon"))
        provenance["context_factor_id"] = _nested_text(
            setup_spec,
            "entry_context",
            "factor_id",
        )
        provenance["trigger_factor_id"] = _nested_text(
            setup_spec,
            "event_trigger",
            "factor_id",
        )
    if mechanism_card is not None:
        provenance["mechanism_id"] = _text_or_empty(mechanism_card.get("mechanism_id"))
        provenance["variant_budget"] = _json_scalar(
            mechanism_card.get("variant_budget"),
            default=0,
        )
    return provenance


def _source_links(
    object_name: str,
    setup_spec: Mapping[str, Any] | None,
    mechanism_card: Mapping[str, Any] | None,
) -> tuple[dict[str, JsonValue], ...]:
    links: list[dict[str, JsonValue]] = []
    if object_name == "AlphaSpec":
        _append_link(links, "hypothesis_id", "mechanism_card.mechanism_id", mechanism_card)
        _append_factor_links(links, "factor_inputs", setup_spec)
        _append_link(links, "label_references", "setup_spec.path_label", setup_spec)
        _append_link(links, "cost_assumptions", "mechanism_card.cost_sensitivity", mechanism_card)
    elif object_name == "StudySpec":
        _append_link(links, "label_spec_id", "setup_spec.path_label", setup_spec)
        _append_link(links, "dataset_scope", "setup_spec.regime_filter", setup_spec)
        _append_link(links, "variant_budget", "mechanism_card.variant_budget", mechanism_card)
        _append_link(links, "family_budget", "mechanism_card.variant_budget", mechanism_card)
    elif object_name == "FeatureRequest":
        _append_factor_links(links, "requested_inputs", setup_spec)
        _append_link(
            links,
            "duplicate_or_equivalent_exposure_notes",
            "mechanism_card.duplicate_exposure",
            mechanism_card,
        )
    elif object_name == "LabelSpec":
        _append_link(links, "horizon", "setup_spec.horizon", setup_spec)
        _append_link(links, "path_rules", "setup_spec.path_label", setup_spec)
        _append_link(links, "target_stop_rules", "setup_spec.target", setup_spec)
        _append_link(links, "target_stop_rules", "setup_spec.stop", setup_spec)
    return tuple(links)


def _append_factor_links(
    links: list[dict[str, JsonValue]],
    trusted_field: str,
    setup_spec: Mapping[str, Any] | None,
) -> None:
    if setup_spec is None:
        return
    for source_field in ("entry_context", "event_trigger"):
        source = setup_spec.get(source_field)
        if not isinstance(source, Mapping):
            continue
        factor_id = source.get("factor_id")
        if not isinstance(factor_id, str) or not factor_id:
            continue
        link: dict[str, JsonValue] = {
            "trusted_field": trusted_field,
            "probe_field": f"setup_spec.{source_field}.factor_id",
            "probe_identifier": factor_id,
        }
        factor_version = source.get("factor_version")
        if isinstance(factor_version, str) and factor_version:
            link["probe_version"] = factor_version
        links.append(link)


def _append_link(
    links: list[dict[str, JsonValue]],
    trusted_field: str,
    probe_field: str,
    source: Mapping[str, Any] | None,
) -> None:
    if source is None:
        return
    value = _value_at_probe_field(source, probe_field)
    if value is None:
        return
    links.append(
        {
            "trusted_field": trusted_field,
            "probe_field": probe_field,
            "probe_identifier": _source_identifier(value),
        }
    )


def _value_at_probe_field(source: Mapping[str, Any], probe_field: str) -> Any:
    parts = probe_field.split(".")
    value: Any = source
    for part in parts[1:]:
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _source_identifier(value: Any) -> JsonValue:
    if isinstance(value, str | int | bool):
        return value
    if isinstance(value, Mapping):
        for key in ("factor_id", "factor_version", "path_outcome", "binding", "policy"):
            item = value.get(key)
            if isinstance(item, str | int | bool):
                return item
        return sorted(str(key) for key in value.keys())
    if isinstance(value, list):
        return [
            _source_identifier(item)
            for item in value
            if isinstance(_source_identifier(item), str | int | bool | list)
        ]
    return str(type(value).__name__)


def _missing_object_identifier(
    object_name: str,
    setup_spec: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
) -> str:
    setup_id = ""
    if setup_spec is not None:
        setup_id = _text_or_empty(setup_spec.get("setup_spec_id"))
    if not setup_id:
        setup_id = _first_text(payload, ("evidence_id", "probe_id", "readout_id"))
    suffix = setup_id or "exploratory_probe"
    return f"missing_{_snake_case(object_name)}_for_{suffix}"


def _checklist() -> list[str]:
    return [
        "Author an AlphaSpec with pre-registered hypothesis, instruments, inputs, "
        "label references, assumptions, exclusions, failure modes, and promotion criteria.",
        "Author FeatureRequest metadata for the context and trigger inputs, including "
        "availability assumptions and duplicate or equivalent exposure notes.",
        "Author a LabelSpec for the trusted path-label binding, including horizon, "
        "path rules, target/stop rules, availability time, and leakage checks.",
        "Author a StudySpec linking AlphaSpec and LabelSpec with dataset scope, split "
        "protocol, metrics, assumptions, variant budget, locked-test policy, negative "
        "controls, and stopping rules.",
        "Run the trusted rerun separately; this EXPLORATORY handoff is only a gap report.",
    ]


def _trusted_handoff_id(payload_without_id: Mapping[str, JsonValue]) -> str:
    return f"thgap_{content_hash(dict(payload_without_id))[:24]}"


def _optional_mapping(payload: Mapping[str, Any], field: str) -> Mapping[str, Any] | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code="invalid_field_type",
                message=f"{field} must be a mapping when present",
                expected="mapping",
                actual=type(value).__name__,
            )
        )
    return value


def _first_text(payload: Mapping[str, Any], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = payload.get(field)
        if isinstance(value, str) and value:
            return value
    return ""


def _nested_text(payload: Mapping[str, Any], field: str, nested_field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        return ""
    return _text_or_empty(value.get(nested_field))


def _text_or_empty(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _json_scalar(value: Any, *, default: JsonValue) -> JsonValue:
    return value if isinstance(value, bool | int | float | str) or value is None else default


def _snake_case(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if char.isupper() and index:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


__all__ = [
    "MISSING_FOR_TRUSTED_RERUN",
    "PARTIAL_FOR_TRUSTED_RERUN",
    "PRESENT_FOR_HUMAN_REVIEW",
    "TRUSTED_HANDOFF_SCHEMA",
    "TRUSTED_HANDOFF_STATUS",
    "TRUSTED_SPEC_REQUIRED_FIELDS",
    "TrustedHandoffGapReport",
    "TrustedSpecGap",
    "create_trusted_handoff_gap_report",
]
