from __future__ import annotations

import pytest

from alpha_system.governance.promotion import (
    EXPLORATORY_PROMOTION_REFUSAL_CODE,
    PromotionLifecycleState,
    reject_exploratory_promotion_artifact,
)
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.validation import GovernanceValidationError


def test_promotion_guard_refuses_exploratory_artifact() -> None:
    artifact = {
        "readout_id": "fixture",
        "stamp": "EXPLORATORY",
        "promotion_eligible": False,
    }

    with pytest.raises(GovernanceValidationError) as exc_info:
        reject_exploratory_promotion_artifact(artifact, field="readout")

    assert exc_info.value.issues[0].code == EXPLORATORY_PROMOTION_REFUSAL_CODE
    assert exc_info.value.issues[0].field == "readout.stamp"


def test_promotion_gate_refuses_exploratory_artifact_before_trusted_transition() -> None:
    context = PromotionGateContext(
        promotion_artifacts=(
            {
                "readout_id": "fixture",
                "stamp": "EXPLORATORY",
                "promotion_eligible": False,
            },
        )
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            PromotionLifecycleState.REVIEWED,
            PromotionLifecycleState.CANDIDATE,
            context,
        )

    assert exc_info.value.issues[0].code == EXPLORATORY_PROMOTION_REFUSAL_CODE
    assert exc_info.value.issues[0].field == "promotion_artifacts[0].stamp"
