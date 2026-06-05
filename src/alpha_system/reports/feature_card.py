"""Plain-text feature evidence card renderer."""

from __future__ import annotations

from dataclasses import dataclass

from alpha_system.features.reports import FeatureCoverageReport, FeatureQualityReport
from alpha_system.reports.prohibited_claims import validate_no_prohibited_claims


class FeatureCardError(ValueError):
    """Raised when a feature card cannot be rendered safely."""


@dataclass(frozen=True, slots=True)
class FeatureCard:
    """Render descriptive quality, coverage, and exposure evidence for a feature."""

    quality_report: FeatureQualityReport
    coverage_report: FeatureCoverageReport

    def __post_init__(self) -> None:
        if not isinstance(self.quality_report, FeatureQualityReport):
            raise FeatureCardError("quality_report must be a FeatureQualityReport")
        if not isinstance(self.coverage_report, FeatureCoverageReport):
            raise FeatureCardError("coverage_report must be a FeatureCoverageReport")
        if self.quality_report.feature_version_id != self.coverage_report.feature_version_id:
            raise FeatureCardError("quality and coverage reports must reference the same feature")

    @property
    def has_blocking_findings(self) -> bool:
        """Return whether either report has blocking findings."""

        return (
            self.quality_report.has_blocking_findings
            or self.coverage_report.has_blocking_findings
        )

    def to_dict(self) -> dict[str, object]:
        """Return the structured card payload."""

        payload: dict[str, object] = {
            "card_type": "FeatureCard",
            "feature_id": self.quality_report.feature_id,
            "feature_version_id": self.quality_report.feature_version_id,
            "dataset_version_id": self.quality_report.dataset_version_id,
            "partition_id": self.coverage_report.partition_id,
            "status": "BLOCKING" if self.has_blocking_findings else "DESCRIPTIVE_ONLY",
            "quality": self.quality_report.to_dict(),
            "coverage": self.coverage_report.to_dict(),
            "duplicate_exposure_status": self.quality_report.duplicate_exposure_status,
            "equivalent_feature_group_count": len(
                self.quality_report.equivalent_feature_groups
            ),
        }
        validate_no_prohibited_claims(payload, context="FeatureCard")
        return payload

    def render_text(self) -> str:
        """Render a deterministic plain-text feature evidence card."""

        lines = [
            f"Feature Card: {self.quality_report.feature_id}",
            f"Version: {self.quality_report.feature_version_id}",
            f"DatasetVersion: {self.quality_report.dataset_version_id}",
            "Partition: "
            f"{self.coverage_report.partition_id} "
            f"({self.coverage_report.partition_role.value})",
            "Scope: descriptive substrate evidence only.",
            f"Status: {'BLOCKING' if self.has_blocking_findings else 'DESCRIPTIVE_ONLY'}",
            "",
            "Quality",
            f"- rows: {self.quality_report.record_count}",
            f"- valid rows: {self.quality_report.valid_value_record_count}",
            f"- null_or_nan_rate: {self.quality_report.nan_rate:.6f}",
            f"- constant_feature: {str(self.quality_report.constant_feature).lower()}",
            f"- missing_bbo_rows: {self.quality_report.missing_bbo_count}",
            f"- bbo_quarantined_rows: {self.quality_report.bbo_quarantined_count}",
            f"- available_ts_missing_rows: {self.quality_report.available_ts_missing_count}",
            f"- available_ts_invalid_rows: {self.quality_report.available_ts_invalid_count}",
            "",
            "Coverage",
            f"- symbols: {_bucket_summary(self.coverage_report.symbol_coverage)}",
            f"- sessions: {_bucket_summary(self.coverage_report.session_coverage)}",
            f"- partitions: {_bucket_summary(self.coverage_report.partition_coverage)}",
            "",
            "Duplicate Exposure",
            f"- status: {self.quality_report.duplicate_exposure_status}",
            f"- equivalent_groups: {len(self.quality_report.equivalent_feature_groups)}",
            "",
            "Blocking Findings",
            *_finding_lines(
                (*self.quality_report.blocking, *self.coverage_report.blocking)
            ),
            "",
            "Non-Blocking Metrics",
            *_finding_lines(
                (*self.quality_report.non_blocking, *self.coverage_report.non_blocking)
            ),
        ]
        text = "\n".join(lines).rstrip() + "\n"
        validate_no_prohibited_claims(text, context="FeatureCard")
        return text


def render_feature_card(
    quality_report: FeatureQualityReport,
    coverage_report: FeatureCoverageReport,
) -> str:
    """Render a plain-text card for feature quality and coverage reports."""

    return FeatureCard(quality_report=quality_report, coverage_report=coverage_report).render_text()


def _bucket_summary(buckets: tuple[object, ...]) -> str:
    if not buckets:
        return "none"
    return ", ".join(
        f"{getattr(bucket, 'key')}={getattr(bucket, 'count')}" for bucket in buckets
    )


def _finding_lines(findings: tuple[object, ...]) -> list[str]:
    if not findings:
        return ["- none"]
    return [f"- {getattr(finding, 'code')}: {getattr(finding, 'message')}" for finding in findings]


__all__ = ["FeatureCard", "FeatureCardError", "render_feature_card"]
