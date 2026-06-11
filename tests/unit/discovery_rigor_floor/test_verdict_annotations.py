from __future__ import annotations

import hashlib
import json
from pathlib import Path

from alpha_system.governance.verdict_reason_code import VerdictReasonCode

ANNOTATION_ROOT = Path("research/futures_core_alpha_pilot_v1/verdict_annotations")
EXPECTED_STUDY_SPEC_IDS = {
    "sspec_02c400a561891171a33c0c66",
    "sspec_267cc052e37668339c38d179",
    "sspec_27bf1262b0bd23d27191cc86",
    "sspec_69c22ec5847395ac8e81b5b6",
    "sspec_9f6f741192a4b534f06e51c0",
    "sspec_aff70fcbc4b7ff226fcc8149",
}


def test_core_pilot_verdict_annotations_bind_to_original_inconclusive_verdicts() -> None:
    annotation_paths = sorted(ANNOTATION_ROOT.glob("annotation_sspec_*.json"))

    assert {path.stem.removeprefix("annotation_") for path in annotation_paths} == (
        EXPECTED_STUDY_SPEC_IDS
    )

    for annotation_path in annotation_paths:
        annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
        original_path = Path(str(annotation["original_verdict_path"]))
        original = json.loads(original_path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(original_path.read_bytes()).hexdigest()

        assert annotation["schema"] == "discovery_rigor_floor.verdict_annotation.v1"
        assert annotation["campaign_id"] == "DISCOVERY_RIGOR_FLOOR_V1"
        assert annotation["phase_id"] == "RIGOR-P01"
        assert annotation["study_spec_id"] in EXPECTED_STUDY_SPEC_IDS
        assert annotation["study_spec_id"] == original["idea"]["study_spec_id"]
        assert annotation["original_verdict_sha256"] == digest
        assert original["judgement"]["statistical_reviewer_judgement"] == "INCONCLUSIVE"
        assert annotation["original_statistical_reviewer_judgement"] == "INCONCLUSIVE"
        assert VerdictReasonCode(annotation["reason_code"])
        assert annotation["basis_citation"]["quote"] == original["judgement"]["basis"]
        assert "does not alter, re-open, or re-judge" in annotation["classification_statement"]
