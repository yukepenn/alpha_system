"""Validate versioned feature/label pack pins before a probe can spend work."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from alpha_system.governance.validation import ValidationIssue
from alpha_system.research_lane.slice_spec import SliceSpec, SliceSpecError
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    RuntimeInputResolverError,
)

DEPRECATED_PACK_PIN_CODE = "DEPRECATED_PACK_PIN"
DATASET_VERSION_MISMATCH_CODE = "DATASET_VERSION_MISMATCH"
TRUE_DATA_GAP_CODE = "TRUE_DATA_GAP"
REGISTRY_UNAVAILABLE_CODE = "REGISTRY_UNAVAILABLE"


def payload_has_versioned_pack_refs(payload: Mapping[str, Any]) -> bool:
    """Return whether an idea payload carries fver/lver refs worth auditing."""

    return any(
        _slice_has_pack_refs(slice_payload) for _, slice_payload in iter_slice_payloads(payload)
    )


def audit_idea_pack_pins(
    payload: Mapping[str, Any],
    *,
    resolver: FeatureLabelPackResolver,
) -> tuple[ValidationIssue, ...]:
    """Resolve all slice fver/lver pins value-free and return loud validation issues.

    This is intentionally registry-only: it checks lifecycle, dataset-version, and
    partition binding through the sanctioned resolver, but it does not load parquet
    values or materialize anything.
    """

    issues: list[ValidationIssue] = []
    for field_prefix, slice_payload in iter_slice_payloads(payload):
        if not _slice_has_pack_refs(slice_payload):
            continue
        try:
            slice_spec = SliceSpec.from_mapping(slice_payload)
        except SliceSpecError as exc:
            issues.append(
                ValidationIssue(
                    field=field_prefix,
                    code="invalid_slice_spec",
                    message="versioned pack-pin audit requires a valid fast-probe slice",
                    expected="valid SliceSpec with dataset_version_id and partition_id",
                    actual=str(exc),
                )
            )
            continue

        feature_pack_refs = _unique(slice_spec.feature_pack_refs)
        label_pack_refs = _unique(slice_spec.label_pack_refs)
        feature_request_ids = _unique(slice_spec.feature_request_ids)
        label_spec_ids = _unique(slice_spec.label_spec_ids)

        if feature_pack_refs:
            try:
                resolver.resolve_feature_packs(
                    feature_pack_refs,
                    expected_dataset_version_id=slice_spec.dataset_version_id,
                    expected_feature_request_ids=feature_request_ids,
                    partition_id=slice_spec.partition_id,
                    allow_horizon_agnostic_partition=True,
                )
            except RuntimeInputResolverError as exc:
                issues.append(_resolver_issue(field_prefix, exc))
        if label_pack_refs:
            try:
                resolver.resolve_label_packs(
                    label_pack_refs,
                    expected_dataset_version_id=slice_spec.dataset_version_id,
                    expected_label_spec_ids=label_spec_ids,
                    partition_id=slice_spec.partition_id,
                )
            except RuntimeInputResolverError as exc:
                issues.append(_resolver_issue(field_prefix, exc))
    return tuple(issues)


def iter_slice_payloads(payload: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    """Yield every slice-like mapping in an idea payload with a stable field prefix."""

    for key in ("slice_spec", "fast_probe_slice", "fast_probe_slice_spec", "slice"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            yield key, value

    if "slice_id" in payload and (
        "feature_inputs" in payload
        or "features" in payload
        or "label_inputs" in payload
        or "labels" in payload
    ):
        yield "$", payload

    for key in ("slices", "slice_specs"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            for name, item in value.items():
                if isinstance(item, Mapping):
                    yield f"{key}.{name}", item
        elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
            for index, item in enumerate(value):
                if isinstance(item, Mapping):
                    yield f"{key}[{index}]", item


def _slice_has_pack_refs(slice_payload: Mapping[str, Any]) -> bool:
    if _nonempty_sequence(slice_payload.get("feature_pack_refs")):
        return True
    if _nonempty_sequence(slice_payload.get("label_pack_refs")):
        return True
    for key in ("feature_inputs", "features", "label_inputs", "labels"):
        for item in _sequence(slice_payload.get(key)):
            if isinstance(item, Mapping) and (
                item.get("pack_ref")
                or item.get("feature_pack_ref")
                or item.get("label_pack_ref")
                or item.get("feature_version_id")
                or item.get("label_version_id")
            ):
                return True
    return False


def _resolver_issue(field_prefix: str, exc: RuntimeInputResolverError) -> ValidationIssue:
    reason = exc.reason
    reason_code = str(reason.code)
    public_code = _public_issue_code(reason_code)
    return ValidationIssue(
        field=f"{field_prefix}.{reason.field}",
        code=public_code,
        message=_issue_message(public_code, reason.message),
        expected=str(reason.expected),
        actual=str(reason.actual),
    )


def _public_issue_code(reason_code: str) -> str:
    if reason_code in {"feature_pack_deprecated", "label_pack_deprecated"}:
        return DEPRECATED_PACK_PIN_CODE
    if reason_code in {
        "feature_pack_dataset_version_mismatch",
        "label_pack_dataset_version_mismatch",
    }:
        return DATASET_VERSION_MISMATCH_CODE
    if reason_code.endswith("_not_found") or reason_code.startswith("missing_"):
        return TRUE_DATA_GAP_CODE
    return REGISTRY_UNAVAILABLE_CODE


def _issue_message(public_code: str, resolver_message: str) -> str:
    if public_code == DEPRECATED_PACK_PIN_CODE:
        return (
            "authored idea pins a DEPRECATED feature/label version; validate the "
            "REGISTERED replacement explicitly before running"
        )
    if public_code == DATASET_VERSION_MISMATCH_CODE:
        return (
            "authored idea pins a pack from a different DatasetVersion; cross-dataset "
            "replacement is not auto-adopted"
        )
    if public_code == TRUE_DATA_GAP_CODE:
        return "authored idea references a pack that is absent from the registry"
    return resolver_message


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return tuple(value)
    return ()


def _nonempty_sequence(value: Any) -> bool:
    return bool(_sequence(value))


def _unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


__all__ = [
    "DATASET_VERSION_MISMATCH_CODE",
    "DEPRECATED_PACK_PIN_CODE",
    "REGISTRY_UNAVAILABLE_CODE",
    "TRUE_DATA_GAP_CODE",
    "audit_idea_pack_pins",
    "iter_slice_payloads",
    "payload_has_versioned_pack_refs",
]
