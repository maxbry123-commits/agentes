"""Coverage-Tests fuer installer.py -- HardwareDetector, ModelRecommender, SetupWizard."""

from __future__ import annotations

from unittest.mock import patch

from cognithor.core.installer import (
    PRESETS,
    ChannelConfig,
    ChannelConfigurator,
    ChannelType,
    GPUInfo,
    HardwareDetector,
    HardwareProfile,
    ModelRecommendation,
    ModelRecommender,
    PresetConfig,
    PresetLevel,
    SetupState,
    SetupStep,
    SetupWizard,
)

# ============================================================================
# GPUInfo
# ============================================================================


class TestGPUInfo:
    def test_defaults(self) -> None:
        gpu = GPUInfo()
        assert gpu.name == "None"
        assert gpu.vram_gb == 0
        assert gpu.cuda_available is False

    def test_to_dict(self) -> None:
        gpu = GPUInfo(name="RTX 4090", vram_gb=24, cuda_available=True)
        d = gpu.to_dict()
        assert d["name"] == "RTX 4090"
        assert d["vram_gb"] == 24
        assert d["cuda"] is True


# ============================================================================
# HardwareProfile
# ============================================================================


class TestHardwareProfile:
    def test_tier_minimal(self) -> None:
        hp = HardwareProfile(ram_gb=4, cpu_cores=2)
        assert hp.tier == "minimal"

    def test_tier_standard(self) -> None:
        hp = HardwareProfile(ram_gb=16, cpu_cores=8, gpu=GPUInfo(vram_gb=8))
        assert hp.tier == "standard"

    def test_tier_power(self) -> None:
        hp = HardwareProfile(ram_gb=32, cpu_cores=12, gpu=GPUInfo(vram_gb=24))
        assert hp.tier == "power"

    def test_tier_enterprise(self) -> None:
        hp = HardwareProfile(ram_gb=128, cpu_cores=32, gpu=GPUInfo(vram_gb=80))
        assert hp.tier == "enterprise"

    def test_to_dict(self) -> None:
        hp = HardwareProfile(cpu_name="i9", cpu_cores=16, ram_gb=64)
        d = hp.to_dict()
        assert d["cpu"] == "i9"
        assert d["cores"] == 16
        assert "tier" in d


# ============================================================================
# HardwareDetector
# ============================================================================


class TestHardwareDetector:
    def test_detect_returns_profile(self) -> None:
        detector = HardwareDetector()
        profile = detector.detect()
        assert isinstance(profile, HardwareProfile)
        assert profile.cpu_cores >= 1
        assert profile.ram_gb > 0

    def test_from_specs(self) -> None:
        profile = HardwareDetector.from_specs(
            cpu="test",
            cores=8,
            ram_gb=32,
            gpu_name="RTX 4090",
            vram_gb=24,
        )
        assert profile.cpu_name == "test"
        assert profile.cpu_cores == 8
        assert profile.gpu.vram_gb == 24
        assert profile.gpu.cuda_available is True

    def test_from_specs_no_gpu(self) -> None:
        profile = HardwareDetector.from_specs(cores=4, ram_gb=16)
        assert profile.gpu.vram_gb == 0
        assert profile.gpu.cuda_available is False

    def test_detect_gpu_no_nvidia(self) -> None:
        detector = HardwareDetector()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            gpu = detector._detect_gpu()
            assert gpu.name == "None"


# ============================================================================
# ModelRecommender
# ============================================================================


