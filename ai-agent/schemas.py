from pydantic import BaseModel, Field
from typing import List, Dict, Literal

class Alert(BaseModel):
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]

class WebhookPayload(BaseModel):
    status: str
    receiver: str
    alerts: List[Alert]

class ThreatAssessment(BaseModel):
    target_namespace: str
    violated_policy: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    recommended_action: str
    simulate_hallucination: bool = False

class PolicyProposal(BaseModel):
    policy_name: str
    yaml_manifest: str
    rationale: str

class ReviewResult(BaseModel):
    approved: bool
    errors: List[str] = Field(default_factory=list)
