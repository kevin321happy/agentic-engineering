import json
from pathlib import Path

import pytest


def test_spec_requires_observable_acceptance_criteria():
    from pydantic import ValidationError

    from agentic_engineering.core.models import Spec

    data = {"spec_id": "sp-list", "title": "Empty state", "goal": "Explain an empty list"}
    for criteria in ([], ["   "]):
        with pytest.raises(ValidationError):
            Spec.model_validate({**data, "acceptance_criteria": criteria})
    spec = Spec.model_validate({**data, "acceptance_criteria": ["Show an empty state"]})
    assert Spec.model_validate_json(spec.model_dump_json()) == spec
    with pytest.raises(ValidationError):
        Spec.model_validate({**spec.model_dump(), "approved": True})


def test_evidence_rejects_advice_and_naive_timestamps():
    from pydantic import ValidationError

    from agentic_engineering.core.models import Evidence

    data = {
        "evidence_id": "ev-list",
        "kind": "test",
        "claim": "Empty state rendered",
        "source": "run:1",
        "status": "passed",
        "collected_at": "2026-01-01T12:00:00Z",
    }
    assert Evidence.model_validate(data).status == "passed"
    for changes in (
        {"kind": "knowledge_hit"},
        {"collected_at": "2026-01-01T12:00:00"},
        {"status": "maybe"},
        {"evidence_id": "two words"},
    ):
        with pytest.raises(ValidationError):
            Evidence.model_validate({**data, **changes})


def test_gate_cannot_claim_go_with_missing_proof():
    from pydantic import ValidationError

    from agentic_engineering.core.models import GateDecision

    data = {
        "gate_id": "gate-list",
        "required_evidence": ["ev-list"],
        "missing_evidence": ["ev-list"],
        "decided_by": "policy:list",
        "decision_reason": "Regression check missing",
    }
    assert GateDecision.model_validate({**data, "status": "NO_GO"}).missing_evidence
    with pytest.raises(ValidationError):
        GateDecision.model_validate({**data, "status": "GO"})


def test_artifact_requires_sha256():
    from pydantic import ValidationError

    from agentic_engineering.core.models import ArtifactRef

    data = {
        "artifact_id": "art-list",
        "kind": "report",
        "path": "reports/list.json",
        "created_by": "runner",
        "created_at": "2026-01-01T12:00:00Z",
    }
    with pytest.raises(ValidationError):
        ArtifactRef.model_validate({**data, "sha256": "unchecked"})
    assert ArtifactRef.model_validate({**data, "sha256": "a" * 64}).path == "reports/list.json"


def test_published_schemas_match_models():
    from agentic_engineering.core.models import Evidence, Spec

    root = Path(__file__).resolve().parents[3] / "schemas"
    for model in (Spec, Evidence):
        assert json.loads((root / f"{model.__name__.lower()}.schema.json").read_text()) == (
            model.model_json_schema()
        )
