"""Cognithor - Model Extension Registry & Multi-Language UI.

Point 4: Extended ML models and language support

  - ModelExtensionRegistry: Integration of custom models
  - ModelCapability:        Classification, extraction, translation, embeddings
  - I18nManager:            Multi-language UI
  - TranslationBundle:      Language packs (DE, EN, FR, ES, etc.)

Architecture reference: §5.3 (Model Router), §9.5 (Localization)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ============================================================================
# Model-Extension-Registry
# ============================================================================


class ModelCapability(Enum):
    """Capabilities of an ML model."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"
    IMAGE_ANALYSIS = "image_analysis"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"


class ModelProvider(Enum):
    """Origin of the model."""

    LOCAL = "local"  # Locally hosted (Ollama, llama.cpp)
    ANTHROPIC = "anthropic"  # Claude API
    OPENAI = "openai"  # OpenAI API
    CUSTOM_API = "custom_api"  # Custom API endpoint
    HUGGINGFACE = "huggingface"


@dataclass
class ModelDefinition:
    """Definition of an ML model."""

    model_id: str
    display_name: str
    provider: ModelProvider
    capabilities: set[ModelCapability] = field(default_factory=set)
    endpoint: str = ""
    api_key_ref: str = ""  # Reference to vault entry
    max_context: int = 4096
    languages: list[str] = field(default_factory=lambda: ["en"])
    cost_per_1k_tokens: float = 0.0
    is_default: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def supports(self, capability: ModelCapability) -> bool:
        return capability in self.capabilities

    def supports_language(self, lang: str) -> bool:
        return lang in self.languages

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "provider": self.provider.value,
            "capabilities": [c.value for c in self.capabilities],
            "languages": self.languages,
            "max_context": self.max_context,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "is_default": self.is_default,
        }


class ModelExtensionRegistry:
    """Registry for integrated ML models.

    Enables integration of custom models and
    automatic selection of the best model per task.
    """

    def __init__(self) -> None:
        self._models: dict[str, ModelDefinition] = {}
        self._defaults: dict[ModelCapability, str] = {}

    def register(self, model: ModelDefinition) -> None:
        """Register a new model."""
        self._models[model.model_id] = model
        if model.is_default:
            for cap in model.capabilities:
                self._defaults[cap] = model.model_id

    def unregister(self, model_id: str) -> bool:
        if model_id in self._models:
            del self._models[model_id]
            self._defaults = {k: v for k, v in self._defaults.items() if v != model_id}
            return True
        return False

    def get(self, model_id: str) -> ModelDefinition | None:
        return self._models.get(model_id)

    def set_default(self, capability: ModelCapability, model_id: str) -> bool:
        model = self._models.get(model_id)
        if model and model.supports(capability):
            self._defaults[capability] = model_id
            return True
        return False

    def get_default(self, capability: ModelCapability) -> ModelDefinition | None:
        model_id = self._defaults.get(capability)
        if model_id:
            return self._models.get(model_id)
        return None

    def find_models(
        self,
        *,
        capability: ModelCapability | None = None,
        provider: ModelProvider | None = None,
        language: str = "",
    ) -> list[ModelDefinition]:
        """Search models by criteria."""
        results = list(self._models.values())
        if capability:
            results = [m for m in results if m.supports(capability)]
        if provider:
            results = [m for m in results if m.provider == provider]
        if language:
            results = [m for m in results if m.supports_language(language)]
        return results

    def best_model_for(
        self,
        capability: ModelCapability,
        *,
        language: str = "en",
        prefer_local: bool = True,
    ) -> ModelDefinition | None:
        """Select the best model for a task."""
        # 1. Expliziter Default
        default = self.get_default(capability)
        if default and default.supports_language(language):
            return default

        # 2. Suche nach Capability + Sprache
        candidates = self.find_models(capability=capability, language=language)
        if not candidates:
            candidates = self.find_models(capability=capability)

        if not candidates:
            return None

        # Prefer local models if desired
        if prefer_local:
            local = [m for m in candidates if m.provider == ModelProvider.LOCAL]
            if local:
                return local[0]

        return candidates[0]

    @property
    def model_count(self) -> int:
        return len(self._models)

    def list_all(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._models.values()]

    def stats(self) -> dict[str, Any]:
        models = list(self._models.values())
        return {
            "total_models": len(models),
            "providers": list(set(m.provider.value for m in models)),
            "capabilities": list(set(c.value for m in models for c in m.capabilities)),
            "languages": list(set(lang for m in models for lang in m.languages)),
            "defaults_set": len(self._defaults),
        }


