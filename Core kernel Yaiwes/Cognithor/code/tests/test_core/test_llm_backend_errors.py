from __future__ import annotations

from cognithor.core.llm_backend import (
    LLMBackendError,
    LLMBadRequestError,
    VLLMDockerError,
    VLLMHardwareError,
    VLLMNotReadyError,
)


class TestErrorHierarchy:
    def test_all_vllm_errors_inherit_from_llm_backend_error(self):
        assert issubclass(LLMBadRequestError, LLMBackendError)
        assert issubclass(VLLMNotReadyError, LLMBackendError)
        assert issubclass(VLLMHardwareError, LLMBackendError)
        assert issubclass(VLLMDockerError, LLMBackendError)

    def test_errors_carry_recovery_hint(self):
        err = VLLMNotReadyError("container down", recovery_hint="Run: docker start vllm")
        assert err.recovery_hint == "Run: docker start vllm"
        assert str(err) == "container down"

    def test_recovery_hint_defaults_to_empty(self):
        err = VLLMDockerError("Docker not found")
        assert err.recovery_hint == ""

    def test_status_code_preserved_from_base(self):
        err = LLMBadRequestError("context too long", status_code=400)
        assert err.status_code == 400


class TestBackendTypeEnum:
    def test_vllm_is_a_backend_type(self):
        from cognithor.core.llm_backend import LLMBackendType

        assert LLMBackendType.VLLM == "vllm"
        assert LLMBackendType.VLLM.value == "vllm"

    def test_vllm_value_matches_config_literal(self):
        """config.CognithorConfig.llm_backend_type accepts "vllm" — keep enum aligned."""
        from cognithor.core.llm_backend import LLMBackendType

        assert "vllm" in {t.value for t in LLMBackendType}


class TestMediaUploadErrors:
    def test_media_upload_error_is_llm_backend_error(self):
        from cognithor.core.llm_backend import LLMBackendError, MediaUploadError

        assert issubclass(MediaUploadError, LLMBackendError)

    def test_too_large_inherits(self):
        from cognithor.core.llm_backend import MediaUploadError, MediaUploadTooLargeError

        assert issubclass(MediaUploadTooLargeError, MediaUploadError)
        err = MediaUploadTooLargeError("file is 600 MB, max is 500 MB", status_code=413)
        assert err.status_code == 413

    def test_unsupported_format_inherits(self):
        from cognithor.core.llm_backend import MediaUploadError, MediaUploadUnsupportedFormatError

        assert issubclass(MediaUploadUnsupportedFormatError, MediaUploadError)

    def test_quota_exceeded_inherits(self):
        from cognithor.core.llm_backend import MediaUploadError, MediaUploadQuotaExceededError

        assert issubclass(MediaUploadQuotaExceededError, MediaUploadError)

    def test_all_carry_recovery_hint(self):
        from cognithor.core.llm_backend import MediaUploadTooLargeError

        err = MediaUploadTooLargeError(
            "too big",
            recovery_hint="Shorten or downscale the clip before uploading.",
        )
        assert err.recovery_hint == "Shorten or downscale the clip before uploading."
