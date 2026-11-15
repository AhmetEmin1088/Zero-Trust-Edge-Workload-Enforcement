# Zero Trust Edge Workload Enforcement & Resilience

## Project Overview
This project simulates a resource-constrained Edge/Combat Cloud environment using lightweight Kubernetes (K3s). It implements autonomous Zero Trust Workload Enforcement using the Kyverno Policy Engine (with high-speed CEL ValidatingPolicies) to strictly block insecure or privileged containers without requiring human intervention or centralized cloud connectivity.

## Progress
- **Phase 1 (Completed):** Provisioned a simulated Edge Node using `k3d` (K3s in Docker) and established a baseline by deploying insecure, root-level workloads.
- **Phase 2 (Completed):** Deployed Kyverno as a Zero Trust Admission Controller. Engineered a CEL-based `ValidatingPolicy` to instantly block any workloads lacking a secure `runAsNonRoot` context. Successfully deployed compliant workloads (`nginx-unprivileged`).
