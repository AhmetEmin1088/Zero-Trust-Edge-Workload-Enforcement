import logging
import yaml
from schemas import Alert, ThreatAssessment, PolicyProposal, ReviewResult
from k8s_enforcer import apply_validating_policy, apply_namespace_quarantine, PROTECTED_NAMESPACES

logger = logging.getLogger("multi-agent")


def analyst_agent(alert: Alert) -> ThreatAssessment:
    """Agent 1: Extracts threat context and determines severity."""
    namespace = alert.labels.get("namespace", "default")
    policy = alert.labels.get("policy_name", "unknown")
    severity = alert.labels.get("severity", "HIGH").upper()
    if severity not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        severity = "HIGH"

    simulate_bad_ai = alert.labels.get("test_hallucination", "false").lower() == "true"

    assessment = ThreatAssessment(
        target_namespace=namespace,
        violated_policy=policy,
        severity=severity,
        recommended_action=f"Enforce readOnlyRootFilesystem in '{namespace}'",
        simulate_hallucination=simulate_bad_ai,
    )
    logger.info(f"[ANALYST] Assessed threat: namespace='{assessment.target_namespace}', severity='{assessment.severity}'")
    return assessment


def architect_agent(assessment: ThreatAssessment) -> PolicyProposal:
    """Agent 2: Generates a Kyverno v1 CEL ValidatingPolicy."""
    policy_name = f"ai-hardening-{assessment.target_namespace}"

    if assessment.simulate_hallucination:
        # Simulated AI mistake: omits protected system namespaces
        cel_expr = "object.spec.containers.all(c, has(c.securityContext) && c.securityContext.readOnlyRootFilesystem == true)"
    else:
        # Compliant CEL expression preserving the VIP Lane
        cel_expr = (
            "request.namespace in ['kube-system', 'kyverno', 'monitoring', 'chaos-mesh'] || "
            "object.spec.containers.all(c, has(c.securityContext) && "
            "has(c.securityContext.readOnlyRootFilesystem) && "
            "c.securityContext.readOnlyRootFilesystem == true)"
        )

    manifest = f"""apiVersion: policies.kyverno.io/v1
kind: ValidatingPolicy
metadata:
  name: {policy_name}
  labels:
    managed-by: zero-trust-ai-agent
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: [""]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["pods"]
  validations:
    - expression: "{cel_expr}"
      message: "AI-GENERATED ZERO TRUST POLICY: Containers must use a read-only root filesystem."
"""
    logger.info(f"[ARCHITECT] Drafted ValidatingPolicy '{policy_name}'")
    return PolicyProposal(
        policy_name=policy_name,
        yaml_manifest=manifest,
        rationale=assessment.recommended_action,
    )


def reviewer_agent(proposal: PolicyProposal) -> ReviewResult:
    """Agent 3: Deterministic safety gate that audits AI-generated YAML."""
    errors = []

    try:
        parsed = yaml.safe_load(proposal.yaml_manifest)
    except yaml.YAMLError as e:
        return ReviewResult(approved=False, errors=[f"Invalid YAML syntax: {e}"])

    if not isinstance(parsed, dict):
        return ReviewResult(approved=False, errors=["YAML root must be a dictionary"])

    if parsed.get("apiVersion") != "policies.kyverno.io/v1":
        errors.append(f"Unsupported apiVersion: {parsed.get('apiVersion')}. Must be policies.kyverno.io/v1")

    if parsed.get("kind") != "ValidatingPolicy":
        errors.append(f"Unsupported kind: {parsed.get('kind')}. Must be ValidatingPolicy")

    validations = parsed.get("spec", {}).get("validations", [])
    if not validations:
        errors.append("Policy contains no CEL validation expressions")
    else:
        for rule in validations:
            expr = rule.get("expression", "")
            for ns in PROTECTED_NAMESPACES:
                if ns not in expr:
                    errors.append(f"Safety violation: CEL expression fails to exclude protected namespace '{ns}'")

    if errors:
        logger.error(f"[REVIEWER] REJECTED policy '{proposal.policy_name}': {errors}")
        return ReviewResult(approved=False, errors=errors)

    logger.info(f"[REVIEWER] APPROVED policy '{proposal.policy_name}'. All safety guardrails passed.")
    return ReviewResult(approved=True)


def circuit_breaker_quarantine(namespace: str, reason: str):
    """Fail-safe fallback when AI policy generation or API apply fails."""
    logger.critical(f"[CIRCUIT BREAKER TRIPPED] Reason: {reason}")
    apply_namespace_quarantine(namespace)


def run_multi_agent_pipeline(alert: Alert):
    """Orchestrates Analyst -> Architect -> Reviewer -> Live K3s Enforcement."""
    logger.info("--- Starting Asynchronous Multi-Agent Pipeline ---")
    assessment = analyst_agent(alert)
    proposal = architect_agent(assessment)
    review = reviewer_agent(proposal)

    if review.approved:
        logger.info(f"[ENFORCER] Applying approved policy '{proposal.policy_name}' to K3s cluster...")
        applied = apply_validating_policy(proposal.yaml_manifest)
        if not applied:
            circuit_breaker_quarantine(
                assessment.target_namespace,
                "K3s API server rejected the approved ValidatingPolicy",
            )
    else:
        circuit_breaker_quarantine(assessment.target_namespace, "; ".join(review.errors))

    logger.info("--- Pipeline Complete ---")
