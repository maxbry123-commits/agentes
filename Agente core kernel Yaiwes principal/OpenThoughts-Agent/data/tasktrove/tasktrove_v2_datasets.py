"""TaskTrove v2 — vetted dataset catalog (96 entries)."""

EASY = [
    "DCAgent/inferredbugs-sandboxes-verifier",
    "DCAgent/code-contests-noblock",
    "SankalpKJ/nemotron-code-oracle-filtered",
    "DCAgent/llm-verifier-freelancer",
    "laion/exp_rpt_methods2test-large-v3",
    "laion/exp_rpt_stack-junit-v6",
    "DCAgent2/nl2bash-tasks-cleaned-oracle",
    "DCAgent/exp_rpt_curriculum-easy",
    "DCAgent/exp_rpt_e2egit-v2",
    "DCAgent/exp_rpt_e2egit-large",
    "DCAgent/exp_rpt_nemotron-junit",
    "DCAgent/exp_rpt_pymethods2test-v3",
    "DCAgent/exp_rpt_unitsyn-python-v3",
    "DCAgent/exp_rpt_unitsyn-python-large",
    "laion/exp_rpt_ghactions-v3",
    "laion/nemotron-gym-instruction-following-structured",
    "laion/nemotron-gym-agent-calendar",
    "laion/exp_rpt_crosscodeeval-csharp-v4",
    "laion/nemotron-gym-knowledge-web-search-mcqa",
    "laion/nemotron-gym-knowledge-mcqa",
    "laion/nemotron-gym-agent-workplace-v2",
    "laion/nemotron-gym-identity-following-v2",
    "laion/nemotron-gym-knowledge-openqa-v2",
    "laion/nemotron-gym-safety-v2",
]

MEDIUM = [
    "SankalpKJ/nemotron-math-oracle-filtered",
    "DCAgent/selfinstruct-naive-sandboxes-2-verified",
    "DCAgent/mix_h2_language_proportional",
    "DCAgent/mix_h4_binary_easy",
    "DCAgent/exp_rpt_pymethods2test-large",
    "laion/swegym-tasks-patched-validated-v2",
    "laion/exp_rpt_stack-bash-v3",
    "laion/exp_rpt_methods2test-large-v2",
    "laion/exp_rpt_codenet-python-v3",
    "DCAgent/exp_rpt_curriculum-medium",
    "laion/exp_rpt_nemotron-cpp-v2",
    "DCAgent/exp_rpt_pr",
    "DCAgent/exp_rpt_stack-pytest-large",
    "DCAgent/exp_rpt_stack-pytest-v2",
    "laion/mix_h1_struggle_zone-v2",
    "laion/mix_h2_language_balanced-v2",
    "laion/mix_h8_original_tests-v2",
    "laion/mix_h10_reward_binary-v2",
    "laion/mix_h10_reward_proportional-v2",
    "laion/mix_h10_reward_staged-v2",
    "laion/mix_h11_single_skill_only-v2",
    "laion/exp_rle_minimal_instructions-v3",
    "laion/nemotron-gym-instruction-following-calendar",
    "laion/nemotron-gym-competitive-coding",
    "laion/nemotron-gym-instruction-following-v2",
]

HARD = [
    "SankalpKJ/swesmith-oracle-filtered",
    "DCAgent/swe_rebench_patched_oracle",
    "DCAgent/r2egym-patched-full-oracle",
    "DCAgent/mix_h6_test_quality_top25",
    "laion/exp_rpt_scaffold-v2",
    "DCAgent/exp_rpt_crosscodeeval-java",
    "laion/exp_rle_heavy_padding-v2",
    "laion/exp_flat25_speed_bonus-v2",
    "laion/exp_flat25_pseudocode-v2",
    "laion/exp_flat25_stackoverflow-v2",
    "laion/openswe-tasks-patched-v5-oracle-success",
    "laion/exp_rpt_stack-go-v4",
    "DCAgent/exp_rpt_curriculum-hard",
    "DCAgent/exp_rpt_issue",
    "DCAgent/exp_rpt_multifile",
    "DCAgent/exp_rpt_stack-dockerfile-v2",
    "DCAgent/exp_rpt_stack-jest-v2",
    "DCAgent/exp_rpt_stack-jest-large",
    "laion/exp_flat25_subtle_debug-v3",
    "laion/exp_rle_detailed-v3",
    "laion/mix_baseline_uniform-v2",
    "laion/mix_h5_skill_diverse-v2",
    "laion/mix_h7_raw_volume_5k-v2",
    "laion/mix_h8_adversarial_tests-v2",
    "laion/mix_h11_compositional_gradient-v2",
    "laion/exp_rle_error_report-v3",
    "laion/exp_rle_github_issue-v3",
    "laion/exp_rpt_defects4j-v3-v4",
    "laion/nemotron-gym-math-stack-overflow",
    "laion/nemotron-gym-math-openmathreasoning",
    "laion/exp_rpt_stack-php-v2-v6",
    "laion/exp_rpt_stack-php-large-v6",
    "laion/nemotron-gym-instruction-following-adversarial-v3",
    "laion/nemotron-gym-math-advanced-calculations-v3",
]

UNKNOWN = [
    "DCAgent/swe_rebench_v2_patched_oracle",
    "laion/freelancer-projects-sandboxes-ta-rl-gpt-5-nano-v2",
    "laion/freelancer-projects-sandboxes-ta-rl-gpt-5-mini-v2",
    "laion/exp_rpt_taco-v2",
    "laion/exp_rpt_stack-bash-withtests-v2",
    "laion/exp_rpt_exercism-python-v2",
    "laion/exp_rpt_stack-ruby-v2",
    "laion/exp_rpt_stack-dockerfile-gpt5mini-v3",
    "DCAgent/exp_rle_adversarial",
    "laion/exp_rpt_stack-csharp-v5",
    "laion/exp_rpt_stack-bash-withtests-gpt5mini-v2",
    "laion/exp_rpt_pr-v2",
    "laion/exp_rpt_stack-rust-v2",
]

ALL = (
    [(r, "easy") for r in EASY]
    + [(r, "medium") for r in MEDIUM]
    + [(r, "hard") for r in HARD]
    + [(r, "unknown") for r in UNKNOWN]
)

if __name__ == "__main__":
    print(
        f"EASY={len(EASY)} MEDIUM={len(MEDIUM)} HARD={len(HARD)} UNKNOWN={len(UNKNOWN)} TOTAL={len(ALL)}"
    )