class TestModelRecommender:
    def test_recommend_with_gpu(self) -> None:
        hw = HardwareProfile(ram_gb=32, gpu=GPUInfo(vram_gb=24))
        recommender = ModelRecommender()
        recs = recommender.recommend(hw, top_n=3)
        assert len(recs) <= 3
        assert all(isinstance(r, ModelRecommendation) for r in recs)

    def test_recommend_cpu_only(self) -> None:
        hw = HardwareProfile(ram_gb=16, gpu=GPUInfo(vram_gb=0))
        recommender = ModelRecommender()
        recs = recommender.recommend(hw)
        for r in recs:
            assert r.vram_required_gb == 0

    def test_recommend_no_candidates(self) -> None:
        hw = HardwareProfile(ram_gb=1, gpu=GPUInfo(vram_gb=0))
        recommender = ModelRecommender()
        recs = recommender.recommend(hw)
        assert isinstance(recs, list)

    def test_recommend_for_use_case(self) -> None:
        hw = HardwareProfile(ram_gb=32, gpu=GPUInfo(vram_gb=24))
        recommender = ModelRecommender()
        rec = recommender.recommend_for_use_case(hw, "Code")
        if rec:
            assert isinstance(rec, ModelRecommendation)

    def test_recommend_for_use_case_no_match(self) -> None:
        hw = HardwareProfile(ram_gb=32, gpu=GPUInfo(vram_gb=24))
        recommender = ModelRecommender()
        rec = recommender.recommend_for_use_case(hw, "nonexistent_use_case_xyz")
        # Falls back to first recommendation
        if rec:
            assert isinstance(rec, ModelRecommendation)

    def test_model_recommendation_to_dict(self) -> None:
        mr = ModelRecommendation(
            model_name="test:7b",
            model_size="7B",
            quantization="Q4_K_M",
            vram_required_gb=5,
            ram_required_gb=8,
            quality_score=7,
            speed_score=7,
            use_case="test",
        )
        d = mr.to_dict()
        assert d["model"] == "test:7b"
        assert d["quality"] == 7


# ============================================================================
# ChannelConfigurator
# ============================================================================


class TestChannelConfigurator:
    def test_configure_with_all_keys(self) -> None:
        cc = ChannelConfigurator()
        cfg = cc.configure(ChannelType.TELEGRAM, {"bot_token": "abc123"})
        assert cfg.enabled is True
        assert cfg.status == "configured"

    def test_configure_with_missing_keys(self) -> None:
        cc = ChannelConfigurator()
        cfg = cc.configure(ChannelType.TELEGRAM, {})
        assert cfg.enabled is False
        assert cfg.status == "unconfigured"

    def test_enable(self) -> None:
        cc = ChannelConfigurator()
        cc.configure(ChannelType.WEB, {"port": 8741, "host": "localhost"})
        assert cc.enable(ChannelType.WEB) is True
        assert cc.enable(ChannelType.TELEGRAM) is False  # Not configured

    def test_configured_channels(self) -> None:
        cc = ChannelConfigurator()
        cc.configure(ChannelType.WEB, {"port": 8741, "host": "localhost"})
        cc.configure(ChannelType.TELEGRAM, {})  # Missing token
        configured = cc.configured_channels()
        assert len(configured) == 1

    def test_channel_count(self) -> None:
        cc = ChannelConfigurator()
        assert cc.channel_count == 0
        cc.configure(ChannelType.API, {"api_key": "test"})
        assert cc.channel_count == 1

    def test_stats(self) -> None:
        cc = ChannelConfigurator()
        cc.configure(ChannelType.WEB, {"port": 8741, "host": "localhost"})
        stats = cc.stats()
        assert stats["total"] == 1
        assert stats["configured"] == 1

    def test_channel_config_to_dict(self) -> None:
        cfg = ChannelConfig(
            channel_type=ChannelType.TELEGRAM,
            enabled=True,
            config={"bot_token": "abc"},
            status="configured",
        )
        d = cfg.to_dict()
        assert d["type"] == "telegram"
        assert d["enabled"] is True


# ============================================================================
# SetupState
# ============================================================================


class TestSetupState:
    def test_is_complete(self) -> None:
        state = SetupState()
        assert state.is_complete is False
        state.current_step = SetupStep.COMPLETE
        assert state.is_complete is True

    def test_progress_percent(self) -> None:
        state = SetupState()
        state.current_step = SetupStep.WELCOME
        assert state.progress_percent == 0

        state.current_step = SetupStep.COMPLETE
        assert state.progress_percent == 100

    def test_to_dict(self) -> None:
        state = SetupState()
        d = state.to_dict()
        assert d["step"] == "welcome"
        assert d["complete"] is False