# ============================================================================
# Multi-Language-UI (i18n)
# ============================================================================


@dataclass
class TranslationBundle:
    """Language pack for a language."""

    locale: str  # e.g. "de", "en", "fr"
    name: str  # e.g. "Deutsch", "English"
    strings: dict[str, str] = field(default_factory=dict)

    def get(self, key: str, **kwargs: Any) -> str:
        """Get a translation with optional string interpolation."""
        template = self.strings.get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, IndexError):
                return template
        return template

    @property
    def string_count(self) -> int:
        return len(self.strings)


# Built-in Bundles
_BUNDLE_DE = TranslationBundle(
    locale="de",
    name="Deutsch",
    strings={
        # Navigation
        "nav.dashboard": "Dashboard",
        "nav.agents": "Agenten",
        "nav.monitoring": "Monitoring",
        "nav.marketplace": "Marktplatz",
        "nav.settings": "Einstellungen",
        "nav.security": "Sicherheit",
        "nav.compliance": "Compliance",
        "nav.workflows": "Workflows",
        "nav.connectors": "Konnektoren",
        # Dashboard
        "dashboard.title": "Jarvis Agent OS -- Dashboard",
        "dashboard.active_agents": "Aktive Agenten",
        "dashboard.tasks_running": "Laufende Tasks",
        "dashboard.success_rate": "Erfolgsquote",
        "dashboard.threats_detected": "Erkannte Bedrohungen",
        # Security
        "security.redteam": "Red-Team-Testing",
        "security.scan_now": "Jetzt scannen",
        "security.risk_score": "Risiko-Score",
        "security.findings": "Findings",
        "security.last_scan": "Letzter Scan",
        # Compliance
        "compliance.title": "Compliance-Bericht",
        "compliance.score": "Compliance-Score",
        "compliance.eu_ai_act": "EU-AI-Verordnung",
        "compliance.dsgvo": "DSGVO",
        "compliance.export": "Bericht exportieren",
        # Memory
        "memory.hygiene": "Memory-Hygiene",
        "memory.scan": "Memory scannen",
        "memory.quarantine": "Quarantäne",
        "memory.threats": "Bedrohungen",
        "memory.clean": "Sauber",
        # Workflows
        "workflow.start": "Workflow starten",
        "workflow.running": "Läuft",
        "workflow.completed": "Abgeschlossen",
        "workflow.templates": "Vorlagen",
        # Common
        "common.save": "Speichern",
        "common.cancel": "Abbrechen",
        "common.delete": "Löschen",
        "common.confirm": "Bestätigen",
        "common.loading": "Wird geladen…",
        "common.error": "Fehler",
        "common.success": "Erfolg",
        "common.status": "Status",
    },
)

