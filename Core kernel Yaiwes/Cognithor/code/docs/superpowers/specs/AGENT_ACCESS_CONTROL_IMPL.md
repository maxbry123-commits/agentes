# Cognithor – Agent Access Control System (AACS)

## Implementierungsanleitung für das Coding-Modell

> **Zweck dieses Dokuments:** Du bist ein AI-Coding-Modell in einer IDE. Dieses Dokument beschreibt das vollständige Agent Access Control System für Cognithor. Deine Aufgabe:
> 1. Prüfe den bestehenden Codebase auf bereits implementierte Komponenten
> 2. Identifiziere Lücken zwischen IST und SOLL
> 3. Implementiere fehlende Komponenten in der vorgegebenen Reihenfolge
>
> **Projektkontext:** Cognithor ist ein Agent Operating System (Apache 2.0, Python 3.12+, ~118k LOC). Architektur: PGE Trinity (Planner → Gatekeeper → Executor). Bestehende Krypto-Infrastruktur: Ed25519-Signaturen, HMAC-Audit-Trails, Hashline Guard.

---

## Inhaltsverzeichnis

1. [Bestandsaufnahme – Was prüfen?](#1-bestandsaufnahme)
2. [Architekturübersicht](#2-architekturübersicht)
3. [Phase 1 – Capability Token Core](#3-phase-1)
4. [Phase 2 – Hashline Guard Integration](#4-phase-2)
5. [Phase 3 – MCP Tool Gate](#5-phase-3)
6. [Phase 4 – Memory Tier Access Control](#6-phase-4)
7. [Phase 5 – A2A Gateway & SPIFFE Bridge](#7-phase-5)
8. [Phase 6 – Dynamic Trust Scoring](#8-phase-6)
9. [Testanforderungen](#9-testanforderungen)
10. [Migrationsplan](#10-migrationsplan)

---

## 1. Bestandsaufnahme – Was prüfen? <a id="1-bestandsaufnahme"></a>

Bevor du Code schreibst, prüfe den aktuellen Stand. Führe folgende Checks durch und dokumentiere die Ergebnisse als Kommentar im jeweiligen Modul.

### 1.1 Vorhandene Krypto-Infrastruktur

```bash
# Suche nach Ed25519-Implementierungen
grep -rn "Ed25519\|ed25519\|signing_key\|verify_key\|nacl\|cryptography.hazmat" --include="*.py" .

# Suche nach HMAC-Implementierungen
grep -rn "hmac\|HMAC\|hash_chain\|hashline" --include="*.py" .

# Suche nach bestehenden Token/Auth-Mechanismen
grep -rn "capability\|token\|permission\|authorization\|access_control\|trust_level" --include="*.py" .
```

**Erwartete Funde:**
- [ ] Ed25519 Schlüsselgenerierung und Signierung
- [ ] HMAC-basierte Audit-Chains (Hashline Guard)
- [ ] DID-Implementierung (Decentralized Identifiers)
- [ ] Bestehende Rollen/Permission-Logik

### 1.2 PGE Trinity Kommunikation

```bash
# Wie kommunizieren Planner, Gatekeeper, Executor aktuell?
grep -rn "class Planner\|class Gatekeeper\|class Executor" --include="*.py" .
grep -rn "def delegate\|def dispatch\|def route_task\|def send_message" --include="*.py" .

# Gibt es bereits Message-Objekte zwischen Komponenten?
grep -rn "class Message\|class TaskMessage\|class AgentMessage" --include="*.py" .
```

**Dokumentiere:**
- Wie werden Nachrichten zwischen PGE-Komponenten aktuell übergeben?
- Gibt es bereits eine Message-Klasse mit Metadaten?
- Wird aktuell überhaupt validiert, wer eine Nachricht sendet?

### 1.3 MCP Tool Execution

```bash
# Wie werden MCP-Tools aufgerufen?
grep -rn "mcp\|tool_call\|tool_execute\|ToolRegistry" --include="*.py" .

# Gibt es Berechtigungsprüfungen vor Tool-Ausführung?
grep -rn "def check_permission\|def authorize\|def validate_access" --include="*.py" .
```

### 1.4 Memory-System

```bash
# Memory-Tier-Struktur
grep -rn "memory_tier\|MemoryTier\|cognitive_memory\|tier_level" --include="*.py" .

# Zugriffskontrollen auf Memory
grep -rn "memory.*access\|memory.*permission\|memory.*read\|memory.*write" --include="*.py" .
```

### 1.5 A2A Protocol

```bash
# Bestehende Agent-to-Agent Kommunikation
grep -rn "a2a\|A2A\|agent_to_agent\|peer_agent\|external_agent" --include="*.py" .
```

### 1.6 Ergebnis-Template

Erstelle nach der Prüfung eine Datei `aacs_audit_result.json`:

```json
{
  "audit_date": "ISO-TIMESTAMP",
  "ed25519_found": true,
  "ed25519_location": "cognithor/crypto/signing.py",
  "hashline_guard_found": true,
  "hashline_guard_location": "cognithor/audit/hashline.py",
  "existing_auth_mechanism": "none | basic_roles | token_based",
  "pge_message_class_exists": false,
  "mcp_permission_check_exists": false,
  "memory_tier_access_control_exists": false,
  "a2a_protocol_exists": true,
  "a2a_auth_mechanism": "none | basic | capability_tokens",
  "components_to_implement": [
    "capability_token_core",
    "token_validator",
    "hashline_capability_logger",
    "mcp_tool_gate",
    "memory_access_controller",
    "a2a_spiffe_bridge",
    "dynamic_trust_scorer"
  ]
}
```

---

## 2. Architekturübersicht <a id="2-architekturübersicht"></a>

### 2.1 Systemdiagramm

```
┌─────────────────────────────────────────────────────────────────┐
│                    COGNITHOR AACS                                │
│                                                                 │
│  ┌──────────┐    CapToken    ┌─────────────┐    SubToken       │
│  │ PLANNER  │───────────────►│ GATEKEEPER  │──────────────┐    │
│  │ (Root    │                │ (Validates   │              │    │
│  │  Auth)   │                │  + Delegates)│              │    │
│  └──────────┘                └──────┬──────┘              │    │
│       │                             │                      │    │
│       │ Signs root                  │ Validates            │    │
│       │ capability                  │ every action         ▼    │
│       │ tokens                      │               ┌──────────┐│
│       │                             │               │EXECUTOR A││
│       │                             │               │(scoped)  ││
│       │                             │               └──────────┘│
│       │                             │                      │    │
│       │                             │                      ▼    │
│       │                             │               ┌──────────┐│
│       │                             │               │EXECUTOR B││
│       │                             │               │(scoped)  ││
│       │                             │               └──────────┘│
│       │                             │                           │
│       ▼                             ▼                           │
│  ┌──────────┐              ┌──────────────┐   ┌──────────────┐ │
│  │ HASHLINE │◄─────────────│  TOKEN       │   │  MCP TOOL    │ │
│  │ GUARD    │  logs every  │  VALIDATOR   │   │  GATE        │ │
│  │ (Audit)  │  grant/deny  │              │   │  (pre-exec   │ │
│  └──────────┘              └──────────────┘   │   check)     │ │
│                                               └──────────────┘ │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────────────────┐                   │
│  │         MEMORY TIER CONTROLLER           │                   │
│  │  Tier 1: Working    → Any Executor       │                   │
│  │  Tier 2: Task       → Assigned Executor  │                   │
│  │  Tier 3: Session    → Gatekeeper + auth  │                   │
│  │  Tier 4: Knowledge  → Planner + GK only  │                   │
│  │  Tier 5: SysConfig  → Planner + Operator │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                 │
│  ┌──────────────────────────────────────────┐                   │
│  │         A2A GATEWAY (Phase 5)            │                   │
│  │  Internal CapTokens ←→ SPIFFE/mTLS      │                   │
│  │  Trust Translation for external agents   │                   │
│  └──────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Dateisystem-Struktur (SOLL)

```
cognithor/
├── aacs/                          # Agent Access Control System
│   ├── __init__.py
│   ├── tokens/
│   │   ├── __init__.py
│   │   ├── capability_token.py    # Phase 1: Token-Datenmodell
│   │   ├── token_issuer.py        # Phase 1: Token-Erstellung + Signierung
│   │   ├── token_validator.py     # Phase 1: Token-Validierung
│   │   ├── token_store.py         # Phase 1: Aktive Token im Speicher
│   │   └── token_revocation.py    # Phase 1: Widerruf-Mechanismus
│   ├── audit/
│   │   ├── __init__.py
│   │   └── capability_logger.py   # Phase 2: Hashline-Integration
│   ├── gates/
│   │   ├── __init__.py
│   │   ├── mcp_tool_gate.py       # Phase 3: Pre-Execution-Prüfung
│   │   └── memory_gate.py         # Phase 4: Memory-Tier-Zugriffskontrolle
│   ├── trust/
│   │   ├── __init__.py
│   │   └── dynamic_scorer.py      # Phase 6: Dynamische Vertrauensbewertung
│   ├── a2a/
│   │   ├── __init__.py
│   │   ├── spiffe_bridge.py       # Phase 5: SPIFFE-Translation
│   │   └── trust_boundary.py      # Phase 5: Externe Trust-Grenze
│   ├── config.py                  # Zentrale AACS-Konfiguration
│   └── exceptions.py              # AACS-spezifische Exceptions
├── tests/
│   └── aacs/
│       ├── test_capability_token.py
│       ├── test_token_issuer.py
│       ├── test_token_validator.py
│       ├── test_token_revocation.py
│       ├── test_capability_logger.py
│       ├── test_mcp_tool_gate.py
│       ├── test_memory_gate.py
│       ├── test_dynamic_scorer.py
│       ├── test_spiffe_bridge.py
│       └── test_integration_pge_flow.py
```

**Anweisung an Coding-Modell:** Prüfe, ob ein `aacs/`-Verzeichnis bereits existiert. Falls ja, mappe vorhandene Dateien auf diese Struktur. Falls nein, erstelle die komplette Struktur.

---

## 3. Phase 1 – Capability Token Core <a id="3-phase-1"></a>

### 3.1 Abhängigkeiten prüfen

```bash
# Prüfe ob diese Pakete verfügbar sind
pip show pynacl       # Ed25519 via libsodium
pip show pydantic     # Datenvalidierung
pip show cryptography # Fallback für Ed25519
```

Falls `pynacl` nicht vorhanden, nutze `cryptography.hazmat.primitives.asymmetric.ed25519`.

### 3.2 Konfiguration

**Datei: `cognithor/aacs/config.py`**

```python
"""
AACS Zentrale Konfiguration.
Alle Zeitwerte, Limits und Defaults für das Access Control System.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AACSConfig:
    """Unveränderliche Konfiguration für AACS."""

    # Token-Zeitlimits (Sekunden)
    default_token_ttl: int = 300          # 5 Minuten Standard
    max_token_ttl: int = 3600             # 1 Stunde Maximum
    min_token_ttl: int = 10               # 10 Sekunden Minimum

    # Delegations-Limits
    max_delegation_depth: int = 5         # Maximale Kette Planner→...→Executor
    max_active_tokens_per_agent: int = 50 # Speicher-Schutz

    # Nonce-Speicher für Replay-Schutz
    nonce_cache_size: int = 10_000
    nonce_expiry_seconds: int = 7200      # 2 Stunden

    # Trust-Score-Grenzen (Phase 6)
    trust_score_min: float = 0.0
    trust_score_max: float = 1.0
    trust_score_initial: float = 0.5
    trust_decay_rate: float = 0.01        # Pro Stunde Inaktivität

    # Memory-Tier-Definitionen
    memory_tiers: dict[int, str] = field(default_factory=lambda: {
        1: "working",       # Arbeitsspeicher – jeder Executor
        2: "task",          # Aufgabenkontext – zugewiesener Executor
        3: "session",       # Sitzungswissen – Gatekeeper + autorisiert
        4: "knowledge",     # Wissensspeicher – Planner + Gatekeeper
        5: "system_config", # Systemkonfiguration – Planner + Operator
    })

    # Pfade
    key_store_path: Path = Path("~/.cognithor/keys").expanduser()

    def validate(self) -> None:
        """Prüft Konfigurationskonsistenz."""
        assert self.min_token_ttl > 0, "min_token_ttl muss > 0 sein"
        assert self.min_token_ttl <= self.default_token_ttl <= self.max_token_ttl
        assert self.max_delegation_depth >= 1
        assert 0.0 <= self.trust_score_initial <= 1.0


# Singleton – importierbar als `from cognithor.aacs.config import AACS_CONFIG`
AACS_CONFIG = AACSConfig()
```

### 3.3 Exceptions

**Datei: `cognithor/aacs/exceptions.py`**

```python
"""AACS-spezifische Exceptions."""


class AACSError(Exception):
    """Basis-Exception für alle AACS-Fehler."""


class TokenExpiredError(AACSError):
    """Token ist abgelaufen."""


class TokenInvalidSignatureError(AACSError):
    """Signatur des Tokens ist ungültig."""


class TokenRevokedError(AACSError):
    """Token wurde widerrufen."""


class PrivilegeEscalationError(AACSError):
    """Versuch einer Rechteeskalation erkannt."""


class DelegationDepthExceededError(AACSError):
    """Maximale Delegationstiefe überschritten."""


class InsufficientPermissionError(AACSError):
    """Agent hat nicht die erforderlichen Rechte."""


class ReplayAttackDetectedError(AACSError):
    """Replay-Angriff erkannt: Nonce wurde bereits verwendet."""


class MemoryTierAccessDeniedError(AACSError):
    """Zugriff auf diese Memory-Tier verweigert."""


class DualSignatureRequiredError(AACSError):
    """Tier-5-Zugriff erfordert zusätzliche Operator-Signatur."""
```

### 3.4 Capability Token Datenmodell

**Datei: `cognithor/aacs/tokens/capability_token.py`**

```python
"""
Capability Token – Kernbaustein des AACS.

Ein Token kodiert exakt, was ein Agent tun darf.
Tokens können nur eingeschränkt (attenuiert), nie erweitert werden.

Design-Prinzipien:
- Unfälschbar: Ed25519-signiert
- Kurzlebig: TTL von 10-3600 Sekunden
- Attenuation-only: Sub-Tokens können nie mehr Rechte haben als der Eltern-Token
- Replay-geschützt: Einmalige Nonce
"""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Self


class ActionVerb(str, Enum):
    """Erlaubte Aktions-Verben für Capability Tokens."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELEGATE = "delegate"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass(frozen=True)
class Action:
    """
    Eine spezifische erlaubte Aktion.

    Beispiele:
        Action(resource="mcp.tool.web_search", verb=ActionVerb.EXECUTE)
        Action(resource="memory.tier.2", verb=ActionVerb.READ)
        Action(resource="vault.insurance.bav.*", verb=ActionVerb.READ)
    """
    resource: str         # Ressourcen-Muster (unterstützt Wildcards mit *)
    verb: ActionVerb

    def matches(self, requested_resource: str, requested_verb: ActionVerb) -> bool:
        """Prüft ob diese Action die angeforderte Aktion abdeckt."""
        if self.verb != requested_verb:
            return False
        return self._resource_matches(self.resource, requested_resource)

    @staticmethod
    def _resource_matches(pattern: str, target: str) -> bool:
        """Wildcard-Matching für Ressourcen-Pfade."""
        if pattern == "*":
            return True
        if pattern == target:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return target == prefix or target.startswith(prefix + ".")
        return False

    def is_subset_of(self, parent: Action) -> bool:
        """Prüft ob diese Action eine Teilmenge der Eltern-Action ist."""
        if not parent.matches(self.resource, self.verb):
            # Prüfe ob das Verb gleich ist und die Ressource spezifischer
            if self.verb != parent.verb:
                return False
            return self._resource_matches(parent.resource, self.resource)
        return True


@dataclass(frozen=True)
class CapabilityToken:
    """
    Unfälschbarer Capability Token für Agent-Autorisierung.

    WICHTIG: Dieses Objekt ist immutable (frozen=True).
    Änderungen erfordern Erstellung eines neuen Tokens.
    """

    # ── Identität ──
    token_id: str                           # Eindeutige Token-ID (UUID oder ähnlich)
    issuer_did: str                         # DID des ausstellenden Agents
    subject_did: str                        # DID des berechtigten Agents

    # ── Berechtigungen ──
    allowed_actions: tuple[Action, ...]     # Erlaubte Aktionen (tuple für immutability)
    denied_actions: tuple[Action, ...] = () # Explizite Verbote (überschreiben allowed)
    max_delegation_depth: int = 0           # 0 = darf nicht weiter delegieren

    # ── Scope-Einschränkungen ──
    memory_tier_ceiling: int = 1            # Höchste erlaubte Memory-Tier (1-5)
    resource_patterns: tuple[str, ...] = () # Zusätzliche Ressourcen-Muster

    # ── Zeitliche Einschränkungen ──
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None      # None = nutze Default-TTL aus Config
    nonce: str = field(default_factory=lambda: secrets.token_hex(16))

    # ── Vertrauenskette ──
    parent_token_hash: str | None = None    # Hash des Eltern-Tokens (None = Root)
    delegation_depth: int = 0               # Aktuelle Tiefe in der Kette

    # ── Kryptographie (wird beim Signieren gesetzt) ──
    signature: bytes = b""                  # Ed25519-Signatur über den Payload

    @property
    def is_root_token(self) -> bool:
        """Ist dies ein Root-Token (direkt vom Planner ausgestellt)?"""
        return self.parent_token_hash is None

    @property
    def is_expired(self) -> bool:
        """Ist das Token abgelaufen?"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_signed(self) -> bool:
        """Wurde das Token signiert?"""
        return len(self.signature) > 0

    def payload_bytes(self) -> bytes:
        """
        Serialisiert den Token-Payload für Signierung.
        WICHTIG: Signatur selbst ist NICHT Teil des Payloads.
        """
        payload = {
            "token_id": self.token_id,
            "issuer_did": self.issuer_did,
            "subject_did": self.subject_did,
            "allowed_actions": [
                {"resource": a.resource, "verb": a.verb.value}
                for a in self.allowed_actions
            ],
            "denied_actions": [
                {"resource": a.resource, "verb": a.verb.value}
                for a in self.denied_actions
            ],
            "max_delegation_depth": self.max_delegation_depth,
            "memory_tier_ceiling": self.memory_tier_ceiling,
            "resource_patterns": list(self.resource_patterns),
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "nonce": self.nonce,
            "parent_token_hash": self.parent_token_hash,
            "delegation_depth": self.delegation_depth,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def compute_hash(self) -> str:
        """SHA-256-Hash des Token-Payloads (für Verkettung)."""
        return hashlib.sha256(self.payload_bytes()).hexdigest()

    def check_action_allowed(self, resource: str, verb: ActionVerb) -> bool:
        """
        Prüft ob eine Aktion durch diesen Token erlaubt ist.

        Logik:
        1. Wenn in denied_actions → VERWEIGERT
        2. Wenn in allowed_actions → ERLAUBT
        3. Sonst → VERWEIGERT (Default Deny)
        """
        # Deny-Liste hat Vorrang
        for denied in self.denied_actions:
            if denied.matches(resource, verb):
                return False

        # Dann Allow-Liste prüfen
        for allowed in self.allowed_actions:
            if allowed.matches(resource, verb):
                return True

        # Default: Verweigern
        return False

    def can_delegate(self) -> bool:
        """Darf dieser Token-Inhaber Sub-Tokens erstellen?"""
        return self.max_delegation_depth > 0

    def validate_subtokens_attenuation(self, child: CapabilityToken) -> bool:
        """
        Prüft ob ein Kind-Token eine gültige Attenuation dieses Tokens ist.

        Regeln:
        - Kind darf NICHT mehr Rechte haben als Eltern
        - Kind darf NICHT höhere Memory-Tier haben
        - Kind darf NICHT größere Delegationstiefe haben
        - Kind muss kürzer oder gleich lang gültig sein
        """
        # Memory-Tier darf nicht steigen
        if child.memory_tier_ceiling > self.memory_tier_ceiling:
            return False

        # Delegationstiefe darf nicht steigen
        if child.max_delegation_depth >= self.max_delegation_depth:
            return False

        # Delegation Depth muss Eltern + 1 sein
        if child.delegation_depth != self.delegation_depth + 1:
            return False

        # Laufzeit darf nicht länger sein
        if self.expires_at and child.expires_at:
            if child.expires_at > self.expires_at:
                return False

        # Jede Kind-Aktion muss Teilmenge einer Eltern-Aktion sein
        for child_action in child.allowed_actions:
            is_covered = any(
                child_action.is_subset_of(parent_action)
                for parent_action in self.allowed_actions
            )
            if not is_covered:
                return False

        # Parent-Token-Hash muss stimmen
        if child.parent_token_hash != self.compute_hash():
            return False

        return True
```

### 3.5 Token Issuer

**Datei: `cognithor/aacs/tokens/token_issuer.py`**

```python
"""
Token Issuer – Erstellt und signiert Capability Tokens.

Der Issuer ist an einen bestimmten Agent (DID) gebunden und
nutzt dessen Ed25519-Schlüssel zum Signieren.

Verwendung:
    issuer = TokenIssuer(agent_did="did:cognithor:planner-001", signing_key=key)
    token = issuer.issue_root_token(subject_did="did:cognithor:gatekeeper-001", ...)
    sub_token = issuer.delegate(parent_token=token, subject_did="did:cognithor:executor-042", ...)
"""
from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Sequence

from cognithor.aacs.config import AACS_CONFIG
from cognithor.aacs.exceptions import (
    DelegationDepthExceededError,
    PrivilegeEscalationError,
)
from cognithor.aacs.tokens.capability_token import (
    Action,
    CapabilityToken,
)

# ── ANWEISUNG AN CODING-MODELL ──
# Prüfe wie Ed25519 im Projekt implementiert ist.
# Möglichkeit 1: PyNaCl (bevorzugt)
#   from nacl.signing import SigningKey, VerifyKey
# Möglichkeit 2: cryptography
#   from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
#
# Passe den Import und die sign()-Aufrufe entsprechend an.
# Suche im Codebase nach bestehenden Signing-Utilities und nutze diese.

try:
    from nacl.signing import SigningKey
    CRYPTO_BACKEND = "pynacl"
except ImportError:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey as SigningKey,
    )
    CRYPTO_BACKEND = "cryptography"


class TokenIssuer:
    """Erstellt und signiert Capability Tokens für einen Agent."""

    def __init__(self, agent_did: str, signing_key: SigningKey) -> None:
        self._agent_did = agent_did
        self._signing_key = signing_key

    @property
    def agent_did(self) -> str:
        return self._agent_did

    def _sign_token(self, token: CapabilityToken) -> CapabilityToken:
        """Signiert einen Token mit dem Ed25519-Schlüssel des Issuers."""
        payload = token.payload_bytes()

        if CRYPTO_BACKEND == "pynacl":
            signed = self._signing_key.sign(payload)
            signature = signed.signature
        else:
            signature = self._signing_key.sign(payload)

        # Frozen dataclass → replace() für neues Objekt
        return replace(token, signature=signature)

    def issue_root_token(
        self,
        subject_did: str,
        allowed_actions: Sequence[Action],
        denied_actions: Sequence[Action] = (),
        max_delegation_depth: int = 0,
        memory_tier_ceiling: int = 1,
        resource_patterns: Sequence[str] = (),
        ttl_seconds: int | None = None,
    ) -> CapabilityToken:
        """
        Erstellt einen Root-Token (kein Eltern-Token).

        Nur der Planner sollte Root-Tokens erstellen.
        """
        ttl = ttl_seconds or AACS_CONFIG.default_token_ttl
        ttl = max(AACS_CONFIG.min_token_ttl, min(ttl, AACS_CONFIG.max_token_ttl))

        now = datetime.now(timezone.utc)

        token = CapabilityToken(
            token_id=str(uuid.uuid4()),
            issuer_did=self._agent_did,
            subject_did=subject_did,
            allowed_actions=tuple(allowed_actions),
            denied_actions=tuple(denied_actions),
            max_delegation_depth=max_delegation_depth,
            memory_tier_ceiling=memory_tier_ceiling,
            resource_patterns=tuple(resource_patterns),
            issued_at=now,
            expires_at=now + timedelta(seconds=ttl),
            parent_token_hash=None,
            delegation_depth=0,
        )

        return self._sign_token(token)

    def delegate(
        self,
        parent_token: CapabilityToken,
        subject_did: str,
        allowed_actions: Sequence[Action],
        denied_actions: Sequence[Action] = (),
        max_delegation_depth: int = 0,
        memory_tier_ceiling: int | None = None,
        resource_patterns: Sequence[str] = (),
        ttl_seconds: int | None = None,
    ) -> CapabilityToken:
        """
        Erstellt einen Sub-Token durch Delegation.

        Prüft automatisch:
        - Darf der Eltern-Token delegieren?
        - Ist die maximale Delegationstiefe erreicht?
        - Ist der Sub-Token eine gültige Attenuation?

        Raises:
            DelegationDepthExceededError: Maximale Tiefe überschritten
            PrivilegeEscalationError: Sub-Token hat mehr Rechte als Eltern
        """
        # Prüfe Delegationsrecht
        if not parent_token.can_delegate():
            raise DelegationDepthExceededError(
                f"Token {parent_token.token_id} darf nicht delegieren "
                f"(max_delegation_depth={parent_token.max_delegation_depth})"
            )

        if parent_token.delegation_depth + 1 > AACS_CONFIG.max_delegation_depth:
            raise DelegationDepthExceededError(
                f"Globale maximale Delegationstiefe "
                f"({AACS_CONFIG.max_delegation_depth}) erreicht"
            )

        # Memory-Tier-Ceiling begrenzen
        effective_tier = min(
            memory_tier_ceiling or parent_token.memory_tier_ceiling,
            parent_token.memory_tier_ceiling,
        )

        # TTL begrenzen auf Eltern-Restlaufzeit
        now = datetime.now(timezone.utc)
        parent_remaining = (parent_token.expires_at - now).total_seconds()
        ttl = ttl_seconds or AACS_CONFIG.default_token_ttl
        ttl = min(ttl, parent_remaining, AACS_CONFIG.max_token_ttl)
        ttl = max(ttl, AACS_CONFIG.min_token_ttl)

        child_token = CapabilityToken(
            token_id=str(uuid.uuid4()),
            issuer_did=self._agent_did,
            subject_did=subject_did,
            allowed_actions=tuple(allowed_actions),
            denied_actions=tuple(denied_actions),
            max_delegation_depth=min(
                max_delegation_depth,
                parent_token.max_delegation_depth - 1,
            ),
            memory_tier_ceiling=effective_tier,
            resource_patterns=tuple(resource_patterns),
            issued_at=now,
            expires_at=now + timedelta(seconds=ttl),
            parent_token_hash=parent_token.compute_hash(),
            delegation_depth=parent_token.delegation_depth + 1,
        )

        # Attenuation-Prüfung
        if not parent_token.validate_subtokens_attenuation(child_token):
            raise PrivilegeEscalationError(
                f"Sub-Token für {subject_did} würde die Rechte von "
                f"Token {parent_token.token_id} überschreiten"
            )

        return self._sign_token(child_token)
```

### 3.6 Token Validator

**Datei: `cognithor/aacs/tokens/token_validator.py`**

```python
"""
Token Validator – Verifiziert Capability Tokens.

Prüft:
1. Ed25519-Signatur
2. Ablaufzeit
3. Nonce (Replay-Schutz)
4. Widerrufsstatus
5. Delegationskette

ANWEISUNG AN CODING-MODELL:
- Prüfe ob im Projekt bereits ein VerifyKey-Cache existiert
- Prüfe ob ein DID-Resolver existiert (DID → Public Key)
- Falls ja, integriere diese. Falls nein, implementiere den Resolver.
"""
from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from cognithor.aacs.config import AACS_CONFIG
from cognithor.aacs.exceptions import (
    ReplayAttackDetectedError,
    TokenExpiredError,
    TokenInvalidSignatureError,
    TokenRevokedError,
)
from cognithor.aacs.tokens.capability_token import CapabilityToken

# ── ANWEISUNG AN CODING-MODELL ──
# Passe Import an den verwendeten Crypto-Backend an (siehe token_issuer.py)
try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
    CRYPTO_BACKEND = "pynacl"
except ImportError:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey as VerifyKey,
    )
    from cryptography.exceptions import InvalidSignature as BadSignatureError
    CRYPTO_BACKEND = "cryptography"


class NonceCache:
    """
    LRU-Cache für verwendete Nonces (Replay-Schutz).

    ANWEISUNG AN CODING-MODELL:
    Falls Redis oder ein anderer Cache im Projekt verfügbar ist,
    ersetze diese In-Memory-Implementierung durch einen persistenten Cache.
    """

    def __init__(self, max_size: int = AACS_CONFIG.nonce_cache_size) -> None:
        self._cache: OrderedDict[str, float] = OrderedDict()
        self._max_size = max_size

    def check_and_store(self, nonce: str) -> bool:
        """
        Prüft ob Nonce bereits verwendet und speichert sie.
        Returns: True wenn Nonce neu ist, False wenn Replay.
        """
        now = time.time()
        self._evict_expired(now)

        if nonce in self._cache:
            return False  # Replay!

        self._cache[nonce] = now
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)  # Ältesten entfernen

        return True

    def _evict_expired(self, now: float) -> None:
        """Entferne abgelaufene Nonces."""
        cutoff = now - AACS_CONFIG.nonce_expiry_seconds
        while self._cache:
            oldest_nonce, oldest_time = next(iter(self._cache.items()))
            if oldest_time < cutoff:
                self._cache.popitem(last=False)
            else:
                break


class RevokedTokenStore:
    """
    Speicher für widerrufene Token-IDs.

    ANWEISUNG AN CODING-MODELL:
    Falls eine Datenbank (SQLite, PostgreSQL) im Projekt vorhanden ist,
    nutze diese für Persistenz. Sonst In-Memory mit Warnung im Log.
    """

    def __init__(self) -> None:
        self._revoked: set[str] = set()

    def revoke(self, token_id: str) -> None:
        self._revoked.add(token_id)

    def is_revoked(self, token_id: str) -> bool:
        return token_id in self._revoked


# ── ANWEISUNG AN CODING-MODELL ──
# Erstelle eine Klasse oder Funktion die DID → VerifyKey auflöst.
# Prüfe ob im Projekt bereits ein DID-Registry oder Agent-Registry existiert.
# Falls ja, wrappe diese. Falls nein, erstelle eine einfache Dict-basierte Registry.

class DIDResolver:
    """
    Löst DIDs zu Ed25519-VerifyKeys auf.

    ANWEISUNG AN CODING-MODELL:
    Integriere dies mit dem bestehenden DID/Agent-Registry-System.
    """

    def __init__(self) -> None:
        self._registry: dict[str, VerifyKey] = {}

    def register(self, did: str, verify_key: VerifyKey) -> None:
        """Registriert einen Agent-DID mit seinem öffentlichen Schlüssel."""
        self._registry[did] = verify_key

    def resolve(self, did: str) -> VerifyKey | None:
        """Löst DID zu VerifyKey auf. None wenn unbekannt."""
        return self._registry.get(did)


@dataclass
class ValidationResult:
    """Ergebnis einer Token-Validierung."""
    valid: bool
    token: CapabilityToken | None = None
    error: str = ""
    error_type: str = ""  # Fehlerklasse für Audit-Log


class TokenValidator:
    """Vollständige Token-Validierung mit allen Sicherheitsprüfungen."""

    def __init__(
        self,
        did_resolver: DIDResolver,
        nonce_cache: NonceCache | None = None,
        revoked_store: RevokedTokenStore | None = None,
    ) -> None:
        self._did_resolver = did_resolver
        self._nonce_cache = nonce_cache or NonceCache()
        self._revoked_store = revoked_store or RevokedTokenStore()

    def validate(self, token: CapabilityToken) -> ValidationResult:
        """
        Vollständige Validierung eines Capability Tokens.

        Prüfungsreihenfolge (fail-fast):
        1. Signatur (kryptographisch)
        2. Ablaufzeit
        3. Nonce (Replay)
        4. Widerruf
        """
        # 1. Signatur prüfen
        verify_key = self._did_resolver.resolve(token.issuer_did)
        if verify_key is None:
            return ValidationResult(
                valid=False,
                error=f"Unbekannter Issuer-DID: {token.issuer_did}",
                error_type="UNKNOWN_ISSUER",
            )

        try:
            if CRYPTO_BACKEND == "pynacl":
                verify_key.verify(token.payload_bytes(), token.signature)
            else:
                verify_key.verify(token.signature, token.payload_bytes())
        except BadSignatureError:
            return ValidationResult(
                valid=False,
                error=f"Ungültige Signatur für Token {token.token_id}",
                error_type="INVALID_SIGNATURE",
            )

        # 2. Ablaufzeit prüfen
        if token.is_expired:
            return ValidationResult(
                valid=False,
                error=f"Token {token.token_id} abgelaufen um {token.expires_at}",
                error_type="EXPIRED",
            )

        # 3. Nonce prüfen (Replay-Schutz)
        if not self._nonce_cache.check_and_store(token.nonce):
            return ValidationResult(
                valid=False,
                error=f"Replay erkannt: Nonce {token.nonce[:8]}... bereits verwendet",
                error_type="REPLAY_ATTACK",
            )

        # 4. Widerruf prüfen
        if self._revoked_store.is_revoked(token.token_id):
            return ValidationResult(
                valid=False,
                error=f"Token {token.token_id} wurde widerrufen",
                error_type="REVOKED",
            )

        return ValidationResult(valid=True, token=token)

    def revoke_token(self, token_id: str) -> None:
        """Widerruft einen Token (ab sofort ungültig)."""
        self._revoked_store.revoke(token_id)
```

---

## 4. Phase 2 – Hashline Guard Integration <a id="4-phase-2"></a>

**Datei: `cognithor/aacs/audit/capability_logger.py`**

```python
"""
Capability Logger – Hashline Guard Integration für AACS.

Jede Token-Aktion (Erstellung, Nutzung, Ablehnung, Widerruf)
wird als fälschungssicherer Eintrag im Hashline Guard protokolliert.

ANWEISUNG AN CODING-MODELL:
1. Finde die bestehende Hashline Guard Implementierung:
   grep -rn "class HashlineGuard\|class Hashline\|hashline" --include="*.py" .
2. Prüfe das Interface: Welche Methode wird zum Hinzufügen verwendet?
   Vermutlich: add_entry(), append(), log() oder ähnlich.
3. Passe die Aufrufe unten an das tatsächliche Interface an.
4. Prüfe ob HMAC bereits im Hashline Guard integriert ist.
   Falls ja, nutze die bestehende Implementierung.
   Falls nein, füge HMAC hier hinzu.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CapabilityEventType(str, Enum):
    """Typen von AACS-Events für das Audit-Log."""
    TOKEN_GRANTED = "TOKEN_GRANTED"
    TOKEN_USED = "TOKEN_USED"
    TOKEN_DENIED = "TOKEN_DENIED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    ESCALATION_BLOCKED = "ESCALATION_BLOCKED"
    DELEGATION_CREATED = "DELEGATION_CREATED"
    MEMORY_ACCESS_GRANTED = "MEMORY_ACCESS_GRANTED"
    MEMORY_ACCESS_DENIED = "MEMORY_ACCESS_DENIED"
    MCP_TOOL_ALLOWED = "MCP_TOOL_ALLOWED"
    MCP_TOOL_BLOCKED = "MCP_TOOL_BLOCKED"
    DUAL_SIGNATURE_REQUIRED = "DUAL_SIGNATURE_REQUIRED"


@dataclass(frozen=True)
class CapabilityAuditEntry:
    """Ein einzelner AACS-Audit-Eintrag für den Hashline Guard."""
    previous_hash: str
    timestamp: datetime
    event_type: CapabilityEventType
    token_id: str
    actor_did: str
    action_attempted: str
    resource: str
    result: str          # "ALLOWED" | "DENIED" | Fehlerdetail
    metadata: dict[str, Any]  # Zusätzliche Kontextinformationen
    entry_hash: str = ""
    hmac_signature: bytes = b""

    def compute_hash(self) -> str:
        """Berechnet den Hash dieses Eintrags (für Verkettung)."""
        payload = {
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "token_id": self.token_id,
            "actor_did": self.actor_did,
            "action_attempted": self.action_attempted,
            "resource": self.resource,
            "result": self.result,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()


class CapabilityLogger:
    """
    Protokolliert alle AACS-Events im Hashline Guard.

    ANWEISUNG AN CODING-MODELL:
    Ersetze self._hashline_guard mit der tatsächlichen
    Hashline Guard Instanz aus dem Projekt.
    """

    def __init__(self, hmac_key: bytes, hashline_guard: Any = None) -> None:
        """
        Args:
            hmac_key: Geheimer Schlüssel für HMAC-Integrität
            hashline_guard: Bestehende Hashline Guard Instanz
                           (None = eigenständiger Betrieb mit internem Log)
        """
        self._hmac_key = hmac_key
        self._hashline_guard = hashline_guard
        self._chain: list[CapabilityAuditEntry] = []
        self._last_hash = "0" * 64  # Genesis-Hash

    def log_event(
        self,
        event_type: CapabilityEventType,
        token_id: str,
        actor_did: str,
        action_attempted: str,
        resource: str,
        result: str,
        metadata: dict[str, Any] | None = None,
    ) -> CapabilityAuditEntry:
        """
        Protokolliert ein AACS-Event.

        Returns:
            Der erstellte und signierte Audit-Eintrag.
        """
        entry = CapabilityAuditEntry(
            previous_hash=self._last_hash,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            token_id=token_id,
            actor_did=actor_did,
            action_attempted=action_attempted,
            resource=resource,
            result=result,
            metadata=metadata or {},
        )

        # Hash berechnen
        entry_hash = entry.compute_hash()

        # HMAC berechnen
        hmac_sig = hmac.new(
            self._hmac_key,
            entry_hash.encode(),
            hashlib.sha256,
        ).digest()

        from dataclasses import replace
        entry = replace(entry, entry_hash=entry_hash, hmac_signature=hmac_sig)

        # In Kette einfügen
        self._last_hash = entry_hash
        self._chain.append(entry)

        # An Hashline Guard weiterleiten falls vorhanden
        if self._hashline_guard is not None:
            # ANWEISUNG: Passe diesen Aufruf an das tatsächliche Interface an
            # self._hashline_guard.add_entry(entry)
            pass

        return entry

    def verify_chain_integrity(self) -> bool:
        """Prüft die Integrität der gesamten Audit-Kette."""
        if not self._chain:
            return True

        expected_previous = "0" * 64
        for entry in self._chain:
            # Previous-Hash prüfen
            if entry.previous_hash != expected_previous:
                return False

            # Entry-Hash prüfen
            if entry.compute_hash() != entry.entry_hash:
                return False

            # HMAC prüfen
            expected_hmac = hmac.new(
                self._hmac_key,
                entry.entry_hash.encode(),
                hashlib.sha256,
            ).digest()
            if not hmac.compare_digest(entry.hmac_signature, expected_hmac):
                return False

            expected_previous = entry.entry_hash

        return True

    def get_events_for_agent(self, agent_did: str) -> list[CapabilityAuditEntry]:
        """Alle Events für einen bestimmten Agent (GDPR-relevant)."""
        return [e for e in self._chain if e.actor_did == agent_did]

    def get_events_for_token(self, token_id: str) -> list[CapabilityAuditEntry]:
        """Alle Events für einen bestimmten Token."""
        return [e for e in self._chain if e.token_id == token_id]
```

---

## 5. Phase 3 – MCP Tool Gate <a id="5-phase-3"></a>

**Datei: `cognithor/aacs/gates/mcp_tool_gate.py`**

```python
"""
MCP Tool Gate – Pre-Execution Berechtigungsprüfung für MCP-Tools.

Wird VOR jedem MCP-Tool-Aufruf ausgeführt.
Prüft ob der aufrufende Agent einen gültigen Token hat
der die Ausführung dieses spezifischen Tools erlaubt.

ANWEISUNG AN CODING-MODELL:
1. Finde die Stelle wo MCP-Tools aktuell aufgerufen werden:
   grep -rn "tool_execute\|execute_tool\|run_tool\|call_tool" --include="*.py" .
2. Finde die Tool-Registry:
   grep -rn "ToolRegistry\|tool_registry\|registered_tools" --include="*.py" .
3. Integriere den MCPToolGate als Middleware/Decorator VOR dem Tool-Aufruf.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from cognithor.aacs.audit.capability_logger import (
    CapabilityEventType,
    CapabilityLogger,
)
from cognithor.aacs.exceptions import InsufficientPermissionError
from cognithor.aacs.tokens.capability_token import ActionVerb, CapabilityToken
from cognithor.aacs.tokens.token_validator import TokenValidator, ValidationResult


@dataclass
class ToolExecutionRequest:
    """Anfrage zur Ausführung eines MCP-Tools."""
    tool_name: str                  # z.B. "web_search", "db_query"
    tool_namespace: str             # z.B. "mcp.tool"
    parameters: dict[str, Any]      # Tool-Parameter
    caller_did: str                 # DID des aufrufenden Agents
    capability_token: CapabilityToken  # Berechtigungstoken

    @property
    def resource_path(self) -> str:
        """Vollständiger Ressourcenpfad für Permission-Check."""
        return f"{self.tool_namespace}.{self.tool_name}"


@dataclass
class ToolExecutionResult:
    """Ergebnis einer Tool-Ausführung (inkl. Access-Control-Metadaten)."""
    allowed: bool
    result: Any = None
    error: str = ""
    token_validation: ValidationResult | None = None


class MCPToolGate:
    """
    Gate zwischen Agent und MCP-Tool-Ausführung.

    Verwendung als Middleware:
        gate = MCPToolGate(validator=validator, logger=logger)

        # Vor jedem Tool-Aufruf:
        result = gate.execute(request)
        if not result.allowed:
            handle_denied(result)
    """

    def __init__(
        self,
        validator: TokenValidator,
        logger: CapabilityLogger,
    ) -> None:
        self._validator = validator
        self._logger = logger

        # Optionale Tool-spezifische Einschränkungen
        # z.B. {"db_write": ActionVerb.WRITE, "db_read": ActionVerb.READ}
        self._tool_verb_mapping: dict[str, ActionVerb] = {}

    def register_tool_verb(self, tool_name: str, required_verb: ActionVerb) -> None:
        """
        Registriert welches Verb ein Tool benötigt.
        Default: EXECUTE für alle Tools.
        """
        self._tool_verb_mapping[tool_name] = required_verb

    def check_permission(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """
        Prüft ob der Agent das Tool ausführen darf (OHNE es auszuführen).
        """
        # 1. Token validieren
        validation = self._validator.validate(request.capability_token)
        if not validation.valid:
            self._logger.log_event(
                event_type=CapabilityEventType.MCP_TOOL_BLOCKED,
                token_id=request.capability_token.token_id,
                actor_did=request.caller_did,
                action_attempted=f"execute:{request.tool_name}",
                resource=request.resource_path,
                result=f"DENIED: {validation.error}",
            )
            return ToolExecutionResult(
                allowed=False,
                error=validation.error,
                token_validation=validation,
            )

        # 2. Aktion im Token prüfen
        required_verb = self._tool_verb_mapping.get(
            request.tool_name, ActionVerb.EXECUTE
        )
        if not request.capability_token.check_action_allowed(
            request.resource_path, required_verb
        ):
            error_msg = (
                f"Token {request.capability_token.token_id} erlaubt nicht "
                f"{required_verb.value} auf {request.resource_path}"
            )
            self._logger.log_event(
                event_type=CapabilityEventType.MCP_TOOL_BLOCKED,
                token_id=request.capability_token.token_id,
                actor_did=request.caller_did,
                action_attempted=f"{required_verb.value}:{request.tool_name}",
                resource=request.resource_path,
                result=f"DENIED: {error_msg}",
            )
            return ToolExecutionResult(allowed=False, error=error_msg)

        # 3. Token-Subject muss der Aufrufer sein
        if request.capability_token.subject_did != request.caller_did:
            error_msg = (
                f"Token subject ({request.capability_token.subject_did}) "
                f"stimmt nicht mit caller ({request.caller_did}) überein"
            )
            self._logger.log_event(
                event_type=CapabilityEventType.ESCALATION_BLOCKED,
                token_id=request.capability_token.token_id,
                actor_did=request.caller_did,
                action_attempted=f"impersonation:{request.tool_name}",
                resource=request.resource_path,
                result=f"DENIED: {error_msg}",
            )
            return ToolExecutionResult(allowed=False, error=error_msg)

        # Erlaubt
        self._logger.log_event(
            event_type=CapabilityEventType.MCP_TOOL_ALLOWED,
            token_id=request.capability_token.token_id,
            actor_did=request.caller_did,
            action_attempted=f"{required_verb.value}:{request.tool_name}",
            resource=request.resource_path,
            result="ALLOWED",
        )
        return ToolExecutionResult(allowed=True)

    def execute_guarded(
        self,
        request: ToolExecutionRequest,
        tool_function: Callable[..., Any],
    ) -> ToolExecutionResult:
        """
        Prüft Berechtigung UND führt das Tool aus falls erlaubt.

        ANWEISUNG AN CODING-MODELL:
        Dies ist die Hauptmethode für die Integration.
        Wrape bestehende Tool-Aufrufe mit dieser Methode.
        """
        permission_result = self.check_permission(request)
        if not permission_result.allowed:
            return permission_result

        try:
            result = tool_function(**request.parameters)
            return ToolExecutionResult(allowed=True, result=result)
        except Exception as e:
            return ToolExecutionResult(
                allowed=True,
                error=f"Tool-Ausführungsfehler: {e}",
            )
```

---

## 6. Phase 4 – Memory Tier Access Control <a id="6-phase-4"></a>

**Datei: `cognithor/aacs/gates/memory_gate.py`**

```python
"""
Memory Tier Gate – Zugriffskontrolle für die 5-stufige kognitive Memory.

Tier-Hierarchie:
  Tier 1 (Working)      → Jeder Executor mit gültigem Token
  Tier 2 (Task)         → Nur der zugewiesene Executor
  Tier 3 (Session)      → Gatekeeper + autorisierte Executoren
  Tier 4 (Knowledge)    → Nur Planner + Gatekeeper
  Tier 5 (System Config) → Planner + Operator (Dual-Signatur erforderlich!)

ANWEISUNG AN CODING-MODELL:
1. Finde die Memory-Implementierung:
   grep -rn "class Memory\|class CognitiveMemory\|class MemoryStore" --include="*.py" .
2. Finde die read/write Methoden der Memory:
   grep -rn "def read\|def write\|def get\|def put\|def store" <memory_file>
3. Integriere MemoryGate als Wrapper um die bestehenden read/write Methoden.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cognithor.aacs.audit.capability_logger import (
    CapabilityEventType,
    CapabilityLogger,
)
from cognithor.aacs.exceptions import (
    DualSignatureRequiredError,
    InsufficientPermissionError,
    MemoryTierAccessDeniedError,
)
from cognithor.aacs.tokens.capability_token import ActionVerb, CapabilityToken
from cognithor.aacs.tokens.token_validator import TokenValidator


@dataclass
class MemoryAccessRequest:
    """Anfrage für Memory-Zugriff."""
    tier: int                       # 1-5
    key: str                        # Memory-Schlüssel
    verb: ActionVerb                # READ, WRITE, DELETE
    caller_did: str
    capability_token: CapabilityToken
    operator_signature: bytes | None = None  # Nur für Tier 5


class MemoryGate:
    """
    Kontrolliert Zugriff auf die kognitive Memory basierend auf Capability Tokens.

    Dual-Signatur für Tier 5:
    Tier 5 (System Config) erfordert ZUSÄTZLICH zur Agent-Signatur
    eine Operator-Signatur (Alexanders persönlicher Schlüssel).
    Dies verhindert, dass selbst ein kompromittierter Planner
    die Systemkonfiguration ändern kann.
    """

    def __init__(
        self,
        validator: TokenValidator,
        logger: CapabilityLogger,
        operator_verify_key: Any = None,  # Ed25519 VerifyKey des Operators
    ) -> None:
        self._validator = validator
        self._logger = logger
        self._operator_verify_key = operator_verify_key

    def check_access(self, request: MemoryAccessRequest) -> bool:
        """
        Prüft ob der Zugriff auf die angeforderte Memory-Tier erlaubt ist.

        Raises:
            MemoryTierAccessDeniedError: Zugriff verweigert
            DualSignatureRequiredError: Tier-5-Zugriff ohne Operator-Signatur
        """
        # 1. Token validieren
        validation = self._validator.validate(request.capability_token)
        if not validation.valid:
            self._logger.log_event(
                event_type=CapabilityEventType.MEMORY_ACCESS_DENIED,
                token_id=request.capability_token.token_id,
                actor_did=request.caller_did,
                action_attempted=f"memory.{request.verb.value}",
                resource=f"memory.tier.{request.tier}.{request.key}",
                result=f"DENIED: {validation.error}",
            )
            raise MemoryTierAccessDeniedError(validation.error)

        # 2. Memory-Tier-Ceiling prüfen
        if request.tier > request.capability_token.memory_tier_ceiling:
            error_msg = (
                f"Token erlaubt maximal Tier {request.capability_token.memory_tier_ceiling}, "
                f"angefordert: Tier {request.tier}"
            )
            self._logger.log_event(
                event_type=CapabilityEventType.MEMORY_ACCESS_DENIED,
                token_id=request.capability_token.token_id,
                actor_did=request.caller_did,
                action_attempted=f"memory.{request.verb.value}",
                resource=f"memory.tier.{request.tier}.{request.key}",
                result=f"DENIED: {error_msg}",
            )
            raise MemoryTierAccessDeniedError(error_msg)

        # 3. Aktions-Berechtigung prüfen
        resource = f"memory.tier.{request.tier}"
        if not request.capability_token.check_action_allowed(resource, request.verb):
            error_msg = (
                f"Token erlaubt nicht {request.verb.value} auf {resource}"
            )
            self._logger.log_event(
                event_type=CapabilityEventType.MEMORY_ACCESS_DENIED,
                token_id=request.capability_token.token_id,
                actor_did=request.caller_did,
                action_attempted=f"memory.{request.verb.value}",
                resource=f"memory.tier.{request.tier}.{request.key}",
                result=f"DENIED: {error_msg}",
            )
            raise MemoryTierAccessDeniedError(error_msg)

        # 4. Tier 5: Dual-Signatur prüfen
        if request.tier == 5 and request.verb in (ActionVerb.WRITE, ActionVerb.DELETE):
            if request.operator_signature is None:
                self._logger.log_event(
                    event_type=CapabilityEventType.DUAL_SIGNATURE_REQUIRED,
                    token_id=request.capability_token.token_id,
                    actor_did=request.caller_did,
                    action_attempted=f"memory.{request.verb.value}",
                    resource=f"memory.tier.5.{request.key}",
                    result="DENIED: Dual-Signatur erforderlich",
                )
                raise DualSignatureRequiredError(
                    "Tier-5-Schreibzugriff erfordert Operator-Signatur"
                )

            if not self._verify_operator_signature(request):
                self._logger.log_event(
                    event_type=CapabilityEventType.DUAL_SIGNATURE_REQUIRED,
                    token_id=request.capability_token.token_id,
                    actor_did=request.caller_did,
                    action_attempted=f"memory.{request.verb.value}",
                    resource=f"memory.tier.5.{request.key}",
                    result="DENIED: Ungültige Operator-Signatur",
                )
                raise DualSignatureRequiredError(
                    "Ungültige Operator-Signatur für Tier-5-Zugriff"
                )

        # Zugriff erlaubt
        self._logger.log_event(
            event_type=CapabilityEventType.MEMORY_ACCESS_GRANTED,
            token_id=request.capability_token.token_id,
            actor_did=request.caller_did,
            action_attempted=f"memory.{request.verb.value}",
            resource=f"memory.tier.{request.tier}.{request.key}",
            result="ALLOWED",
        )
        return True

    def _verify_operator_signature(self, request: MemoryAccessRequest) -> bool:
        """
        Prüft die Operator-Signatur für Tier-5-Zugriffe.

        ANWEISUNG AN CODING-MODELL:
        Implementiere die Verifikation mit dem Operator-VerifyKey.
        Der Operator-Key ist Alexanders persönlicher Ed25519-Schlüssel,
        der NICHT im Agent-System gespeichert wird.
        """
        if self._operator_verify_key is None:
            return False

        # TODO: Implementiere Signatur-Verifikation
        # Der signierte Payload sollte enthalten:
        # - token_id
        # - requested_tier
        # - requested_key
        # - requested_verb
        # - timestamp (frisch, max 60 Sekunden alt)
        return False  # Sicher: Default Deny
```

---

## 7. Phase 5 – A2A Gateway & SPIFFE Bridge <a id="7-phase-5"></a>

**Datei: `cognithor/aacs/a2a/trust_boundary.py`**

```python
"""
Trust Boundary – Grenze zwischen internem und externem Agent-Vertrauen.

ANWEISUNG AN CODING-MODELL:
1. Finde die A2A-Implementierung:
   grep -rn "a2a\|A2A\|AgentToAgent\|peer_agent" --include="*.py" .
2. Prüfe wie externe Agents aktuell authentifiziert werden.
3. Diese Klasse wird als Wrapper um die A2A-Kommunikation gesetzt.

Architektur:
  Intern: Ed25519 Capability Tokens (schnell, detailliert)
  Extern: mTLS + SPIFFE IDs (standardisiert, interoperabel)
  Gateway: Übersetzt zwischen beiden Welten
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class ExternalTrustLevel(Enum):
    """Vertrauensstufen für externe Agents."""
    UNTRUSTED = auto()      # Unbekannter Agent
    VERIFIED = auto()       # DID verifiziert, keine Historie
    TRUSTED = auto()        # Erfolgreiche Interaktionen
    PARTNER = auto()        # Vertraglich gebunden (z.B. andere Cognithor-Instanz)


@dataclass
class ExternalAgentIdentity:
    """Identität eines externen Agents an der Trust-Grenze."""
    external_did: str                    # DID des externen Agents
    spiffe_id: str | None = None         # SPIFFE ID falls vorhanden
    trust_level: ExternalTrustLevel = ExternalTrustLevel.UNTRUSTED
    verified_capabilities: list[str] = None  # Was der Agent nachweislich kann
    interaction_count: int = 0
    last_interaction_success: bool | None = None

    def __post_init__(self):
        if self.verified_capabilities is None:
            self.verified_capabilities = []


class TrustBoundary:
    """
    Kontrolliert Kommunikation zwischen internen und externen Agents.

    Regeln:
    - Externe Agents bekommen IMMER eingeschränkte Tokens
    - Externe Agents können NIEMALS auf Memory Tier 3+ zugreifen
    - Jede externe Kommunikation wird separat geloggt
    - Trust-Level steigt nur durch erfolgreiche Interaktionen

    ANWEISUNG AN CODING-MODELL:
    Integriere dies mit dem bestehenden A2A-Protokoll.
    Jede eingehende A2A-Nachricht muss durch die TrustBoundary.
    """

    # Maximale Berechtigungen pro Trust-Level
    TRUST_LEVEL_CEILINGS: dict[ExternalTrustLevel, dict[str, Any]] = {
        ExternalTrustLevel.UNTRUSTED: {
            "memory_tier_ceiling": 1,
            "max_delegation_depth": 0,
            "allowed_tool_namespaces": [],
            "max_token_ttl": 30,
        },
        ExternalTrustLevel.VERIFIED: {
            "memory_tier_ceiling": 1,
            "max_delegation_depth": 0,
            "allowed_tool_namespaces": ["mcp.tool.web_search"],
            "max_token_ttl": 60,
        },
        ExternalTrustLevel.TRUSTED: {
            "memory_tier_ceiling": 2,
            "max_delegation_depth": 0,
            "allowed_tool_namespaces": ["mcp.tool.*"],
            "max_token_ttl": 300,
        },
        ExternalTrustLevel.PARTNER: {
            "memory_tier_ceiling": 2,
            "max_delegation_depth": 1,
            "allowed_tool_namespaces": ["mcp.tool.*", "mcp.db.read"],
            "max_token_ttl": 600,
        },
    }

    def __init__(self, logger: Any = None) -> None:
        self._external_agents: dict[str, ExternalAgentIdentity] = {}
        self._logger = logger

    def register_external_agent(
        self, agent: ExternalAgentIdentity
    ) -> None:
        """Registriert einen externen Agent."""
        self._external_agents[agent.external_did] = agent

    def get_ceiling_for_agent(
        self, external_did: str
    ) -> dict[str, Any]:
        """
        Gibt die maximalen Berechtigungen für einen externen Agent zurück.
        Unbekannte Agents bekommen UNTRUSTED-Level.
        """
        agent = self._external_agents.get(external_did)
        if agent is None:
            return self.TRUST_LEVEL_CEILINGS[ExternalTrustLevel.UNTRUSTED]
        return self.TRUST_LEVEL_CEILINGS[agent.trust_level]

    def record_interaction_result(
        self, external_did: str, success: bool
    ) -> None:
        """
        Aktualisiert den Trust-Level basierend auf Interaktionsergebnis.

        ANWEISUNG AN CODING-MODELL:
        Implementiere die Trust-Level-Logik:
        - 5 erfolgreiche Interaktionen: UNTRUSTED → VERIFIED
        - 20 erfolgreiche Interaktionen: VERIFIED → TRUSTED
        - PARTNER nur manuell durch Operator
        - 3 aufeinanderfolgende Fehler: Downgrade um eine Stufe
        """
        agent = self._external_agents.get(external_did)
        if agent is None:
            return

        agent.interaction_count += 1
        agent.last_interaction_success = success

        # Trust-Upgrade-Logik (konservativ)
        if success:
            if (
                agent.trust_level == ExternalTrustLevel.UNTRUSTED
                and agent.interaction_count >= 5
            ):
                agent.trust_level = ExternalTrustLevel.VERIFIED
            elif (
                agent.trust_level == ExternalTrustLevel.VERIFIED
                and agent.interaction_count >= 20
            ):
                agent.trust_level = ExternalTrustLevel.TRUSTED
            # PARTNER nur manuell!
```

---

## 8. Phase 6 – Dynamic Trust Scoring <a id="8-phase-6"></a>

**Datei: `cognithor/aacs/trust/dynamic_scorer.py`**

```python
"""
Dynamic Trust Scorer – Automatische Vertrauensbewertung für Agents.

Agents die zuverlässig arbeiten bekommen höhere Trust-Scores.
Dies beeinflusst welche Capability Tokens der Planner ausstellt.

Relevanz für ARC-AGI-3:
Agents die mehr Puzzles lösen bekommen Zugriff auf mehr Rechenressourcen.

ANWEISUNG AN CODING-MODELL:
1. Prüfe ob bereits ein Score/Rating-System für Agents existiert.
2. Integriere den DynamicTrustScorer mit dem Planner.
3. Der Planner soll den Score nutzen um Token-Scope zu bestimmen.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from cognithor.aacs.config import AACS_CONFIG


@dataclass
class AgentTrustProfile:
    """Vertrauensprofil eines Agents."""
    agent_did: str
    trust_score: float = AACS_CONFIG.trust_score_initial  # 0.0 - 1.0
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    escalation_attempts: int = 0      # Verdächtige Eskalationsversuche
    last_activity: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def success_rate(self) -> float:
        """Erfolgsrate (0.0 - 1.0)."""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks

    @property
    def suggested_memory_tier_ceiling(self) -> int:
        """Empfohlene maximale Memory-Tier basierend auf Trust-Score."""
        if self.trust_score >= 0.9:
            return 4  # Tier 5 immer nur mit Operator
        if self.trust_score >= 0.7:
            return 3
        if self.trust_score >= 0.5:
            return 2
        return 1

    @property
    def suggested_delegation_depth(self) -> int:
        """Empfohlene maximale Delegationstiefe."""
        if self.trust_score >= 0.9:
            return 2
        if self.trust_score >= 0.7:
            return 1
        return 0


class DynamicTrustScorer:
    """
    Berechnet und aktualisiert Trust-Scores für Agents.

    Scoring-Formel:
    score = base_score * success_factor * decay_factor * penalty_factor

    Wobei:
    - base_score: Gewichteter Durchschnitt der Erfolgsrate
    - success_factor: Bonus für konstant erfolgreiche Arbeit
    - decay_factor: Zeitbasierter Verfall bei Inaktivität
    - penalty_factor: Straffe für Eskalationsversuche
    """

    def __init__(self) -> None:
        self._profiles: dict[str, AgentTrustProfile] = {}

    def get_or_create_profile(self, agent_did: str) -> AgentTrustProfile:
        """Holt oder erstellt ein Trust-Profil."""
        if agent_did not in self._profiles:
            self._profiles[agent_did] = AgentTrustProfile(agent_did=agent_did)
        return self._profiles[agent_did]

    def record_task_result(
        self, agent_did: str, success: bool
    ) -> AgentTrustProfile:
        """Aktualisiert den Trust-Score nach einer Task-Ausführung."""
        profile = self.get_or_create_profile(agent_did)
        profile.total_tasks += 1
        profile.last_activity = datetime.now(timezone.utc)

        if success:
            profile.successful_tasks += 1
        else:
            profile.failed_tasks += 1

        profile.trust_score = self._calculate_score(profile)
        return profile

    def record_escalation_attempt(self, agent_did: str) -> AgentTrustProfile:
        """
        Registriert einen Eskalationsversuch.
        Starke Strafe – reduziert Trust erheblich.
        """
        profile = self.get_or_create_profile(agent_did)
        profile.escalation_attempts += 1
        profile.last_activity = datetime.now(timezone.utc)
        profile.trust_score = self._calculate_score(profile)
        return profile

    def _calculate_score(self, profile: AgentTrustProfile) -> float:
        """
        Berechnet den aktuellen Trust-Score.

        Formel ist bewusst konservativ:
        - Schnelles Sinken bei Fehlern/Eskalation
        - Langsames Steigen bei Erfolgen
        - Zeitlicher Verfall bei Inaktivität
        """
        # Basis: Erfolgsrate mit Bayesian Smoothing
        # (verhindert dass 1/1 = 1.0 besser ist als 99/100 = 0.99)
        alpha = 2  # Prior successes
        beta = 2   # Prior failures
        base_score = (profile.successful_tasks + alpha) / (
            profile.total_tasks + alpha + beta
        )

        # Eskalations-Strafe (exponentiell)
        # Jeder Versuch halbiert den Score
        penalty_factor = 0.5 ** profile.escalation_attempts

        # Zeitlicher Verfall
        hours_inactive = (
            datetime.now(timezone.utc) - profile.last_activity
        ).total_seconds() / 3600
        decay_factor = math.exp(
            -AACS_CONFIG.trust_decay_rate * hours_inactive
        )

        # Erfahrungsbonus (langsam steigend)
        # Mehr abgeschlossene Tasks = höheres Vertrauen
        experience_factor = min(1.0, math.log1p(profile.total_tasks) / 5)

        score = base_score * penalty_factor * decay_factor * experience_factor

        # Clamp auf gültigen Bereich
        return max(
            AACS_CONFIG.trust_score_min,
            min(AACS_CONFIG.trust_score_max, score),
        )

    def get_recommended_token_params(
        self, agent_did: str
    ) -> dict:
        """
        Gibt empfohlene Token-Parameter für einen Agent zurück.
        Der Planner nutzt dies bei der Token-Erstellung.

        ANWEISUNG AN CODING-MODELL:
        Integriere diese Methode in den Planner.
        Wenn der Planner einen Token für einen Executor erstellt,
        soll er diese Empfehlungen als Obergrenze nutzen.
        """
        profile = self.get_or_create_profile(agent_did)
        return {
            "memory_tier_ceiling": profile.suggested_memory_tier_ceiling,
            "max_delegation_depth": profile.suggested_delegation_depth,
            "suggested_ttl": self._suggested_ttl(profile),
            "trust_score": profile.trust_score,
        }

    def _suggested_ttl(self, profile: AgentTrustProfile) -> int:
        """Empfohlene Token-Lebensdauer basierend auf Trust."""
        if profile.trust_score >= 0.9:
            return 600   # 10 Minuten
        if profile.trust_score >= 0.7:
            return 300   # 5 Minuten
        if profile.trust_score >= 0.5:
            return 120   # 2 Minuten
        return 30        # 30 Sekunden (minimal)
```

---

## 9. Testanforderungen <a id="9-testanforderungen"></a>

### 9.1 Pflicht-Tests (MÜSSEN alle grün sein)

```python
"""
ANWEISUNG AN CODING-MODELL:
Erstelle Tests für JEDE der folgenden Kategorien.
Nutze pytest. Mindestens die hier aufgelisteten Szenarien.
"""

# ── Phase 1: Token Core ──

class TestCapabilityToken:
    def test_token_creation_with_valid_params(self): ...
    def test_token_is_immutable(self): ...
    def test_expired_token_detected(self): ...
    def test_action_allowed_with_matching_resource(self): ...
    def test_action_denied_when_in_deny_list(self): ...
    def test_deny_overrides_allow(self): ...
    def test_wildcard_resource_matching(self): ...
    def test_payload_bytes_deterministic(self): ...
    def test_compute_hash_changes_with_different_nonce(self): ...

class TestTokenIssuer:
    def test_root_token_has_no_parent(self): ...
    def test_root_token_is_signed(self): ...
    def test_delegation_creates_child_token(self): ...
    def test_delegation_depth_incremented(self): ...
    def test_delegation_blocked_when_depth_zero(self): ...
    def test_child_cannot_exceed_parent_permissions(self): ...
    def test_child_cannot_exceed_parent_memory_tier(self): ...
    def test_child_cannot_exceed_parent_ttl(self): ...
    def test_child_has_parent_hash(self): ...

class TestTokenValidator:
    def test_valid_token_passes(self): ...
    def test_expired_token_rejected(self): ...
    def test_tampered_token_rejected(self): ...
    def test_unknown_issuer_rejected(self): ...
    def test_replay_attack_detected(self): ...
    def test_revoked_token_rejected(self): ...

# ── Phase 2: Audit ──

class TestCapabilityLogger:
    def test_chain_integrity_valid(self): ...
    def test_chain_integrity_detects_tampering(self): ...
    def test_events_retrievable_by_agent(self): ...
    def test_events_retrievable_by_token(self): ...

# ── Phase 3: MCP Gate ──

class TestMCPToolGate:
    def test_valid_token_allows_execution(self): ...
    def test_expired_token_blocks_execution(self): ...
    def test_wrong_permission_blocks_execution(self): ...
    def test_impersonation_blocked(self): ...
    def test_audit_log_created_on_allow(self): ...
    def test_audit_log_created_on_deny(self): ...

# ── Phase 4: Memory Gate ──

class TestMemoryGate:
    def test_tier1_accessible_by_any_executor(self): ...
    def test_tier4_blocked_for_low_ceiling_token(self): ...
    def test_tier5_write_requires_dual_signature(self): ...
    def test_tier5_read_without_dual_signature_ok(self): ...

# ── Phase 5: Trust Boundary ──

class TestTrustBoundary:
    def test_unknown_agent_gets_untrusted_ceiling(self): ...
    def test_trust_upgrade_after_interactions(self): ...
    def test_partner_only_manual(self): ...

# ── Phase 6: Dynamic Scorer ──

class TestDynamicTrustScorer:
    def test_initial_score_is_default(self): ...
    def test_score_increases_with_success(self): ...
    def test_score_decreases_with_failure(self): ...
    def test_escalation_severely_penalized(self): ...
    def test_score_clamped_to_valid_range(self): ...
    def test_recommended_params_scale_with_trust(self): ...
```

### 9.2 Integrationstests

```python
class TestPGEFlowIntegration:
    """
    End-to-End-Test: Planner → Gatekeeper → Executor mit AACS.

    ANWEISUNG AN CODING-MODELL:
    Dieser Test simuliert den vollständigen Ablauf:
    1. Planner erstellt Root-Token für Gatekeeper
    2. Gatekeeper validiert und erstellt Sub-Token für Executor
    3. Executor nutzt Sub-Token für MCP-Tool-Aufruf
    4. MCP Tool Gate prüft und erlaubt/verweigert
    5. Alles wird im Audit-Log protokolliert
    6. Audit-Chain-Integrität wird verifiziert
    """
    def test_happy_path_planner_to_executor(self): ...
    def test_executor_cannot_access_higher_tier(self): ...
    def test_executor_cannot_forge_planner_token(self): ...
    def test_revoked_token_blocks_mid_flow(self): ...
    def test_expired_token_blocks_mid_flow(self): ...
    def test_full_audit_trail_after_flow(self): ...
```

---

## 10. Migrationsplan <a id="10-migrationsplan"></a>

### 10.1 Reihenfolge (STRIKT einhalten)

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
  │          │          │          │          │          │
  │          │          │          │          │          └─ Dynamic Trust
  │          │          │          │          └─ A2A Gateway
  │          │          │          └─ Memory-Zugriffskontrolle
  │          │          └─ MCP-Tool-Gate
  │          └─ Audit-Integration
  └─ Token-System (MUSS zuerst fertig sein)
```

### 10.2 Feature-Flags

```python
"""
ANWEISUNG AN CODING-MODELL:
Implementiere Feature-Flags damit AACS schrittweise aktiviert werden kann.
Prüfe ob im Projekt bereits ein Feature-Flag-System existiert.
"""

# In cognithor/aacs/config.py ergänzen:
@dataclass
class AACSFeatureFlags:
    """Schrittweise Aktivierung des AACS."""
    token_validation_enabled: bool = False      # Phase 1
    audit_logging_enabled: bool = False          # Phase 2
    mcp_gate_enabled: bool = False               # Phase 3
    memory_gate_enabled: bool = False            # Phase 4
    a2a_trust_boundary_enabled: bool = False     # Phase 5
    dynamic_trust_scoring_enabled: bool = False  # Phase 6

    # Soft-Mode: Loggt Verstöße, blockiert aber nicht
    enforcement_mode: str = "log_only"  # "log_only" | "enforce"
```

### 10.3 Checkliste für das Coding-Modell

```markdown
## Vor Implementierung

- [ ] `aacs_audit_result.json` erstellt (Bestandsaufnahme)
- [ ] Bestehende Krypto-Utils identifiziert und Imports angepasst
- [ ] Bestehende Message-Klassen identifiziert
- [ ] PGE-Kommunikationspfade dokumentiert
- [ ] MCP-Tool-Aufrufstelle identifiziert
- [ ] Memory-System-Interface dokumentiert
- [ ] A2A-Protokoll-Einstiegspunkte identifiziert

## Phase 1 Abschluss

- [ ] CapabilityToken erstellt und signiert
- [ ] TokenIssuer erstellt Root- und Sub-Tokens
- [ ] TokenValidator prüft Signatur, TTL, Nonce, Revocation
- [ ] Attenuation-Regel ist kryptographisch erzwungen
- [ ] Alle Phase-1-Tests grün
- [ ] Feature-Flag `token_validation_enabled` schaltbar

## Phase 2 Abschluss

- [ ] CapabilityLogger erstellt verkettete Audit-Einträge
- [ ] HMAC-Integrität der Kette verifizierbar
- [ ] Hashline Guard Integration funktioniert
- [ ] GDPR: Events per Agent abrufbar (Recht auf Auskunft)
- [ ] Alle Phase-2-Tests grün

## Phase 3 Abschluss

- [ ] MCPToolGate prüft jeden Tool-Aufruf
- [ ] Bestehende Tool-Aufrufe durch Gate gewrapped
- [ ] Tool-Verb-Mapping konfiguriert
- [ ] Audit-Log für jede Erlaubnis/Ablehnung
- [ ] Alle Phase-3-Tests grün

## Phase 4 Abschluss

- [ ] MemoryGate kontrolliert alle Memory-Zugriffe
- [ ] Tier-Ceiling wird durchgesetzt
- [ ] Dual-Signatur für Tier 5 implementiert
- [ ] Operator-Key-Management eingerichtet
- [ ] Alle Phase-4-Tests grün

## Phase 5 Abschluss

- [ ] TrustBoundary für A2A-Kommunikation aktiv
- [ ] Externe Agents bekommen eingeschränkte Tokens
- [ ] Trust-Level-Upgrade funktioniert
- [ ] Alle Phase-5-Tests grün

## Phase 6 Abschluss

- [ ] DynamicTrustScorer bewertet alle Agents
- [ ] Planner nutzt Scores für Token-Erstellung
- [ ] Score-Verfall bei Inaktivität funktioniert
- [ ] Eskalationsstrafe funktioniert
- [ ] Alle Phase-6-Tests grün
- [ ] Integrationstests grün

## Final

- [ ] enforcement_mode von "log_only" auf "enforce" umgestellt
- [ ] Alle Feature-Flags aktiviert
- [ ] README/CHANGELOG aktualisiert
- [ ] Versionsnummer erhöht
```

---

## Anhang: Schnellreferenz für das Coding-Modell

| Frage | Antwort |
|-------|---------|
| Sprache? | Python 3.12+ |
| Krypto? | Ed25519 (PyNaCl bevorzugt, cryptography als Fallback) |
| Serialisierung? | JSON (deterministic: sort_keys, compact separators) |
| Tests? | pytest |
| Typ-Prüfung? | Type Hints überall, mypy-kompatibel |
| Immutability? | frozen dataclasses für Token/Audit-Einträge |
| Default-Verhalten? | DENY (alles was nicht explizit erlaubt ist, ist verboten) |
| Logging? | structlog falls vorhanden, sonst stdlib logging |
| Zeitzone? | Immer UTC (datetime.now(timezone.utc)) |
| GDPR? | Alle Events per Agent abrufbar und löschbar |
