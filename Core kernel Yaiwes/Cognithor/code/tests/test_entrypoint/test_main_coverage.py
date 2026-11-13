"""Coverage-Tests fuer __main__.py -- Banner, Channel-Registrierung, Startup."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cognithor.config import CognithorConfig, ensure_directory_structure


@pytest.fixture()
def config(tmp_path) -> CognithorConfig:
    cfg = CognithorConfig(cognithor_home=tmp_path)
    ensure_directory_structure(cfg)
    return cfg


# ============================================================================
# _print_banner
# ============================================================================


class TestPrintBanner:
    def test_banner_ollama(self, config: CognithorConfig, capsys) -> None:
        from cognithor.__main__ import _print_banner

        _print_banner(config, api_host="127.0.0.1", api_port=8741)
        captured = capsys.readouterr()
        assert "COGNITHOR" in captured.out
        assert "Agent OS" in captured.out
        assert "8741" in captured.out

    def test_banner_lmstudio(self, config: CognithorConfig, capsys) -> None:
        from cognithor.__main__ import _print_banner

        config.llm_backend_type = "lmstudio"
        config.lmstudio_base_url = "http://localhost:1234"
        _print_banner(config, api_host="0.0.0.0", api_port=9000)
        captured = capsys.readouterr()
        assert "LM Studio" in captured.out

    def test_banner_other_backend(self, config: CognithorConfig, capsys) -> None:
        from cognithor.__main__ import _print_banner

        config.llm_backend_type = "openai"
        _print_banner(config, api_host="127.0.0.1", api_port=8741)
        captured = capsys.readouterr()
        assert "openai" in captured.out.lower() or "LLM" in captured.out

    def test_banner_with_ssl(self, config: CognithorConfig, capsys) -> None:
        from cognithor.__main__ import _print_banner

        config.security.ssl_certfile = "/path/to/cert.pem"
        config.security.ssl_keyfile = "/path/to/key.pem"
        _print_banner(config, api_host="127.0.0.1", api_port=8741)
        captured = capsys.readouterr()
        assert "https" in captured.out


# ============================================================================
# parse_args
# ============================================================================


class TestParseArgs:
    def test_parse_no_args(self) -> None:
        from cognithor.__main__ import parse_args

        with patch("sys.argv", ["cognithor"]):
            args = parse_args()
            assert args.config is None
            assert args.init_only is False
            assert args.no_cli is False
            assert args.api_port == 8741

    def test_parse_init_only(self) -> None:
        from cognithor.__main__ import parse_args

        with patch("sys.argv", ["cognithor", "--init-only"]):
            args = parse_args()
            assert args.init_only is True

    def test_parse_no_cli(self) -> None:
        from cognithor.__main__ import parse_args

        with patch("sys.argv", ["cognithor", "--no-cli"]):
            args = parse_args()
            assert args.no_cli is True

    def test_parse_api_port(self) -> None:
        from cognithor.__main__ import parse_args

        with patch("sys.argv", ["cognithor", "--api-port", "9999"]):
            args = parse_args()
            assert args.api_port == 9999

    def test_parse_api_host(self) -> None:
        from cognithor.__main__ import parse_args

        with patch("sys.argv", ["cognithor", "--api-host", "0.0.0.0"]):
            args = parse_args()
            assert args.api_host == "0.0.0.0"

    def test_parse_log_level(self) -> None:
        from cognithor.__main__ import parse_args

        with patch("sys.argv", ["cognithor", "--log-level", "DEBUG"]):
            args = parse_args()
            assert args.log_level == "DEBUG"

    def test_parse_config_path(self, tmp_path) -> None:
        from cognithor.__main__ import parse_args

        cfg_file = tmp_path / "custom.yaml"
        with patch("sys.argv", ["cognithor", "--config", str(cfg_file)]):
            args = parse_args()
            assert args.config is not None


# ============================================================================
# main (init-only mode)
# ============================================================================


class TestMainInitOnly:
    def test_main_init_only(self, tmp_path) -> None:
        from cognithor.__main__ import main

        with patch("sys.argv", ["cognithor", "--init-only"]):
            with patch("cognithor.__main__.parse_args") as mock_parse:
                mock_args = MagicMock()
                mock_args.config = None
                mock_args.log_level = "WARNING"
                mock_args.init_only = True
                mock_args.no_cli = False
                mock_args.api_port = 8741
                mock_args.api_host = None
                mock_parse.return_value = mock_args

                with patch("cognithor.config.load_config") as mock_load:
                    cfg = CognithorConfig(cognithor_home=tmp_path)
                    ensure_directory_structure(cfg)
                    mock_load.return_value = cfg

                    with patch("cognithor.utils.logging.setup_logging"):
                        # Should return after init-only without starting
                        main()
