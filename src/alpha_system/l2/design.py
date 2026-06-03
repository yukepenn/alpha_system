"""Design-readiness metadata for future L2 capabilities."""

from __future__ import annotations

from dataclasses import dataclass

from alpha_system.core.enums import ReadinessState


L2_READINESS_STATE = ReadinessState.DESIGN_ONLY
L2_EXECUTION_IMPLEMENTATION = "none"
L2_PNL_TRUTH = "tier1_reference_1minute_bar_engine"

DESIGN_ONLY_SCOPE_SUMMARY = (
    "ASV1-P25 records L2 schemas, timestamp semantics, and validation contracts "
    "only. It does not implement replay, queue position, passive fills, live data, "
    "broker connectivity, paper trading, or a second PnL truth."
)

FORBIDDEN_L2_RUNTIME_CAPABILITIES: tuple[str, ...] = (
    "l2_replay_engine",
    "l3_order_book_reconstruction",
    "queue_position_model",
    "passive_fill_simulation",
    "live_market_data_ingestion",
    "broker_execution",
    "paper_trading",
)


@dataclass(frozen=True, slots=True)
class FutureL2Capability:
    """Design metadata for a future L2 capability, not an implementation."""

    capability_id: str
    title: str
    readiness: ReadinessState
    required_future_inputs: tuple[str, ...]
    excluded_this_campaign: tuple[str, ...]
    design_note: str


FUTURE_L2_CAPABILITIES: tuple[FutureL2Capability, ...] = (
    FutureL2Capability(
        capability_id="book_reconstruction",
        title="Future book reconstruction",
        readiness=ReadinessState.DESIGN_ONLY,
        required_future_inputs=(
            "source-specific sequencing rules",
            "snapshot/delta recovery rules",
            "gap and reset handling",
        ),
        excluded_this_campaign=("replay engine", "book reconstruction algorithm"),
        design_note="Schemas expose enough fields to discuss reconstruction later.",
    ),
    FutureL2Capability(
        capability_id="queue_position",
        title="Future queue-position research",
        readiness=ReadinessState.DESIGN_ONLY,
        required_future_inputs=(
            "source order-count semantics",
            "venue priority rules",
            "cancel/replace behavior",
        ),
        excluded_this_campaign=("queue-position model", "L3 reconstruction"),
        design_note="Queue needs are documented but no queue model is present.",
    ),
    FutureL2Capability(
        capability_id="latency_model",
        title="Future latency model",
        readiness=ReadinessState.DESIGN_ONLY,
        required_future_inputs=(
            "feed receive clock policy",
            "research availability policy",
            "latency distribution evidence",
        ),
        excluded_this_campaign=("live feed timing", "execution latency simulator"),
        design_note="receive_ts and available_ts are separate readiness fields.",
    ),
    FutureL2Capability(
        capability_id="passive_fills",
        title="Future passive-fill research",
        readiness=ReadinessState.DESIGN_ONLY,
        required_future_inputs=(
            "validated replay",
            "queue-position assumptions",
            "venue and order-type rules",
        ),
        excluded_this_campaign=("passive-fill simulation", "order routing"),
        design_note="Passive-fill requirements are captured only as future design.",
    ),
)


def design_only_capability_ids() -> tuple[str, ...]:
    """Return future L2 capability ids recorded as design metadata."""
    return tuple(capability.capability_id for capability in FUTURE_L2_CAPABILITIES)


def capability_by_id(capability_id: str) -> FutureL2Capability:
    """Return one future capability descriptor by id."""
    for capability in FUTURE_L2_CAPABILITIES:
        if capability.capability_id == capability_id:
            return capability
    msg = f"unknown future L2 capability: {capability_id}"
    raise KeyError(msg)


def l2_scope_boundary_assertions() -> tuple[str, ...]:
    """Return durable assertions reviewers can use for scope checks."""
    return (
        "L2 readiness state is design_only.",
        "No replay, queue-position, passive-fill, live, broker, or paper scope exists.",
        "The Tier 1 reference 1-minute bar engine remains the single PnL truth.",
        "L2 schemas do not make alpha, tradability, or production-execution claims.",
    )