_BUNDLE_EN = TranslationBundle(
    locale="en",
    name="English",
    strings={
        "nav.dashboard": "Dashboard",
        "nav.agents": "Agents",
        "nav.monitoring": "Monitoring",
        "nav.marketplace": "Marketplace",
        "nav.settings": "Settings",
        "nav.security": "Security",
        "nav.compliance": "Compliance",
        "nav.workflows": "Workflows",
        "nav.connectors": "Connectors",
        "dashboard.title": "Jarvis Agent OS -- Dashboard",
        "dashboard.active_agents": "Active Agents",
        "dashboard.tasks_running": "Running Tasks",
        "dashboard.success_rate": "Success Rate",
        "dashboard.threats_detected": "Threats Detected",
        "security.redteam": "Red Team Testing",
        "security.scan_now": "Scan Now",
        "security.risk_score": "Risk Score",
        "security.findings": "Findings",
        "security.last_scan": "Last Scan",
        "compliance.title": "Compliance Report",
        "compliance.score": "Compliance Score",
        "compliance.eu_ai_act": "EU AI Act",
        "compliance.dsgvo": "GDPR",
        "compliance.export": "Export Report",
        "memory.hygiene": "Memory Hygiene",
        "memory.scan": "Scan Memory",
        "memory.quarantine": "Quarantine",
        "memory.threats": "Threats",
        "memory.clean": "Clean",
        "workflow.start": "Start Workflow",
        "workflow.running": "Running",
        "workflow.completed": "Completed",
        "workflow.templates": "Templates",
        "common.save": "Save",
        "common.cancel": "Cancel",
        "common.delete": "Delete",
        "common.confirm": "Confirm",
        "common.loading": "Loading…",
        "common.error": "Error",
        "common.success": "Success",
        "common.status": "Status",
    },
)

_BUNDLE_FR = TranslationBundle(
    locale="fr",
    name="Français",
    strings={
        "nav.dashboard": "Tableau de bord",
        "nav.agents": "Agents",
        "nav.settings": "Paramètres",
        "nav.security": "Sécurité",
        "nav.compliance": "Conformité",
        "common.save": "Enregistrer",
        "common.cancel": "Annuler",
        "common.delete": "Supprimer",
        "common.loading": "Chargement…",
    },
)

_BUNDLE_ES = TranslationBundle(
    locale="es",
    name="Español",
    strings={
        "nav.dashboard": "Panel de control",
        "nav.agents": "Agentes",
        "nav.settings": "Configuración",
        "nav.security": "Seguridad",
        "common.save": "Guardar",
        "common.cancel": "Cancelar",
        "common.delete": "Eliminar",
        "common.loading": "Cargando…",
    },
)


class I18nManager:
    """Multi-language manager for the Cognithor UI.

    Manages language packs and provides translations
    based on the selected locale.
    """

    def __init__(self, default_locale: str = "de") -> None:
        self._bundles: dict[str, TranslationBundle] = {}
        self._default_locale = default_locale
        self._fallback_locale = "en"

        # Load built-in bundles
        for bundle in [_BUNDLE_DE, _BUNDLE_EN, _BUNDLE_FR, _BUNDLE_ES]:
            self._bundles[bundle.locale] = bundle

    @property
    def default_locale(self) -> str:
        return self._default_locale

    @default_locale.setter
    def default_locale(self, locale: str) -> None:
        self._default_locale = locale

    def add_bundle(self, bundle: TranslationBundle) -> None:
        self._bundles[bundle.locale] = bundle

    def t(self, key: str, *, locale: str = "", **kwargs: Any) -> str:
        """Translate a key into the selected language.

        If no translation available: fallback -> default -> key itself.
        """
        loc = locale or self._default_locale
        bundle = self._bundles.get(loc)

        if bundle:
            result = bundle.get(key, **kwargs)
            if result != key:
                return result

        # Fallback
        fallback = self._bundles.get(self._fallback_locale)
        if fallback:
            result = fallback.get(key, **kwargs)
            if result != key:
                return result

        return key

    def available_locales(self) -> list[dict[str, str]]:
        return [{"locale": b.locale, "name": b.name} for b in self._bundles.values()]

    def get_bundle(self, locale: str) -> TranslationBundle | None:
        return self._bundles.get(locale)

    def all_keys(self, locale: str = "") -> list[str]:
        loc = locale or self._default_locale
        bundle = self._bundles.get(loc)
        return list(bundle.strings.keys()) if bundle else []

    @property
    def locale_count(self) -> int:
        return len(self._bundles)

    def stats(self) -> dict[str, Any]:
        return {
            "default_locale": self._default_locale,
            "locale_count": len(self._bundles),
            "locales": [
                {"locale": b.locale, "name": b.name, "strings": b.string_count}
                for b in self._bundles.values()
            ],
        }
