import logging
import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger("k8s-enforcer")

PROTECTED_NAMESPACES = ["kube-system", "kyverno", "monitoring", "chaos-mesh"]


def load_k8s_client():
    """Loads in-cluster ServiceAccount config inside K3s, or local kubeconfig in WSL2."""
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def apply_validating_policy(yaml_manifest: str) -> bool:
    """Idempotently creates or patches a Kyverno v1 ValidatingPolicy in K3s."""
    load_k8s_client()
    custom_api = client.CustomObjectsApi()
    body = yaml.safe_load(yaml_manifest)
    policy_name = body["metadata"]["name"]

    group = "policies.kyverno.io"
    version = "v1"
    plural = "validatingpolicies"

    try:
        custom_api.create_cluster_custom_object(
            group=group,
            version=version,
            plural=plural,
            body=body,
        )
        logger.info(f"[K8S-API] Created ValidatingPolicy '{policy_name}' in K3s.")
        return True
    except ApiException as e:
        if e.status == 409:
            custom_api.patch_cluster_custom_object(
                group=group,
                version=version,
                plural=plural,
                name=policy_name,
                body=body,
                _content_type="application/merge-patch+json",
            )
            logger.info(f"[K8S-API] Updated existing ValidatingPolicy '{policy_name}' in K3s.")
            return True
        logger.error(f"[K8S-API] Failed to apply ValidatingPolicy '{policy_name}': {e.reason} - {e.body}")
        return False


def apply_namespace_quarantine(namespace: str) -> bool:
    """Applies the deterministic 'quarantine=true' label to a compromised namespace."""
    if namespace in PROTECTED_NAMESPACES:
        logger.error(f"[K8S-API] Blocked attempt to quarantine protected system namespace '{namespace}'.")
        return False

    load_k8s_client()
    core_api = client.CoreV1Api()
    patch_body = {"metadata": {"labels": {"quarantine": "true"}}}

    try:
        core_api.patch_namespace(name=namespace, body=patch_body)
        logger.critical(f"[K8S-API] Applied label 'quarantine=true' to namespace '{namespace}'.")
        return True
    except ApiException as e:
        logger.error(f"[K8S-API] Failed to quarantine namespace '{namespace}': {e.reason}")
        return False
