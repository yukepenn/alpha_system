"""Locking canary: stale pack pins are authoring errors, not DATA_GAP."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from alpha_system.governance.validation import ValidationIssue
from alpha_system.research_lane.pack_pin_audit import audit_idea_pack_pins
from alpha_system.research_lane.testability_gate import (
    CHECK_FEATURES_MATERIALIZED,
    GateStatus,
    _data_gap,
    _overall_status,
    _resolver_rejection_check,
)
from alpha_system.runtime.entry_contract import RuntimeEntryStatus
from alpha_system.runtime.input_resolver import RuntimeInputResolverError, _reason

DATASET_VERSION_ID = "dsv_pack_pin_canary"
PARTITION_ID = "ES_2020_120m"
FEATURE_VERSION_ID = "fver_" + "1" * 64
LABEL_VERSION_ID = "lver_" + "2" * 64
FEATURE_REQUEST_ID = "freq_" + "3" * 24
LABEL_SPEC_ID = "lspec_pack_pin_canary"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class _SelectiveRejectingResolver:
    def __init__(self, *, code: str, field: str, expected: str, actual: str) -> None:
        self.reason = _reason(
            code=code,
            message="canary resolver rejection",
            field=field,
            state=RuntimeEntryStatus.INPUTS_BLOCKED,
            expected=expected,
            actual=actual,
        )
        self.reject_labels = code.startswith("label_")

    def resolve_feature_packs(self, *_args: object, **_kwargs: object) -> tuple[object, ...]:
        if not self.reject_labels:
            raise RuntimeInputResolverError(self.reason)
        return ()

    def resolve_label_packs(self, *_args: object, **_kwargs: object) -> tuple[object, ...]:
        if self.reject_labels:
            raise RuntimeInputResolverError(self.reason)
        return ()


def _idea_payload() -> dict[str, object]:
    return {
        "source": "canary:pack_pin_validate_not_datagap",
        "slices": {
            "default": {
                "slice_id": "default",
                "study_kind": "main_effect",
                "dataset_version_id": DATASET_VERSION_ID,
                "partition_id": PARTITION_ID,
                "instrument_id": "ES",
                "session_id": "ES:RTH",
                "data_version": DATASET_VERSION_ID,
                "feature_inputs": [
                    {
                        "role": "factor",
                        "factor_id": "factor",
                        "factor_version": "v1",
                        "pack_ref": FEATURE_VERSION_ID,
                        "feature_request_id": FEATURE_REQUEST_ID,
                    }
                ],
                "label_inputs": [
                    {
                        "role": "path",
                        "label_id": LABEL_SPEC_ID,
                        "pack_ref": LABEL_VERSION_ID,
                        "label_spec_id": LABEL_SPEC_ID,
                    }
                ],
            }
        },
    }


def _issue_codes(issues: Sequence[ValidationIssue]) -> tuple[str, ...]:
    return tuple(issue.code for issue in issues)


def _check_validate_pack_pin_codes() -> None:
    deprecated = audit_idea_pack_pins(
        _idea_payload(),
        resolver=_SelectiveRejectingResolver(
            code="feature_pack_deprecated",
            field="feature_pack_refs[0].lifecycle_state",
            expected="REGISTERED",
            actual=f"DEPRECATED; replacement_feature_version_id={FEATURE_VERSION_ID}",
        ),
    )
    _assert(
        _issue_codes(deprecated) == ("DEPRECATED_PACK_PIN",),
        f"deprecated pack pin must be DEPRECATED_PACK_PIN, got {_issue_codes(deprecated)}",
    )
    _assert(
        "replacement_feature_version_id=" in deprecated[0].actual,
        "deprecated pack pin must expose candidate replacement detail",
    )

    mismatch = audit_idea_pack_pins(
        _idea_payload(),
        resolver=_SelectiveRejectingResolver(
            code="label_pack_dataset_version_mismatch",
            field="label_pack_refs[0].dataset_version_id",
            expected=DATASET_VERSION_ID,
            actual="dsv_other_dataset",
        ),
    )
    _assert(
        _issue_codes(mismatch) == ("DATASET_VERSION_MISMATCH",),
        f"cross-DatasetVersion pin must be DATASET_VERSION_MISMATCH, got {_issue_codes(mismatch)}",
    )


def _check_gate_pack_pin_codes() -> None:
    deprecated = _resolver_rejection_check(
        CHECK_FEATURES_MATERIALIZED,
        "feature packs are not resolvable",
        RuntimeInputResolverError(
            _reason(
                code="feature_pack_deprecated",
                message="feature pack is deprecated",
                field="feature_pack_refs[0].lifecycle_state",
                state=RuntimeEntryStatus.INPUTS_BLOCKED,
                expected="REGISTERED",
                actual=f"DEPRECATED; replacement_feature_version_id={FEATURE_VERSION_ID}",
            )
        ),
    )
    _assert(
        deprecated.status is GateStatus.FAIL,
        f"deprecated pack pin must be gate FAIL, got {deprecated.status}",
    )

    gap = _data_gap("canary_true_data_gap", "genuine value gap")
    rolled = _overall_status((gap, deprecated))
    _assert(
        rolled is GateStatus.FAIL,
        f"pack-pin FAIL must not be masked by DATA_GAP in rollup, got {rolled}",
    )


def run_pack_pin_validate_not_datagap_canary() -> None:
    _check_validate_pack_pin_codes()
    _check_gate_pack_pin_codes()


def main(argv: list[str] | None = None) -> int:
    try:
        run_pack_pin_validate_not_datagap_canary()
    except AssertionError as exc:
        print(f"FAIL pack_pin_validate_not_datagap: {exc}", file=sys.stderr)
        return 1
    print(
        "pack_pin_validate_not_datagap OK: deprecated and cross-DatasetVersion "
        "pack pins fail loudly before DATA_GAP"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
