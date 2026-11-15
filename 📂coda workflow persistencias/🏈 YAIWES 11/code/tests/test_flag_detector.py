"""flag_detector.py 测试 — 各类 flag 格式的匹配与提取。"""

import pytest
from ctf_tool.flag_detector import detect_flag, extract_all_flags


class TestDetectFlag:
    """detect_flag() — 返回第一个匹配的 flag。"""

    def test_standard_flag(self):
        assert detect_flag("flag{hello123}") == "flag{hello123}"

    def test_flag_with_underscore(self):
        assert detect_flag("flag{hello_world}") == "flag{hello_world}"

    def test_flag_case_insensitive(self):
        assert detect_flag("Flag{test}") == "Flag{test}"

    def test_htb_flag(self):
        assert detect_flag("HTB{abc123}") == "HTB{abc123}"

    def test_ctf_flag(self):
        assert detect_flag("CTF{some_flag}") == "CTF{some_flag}"

    def test_uppercase_flag(self):
        assert detect_flag("FLAG{ALLCAPS}") == "FLAG{ALLCAPS}"

    def test_no_flag_returns_none(self):
        assert detect_flag("nothing here") is None

    def test_empty_string_returns_none(self):
        assert detect_flag("") is None

    def test_none_input_returns_none(self):
        assert detect_flag(None) is None

    def test_flag_in_output_surroundings(self):
        text = "some output\nmore data\nflag{target}\ntail"
        assert detect_flag(text) == "flag{target}"

    def test_flag_with_numbers_and_special(self):
        assert detect_flag("flag{abc_123_xyz}") == "flag{abc_123_xyz}"

    def test_first_flag_priority(self):
        """应返回优先级最高的匹配（flag{} 优先于 CTF{}）。"""
        text = "CTF{second} and flag{first}"
        assert detect_flag(text) == "flag{first}"

    def test_flag_with_dash(self):
        assert detect_flag("flag{test-flag-here}") == "flag{test-flag-here}"

    def test_false_positive_brace(self):
        """花括号但不含 flag 前缀不应匹配。"""
        # {单纯花括号} 不应被通用模式匹配（含下划线）
        # 通用模式要求 [A-Za-z0-9_]+ 前缀
        assert detect_flag("just some {braces}") is None


class TestExtractAllFlags:
    """extract_all_flags() — 提取所有匹配。"""

    def test_multiple_flags(self):
        flags = extract_all_flags("flag{first} and CTF{second}")
        assert "flag{first}" in flags
        assert "CTF{second}" in flags

    def test_empty_text(self):
        assert extract_all_flags("") == []

    def test_no_flags(self):
        assert extract_all_flags("just text") == []

    def test_duplicate_flags(self):
        """保留重复（调用方自行去重）。"""
        flags = extract_all_flags("flag{x} flag{x}")
        assert len(flags) >= 2