# ============================================================================
# SetupWizard
# ============================================================================


class TestSetupWizard:
    def test_init(self) -> None:
        wiz = SetupWizard()
        assert wiz.state.current_step == SetupStep.WELCOME

    def test_step_hardware_auto(self) -> None:
        wiz = SetupWizard()
        hw = wiz.step_hardware()
        assert isinstance(hw, HardwareProfile)
        assert wiz.state.current_step == SetupStep.HARDWARE_DETECT

    def test_step_hardware_manual(self) -> None:
        wiz = SetupWizard()
        manual = HardwareDetector.from_specs(cores=8, ram_gb=32, vram_gb=24)
        hw = wiz.step_hardware(manual=manual)
        assert hw.ram_gb == 32

    def test_step_model(self) -> None:
        wiz = SetupWizard()
        wiz.step_hardware(manual=HardwareDetector.from_specs(cores=8, ram_gb=32, vram_gb=24))
        recs = wiz.step_model()
        assert isinstance(recs, list)
        assert wiz.state.current_step == SetupStep.MODEL_SELECT

    def test_step_model_with_override(self) -> None:
        wiz = SetupWizard()
        wiz.step_hardware()
        wiz.step_model(override="custom:model")
        assert wiz.state.selected_model == "custom:model"

    def test_step_model_auto_hardware(self) -> None:
        wiz = SetupWizard()
        # step_model should auto-detect hardware if not set
        recs = wiz.step_model()
        assert isinstance(recs, list)

    def test_step_preset(self) -> None:
        wiz = SetupWizard()
        wiz.step_hardware(manual=HardwareDetector.from_specs(cores=8, ram_gb=32, vram_gb=24))
        preset = wiz.step_preset()
        assert isinstance(preset, PresetConfig)

    def test_step_preset_explicit(self) -> None:
        wiz = SetupWizard()
        preset = wiz.step_preset(PresetLevel.MINIMAL)
        assert preset.level == PresetLevel.MINIMAL

    def test_step_channels(self) -> None:
        wiz = SetupWizard()
        wiz.step_preset(PresetLevel.STANDARD)
        configs = wiz.step_channels()
        assert isinstance(configs, list)

    def test_step_channels_explicit(self) -> None:
        wiz = SetupWizard()
        configs = wiz.step_channels([ChannelType.WEB])
        assert len(configs) == 1

    def test_step_security(self) -> None:
        wiz = SetupWizard()
        assert wiz.step_security("mypassword") is True

    def test_step_first_agent(self) -> None:
        wiz = SetupWizard()
        name = wiz.step_first_agent("TestAgent")
        assert name == "TestAgent"

    def test_complete(self) -> None:
        wiz = SetupWizard()
        state = wiz.complete()
        assert state.is_complete

    def test_auto_setup(self) -> None:
        wiz = SetupWizard()
        state = wiz.auto_setup()
        assert state.is_complete

    def test_generate_config(self) -> None:
        wiz = SetupWizard()
        wiz.auto_setup()
        config = wiz.generate_config()
        assert "jarvis" in config
        assert "features" in config
        assert "channels" in config

    def test_stats(self) -> None:
        wiz = SetupWizard()
        stats = wiz.stats()
        assert "state" in stats
        assert "channels" in stats

    def test_properties(self) -> None:
        wiz = SetupWizard()
        assert isinstance(wiz.detector, HardwareDetector)
        assert isinstance(wiz.recommender, ModelRecommender)
        assert isinstance(wiz.channels, ChannelConfigurator)


# ============================================================================
# PresetConfig
# ============================================================================


class TestPresetConfig:
    def test_presets_exist(self) -> None:
        assert PresetLevel.MINIMAL in PRESETS
        assert PresetLevel.STANDARD in PRESETS
        assert PresetLevel.POWER in PRESETS
        assert PresetLevel.ENTERPRISE in PRESETS

    def test_preset_to_dict(self) -> None:
        preset = PRESETS[PresetLevel.STANDARD]
        d = preset.to_dict()
        assert d["preset"] == "Standard"
        assert d["level"] == "standard"
