from __future__ import annotations

from decimal import Decimal

from alpha_system.portfolio.universe_constraints import (
    UniverseExposureConstraints,
    UniverseExposureTarget,
    apply_universe_exposure_constraints,
    evaluate_universe_exposure,
)


def test_universe_gross_and_net_limits_are_across_symbols() -> None:
    targets = (
        UniverseExposureTarget(instrument_id="EQ_US_SYNTH_A", signed_notional=Decimal("80000")),
        UniverseExposureTarget(instrument_id="EQ_US_SYNTH_B", signed_notional=Decimal("40000")),
    )
    constraints = UniverseExposureConstraints(max_gross_exposure=Decimal("1.0"), max_net_exposure=Decimal("0.5"))

    adjustment = apply_universe_exposure_constraints(targets, equity=Decimal("100000"), constraints=constraints)

    assert adjustment.reasons == ("max_gross_exposure", "max_net_exposure")
    assert adjustment.evaluation.gross_limit_ok is True
    assert adjustment.evaluation.net_limit_ok is True
    assert adjustment.evaluation.net_notional <= Decimal("50000")


def test_universe_exposure_evaluation_tracks_future_group_representations() -> None:
    targets = (
        UniverseExposureTarget(
            instrument_id="EQ_US_SYNTH_A",
            signed_notional=Decimal("10000"),
            asset_class="equity",
            sector="synthetic_sector",
        ),
        UniverseExposureTarget(
            instrument_id="FUT_US_SYNTH_A",
            signed_notional=Decimal("-5000"),
            asset_class="future",
            sector="synthetic_sector",
        ),
    )
    evaluation = evaluate_universe_exposure(
        targets,
        equity=Decimal("100000"),
        constraints=UniverseExposureConstraints(max_gross_exposure=Decimal("1")),
    )

    assert evaluation.by_asset_class == {"equity": Decimal("10000"), "future": Decimal("5000")}
    assert evaluation.by_sector == {"synthetic_sector": Decimal("15000")}
    assert evaluation.breaches == ()
