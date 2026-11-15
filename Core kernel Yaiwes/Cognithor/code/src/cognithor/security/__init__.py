"""Security modules for Cognithor Agent OS. [B§11]"""

from cognithor.security.agent_vault import (
    AgentVaultManager,
)
from cognithor.security.audit import AuditTrail, mask_credentials, mask_dict
from cognithor.security.capabilities import (
    PERMISSIVE,
    RESTRICTIVE,
    STANDARD,
    CapabilityMatrix,
    PolicyEvaluator,
    SandboxProfile,
)
from cognithor.security.cicd_gate import (
    ContinuousRedTeam,
)
from cognithor.security.cicd_gate import (
    ScanScheduler as CICDScanScheduler,
)
from cognithor.security.cicd_gate import (
    SecurityGate as CICDSecurityGate,
)
from cognithor.security.cicd_gate import (
    WebhookNotifier as CICDWebhookNotifier,
)
from cognithor.security.code_audit import (
    CodeAuditor,
)
from cognithor.security.credentials import CredentialStore
from cognithor.security.framework import (
    IncidentTracker,
    PostureScorer,
    SecurityMetrics,
    SecurityTeam,
)
from cognithor.security.hardening import (
    ContainerIsolation,
    CredentialScanner,
    ScanScheduler,
    SecurityGate,
    WebhookNotifier,
)
from cognithor.security.mlops_pipeline import (
    AdversarialFuzzer,
    CIIntegration,
    DependencyScanner,
    ModelInversionDetector,
    SecurityPipeline,
)
from cognithor.security.mtls import ensure_mtls_certs
from cognithor.security.policies import (
    AgentPermissions,
    PolicyEngine,
    PolicyViolation,
    ResourceQuota,
)
from cognithor.security.red_team import (
    PenetrationSuite,
    PromptFuzzer,
    RedTeamFramework,
    SecurityScanner,
)
from cognithor.security.sandbox import Sandbox, SandboxResult
from cognithor.security.sandbox_isolation import (
    IsolationEnforcer,
    PerAgentSecretVault,
    SandboxManager,
    TenantManager,
)
from cognithor.security.sanitizer import (
    InputSanitizer,
    validate_model_path_containment,
    validate_voice_name,
)
from cognithor.security.secret_store import SecretStore
from cognithor.security.token_store import (
    SecureTokenStore,
    create_ssl_context,
    get_token_store,
)
from cognithor.security.vault import (
    EncryptedVault,
    IsolatedSessionStore,
    SessionIsolationGuard,
    VaultManager,
)

__all__ = [
    "PERMISSIVE",
    "RESTRICTIVE",
    "STANDARD",
    "AdversarialFuzzer",
    "AgentPermissions",
    "AuditTrail",
    "CIIntegration",
    "CapabilityMatrix",
    "ContainerIsolation",
    "CredentialScanner",
    "CredentialStore",
    "DependencyScanner",
    "EncryptedVault",
    "IncidentTracker",
    "InputSanitizer",
    "IsolatedSessionStore",
    "ModelInversionDetector",
    "PenetrationSuite",
    "PolicyEngine",
    "PolicyEvaluator",
    "PolicyViolation",
    "PostureScorer",
    "PromptFuzzer",
    "ResourceQuota",
    "Sandbox",
    "SandboxProfile",
    "SandboxResult",
    "ScanScheduler",
    "SecretStore",
    "SecureTokenStore",
    "SecurityGate",
    "SecurityMetrics",
    "SecurityPipeline",
    "SecurityScanner",
    "SecurityTeam",
    "SessionIsolationGuard",
    "VaultManager",
    "WebhookNotifier",
    "create_ssl_context",
    "ensure_mtls_certs",
    "get_token_store",
    "mask_credentials",
    "mask_dict",
    "validate_model_path_containment",
    "validate_voice_name",
]
