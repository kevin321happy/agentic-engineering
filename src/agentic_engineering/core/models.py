from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")]


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Spec(ProtocolModel):
    spec_id: Identifier
    title: Text
    goal: Text
    constraints: tuple[Text, ...] = ()
    acceptance_criteria: Annotated[tuple[Text, ...], Field(min_length=1)]
    source_refs: tuple[Text, ...] = ()
    status: Literal["draft", "approved"] = "draft"


class ArtifactRef(ProtocolModel):
    artifact_id: Identifier
    kind: Text
    path: Text
    sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    created_by: Text
    created_at: AwareDatetime


class Evidence(ProtocolModel):
    evidence_id: Identifier
    kind: Literal["test", "diff", "observation"]
    claim: Text
    source: Text
    status: Literal["passed", "failed", "unverified"]
    collected_at: AwareDatetime


class GateDecision(ProtocolModel):
    gate_id: Identifier
    status: Literal["GO", "NO_GO"]
    required_evidence: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    missing_evidence: tuple[Identifier, ...]
    decision_reason: Text
    decided_by: Text

    @model_validator(mode="after")
    def check_missing_evidence(self) -> Self:
        if not set(self.missing_evidence).issubset(self.required_evidence):
            raise ValueError("Missing evidence must refer to a requirement of this gate")
        if self.status == "GO" and self.missing_evidence:
            raise ValueError("A gate cannot pass while required evidence is missing")
        return self
