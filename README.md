# Zero Trust Edge Workload Enforcement & Resilience

## Project Overview
This project simulates a resource-constrained Edge/Combat Cloud environment using lightweight Kubernetes (K3s). It implements autonomous Zero Trust Workload Enforcement using the Kyverno Policy Engine (with high-speed CEL ValidatingPolicies) to strictly block insecure or privileged containers without requiring human intervention or centralized cloud connectivity.

## System Architecture

```mermaid
flowchart LR
    A[Malicious Workload<br/>Root Container] -->|Blocked in ms| B[Kyverno v1 CEL<br/>Fail-Closed Gate]
    B -->|kyverno_admission_requests_total| C[Prometheus<br/>15s Scrape & Rules]
    C -->|HighZeroTrustViolations| D[Alertmanager<br/>10s Debouncing]
    D -->|POST /alert JSON| E[FastAPI + Pydantic<br/>202 Accepted]

    subgraph Multi-Agent AI Pod - Non-Root & Least-Privilege RBAC
        E --> F[Analyst Agent<br/>ThreatAssessment]
        F --> G[Architect Agent<br/>CEL PolicyProposal]
        G --> H{Reviewer Agent<br/>Safety Guardrails}
    end

    H -->|Approved| I[K8s Enforcer<br/>Dynamic ValidatingPolicy]
    H -->|Rejected / Hallucination| J[Circuit Breaker<br/>Namespace quarantine=true]
    I -.->|Tightens Defense| B
    J -.->|Locks Namespace| B

## Progress
- **Phase 1:** Provisioned a simulated Edge Node using `k3d` (K3s in Docker) and established a baseline by deploying insecure, root-level workloads.
- **Phase 2:** Deployed Kyverno as a Zero Trust Admission Controller. Engineered a CEL-based `ValidatingPolicy` to instantly block any workloads lacking a secure `runAsNonRoot` context. Successfully deployed compliant workloads (`nginx-unprivileged`).
- **Phase 3:** Engineered an AI-ready telemetry pipeline by deploying a lightweight Prometheus server via Helm. Configured `ServiceMonitor` annotations to establish a VIP metric-scraping lane. Executed Chaos testing (malicious workload injection) and successfully visualized `kyverno_admission_requests_total` security blocks in the Prometheus time-series database.
- **Phase 4:** Transitioned from manual testing to automated Chaos Engineering by deploying **Chaos Mesh**. Integrated Prometheus **Alertmanager** to establish an intelligent telemetry routing pipeline, applying robust alert debouncing mechanisms to prevent alert fatigue during high-volume workload injection attacks.
- **Phase 5:** Architected and containerized an asynchronous **Multi-Agent AI** incident response service (`FastAPI`, `Pydantic`, `kubernetes` client) running inside K3s with non-root security contexts, a read-only root filesystem, and **Least-Privilege RBAC** (`ServiceAccount` + `ClusterRole`). Configured Prometheus Alerting Rules (`HighZeroTrustViolations`) to trigger Alertmanager webhooks autonomously. Implemented an `Analyst -> Architect -> Reviewer` pipeline with a deterministic **`quarantine=true` Circuit Breaker** to prevent unsafe policy rollouts, dynamically enforcing live Kyverno v1 CEL `ValidatingPolicies` without centralized cloud dependency.
