"""Generate synthetic training data for the Classifier Agent (Mistral 7B).

Target: 30,000 samples
Format: RawFinding -> ClassifiedFinding with CVE, CVSS, severity
"""

from generate_data import SyntheticDataGenerator, ClassifiedFinding, OUTPUT_DIR
import os

PROMPT_TEMPLATE = """You are generating training data for an AI vulnerability classifier.

Given this raw security finding:
- Source tool: {tool}
- Finding type: {finding_type}
- Target: {target}
- Detail: {detail}

Generate the correct ClassifiedFinding JSON with:
- title: concise vulnerability title
- description: detailed technical description
- cve_ids: list of applicable CVE IDs (use real CVEs if applicable)
- cvss_score: CVSS v3.1 base score (0.0-10.0)
- severity: critical|high|medium|low|informational
- attack_category: sqli|xss|ssrf|rce|auth_bypass|info_disclosure|misconfig|path_traversal|idor|xxe|etc
- confidence: high|medium|low|unverified

Respond ONLY with valid JSON."""

FINDING_TYPES = [
    {"tool": "nuclei", "finding_type": "sqli", "target": "https://example.com/search?q=test", "detail": "SQL injection detected in search parameter via error-based technique"},
    {"tool": "nuclei", "finding_type": "xss", "target": "https://example.com/comments", "detail": "Reflected XSS in comment body parameter, unsanitized output"},
    {"tool": "httpx", "finding_type": "misconfig", "target": "https://admin.example.com", "detail": "Admin panel exposed without authentication, default credentials may work"},
    {"tool": "nuclei", "finding_type": "ssrf", "target": "https://api.example.com/fetch?url=", "detail": "SSRF via URL parameter, can reach internal network 169.254.169.254"},
    {"tool": "gau", "finding_type": "info_disclosure", "target": "https://example.com/.git/config", "detail": "Exposed .git repository with config containing AWS credentials"},
    {"tool": "nuclei", "finding_type": "rce", "target": "https://example.com/upload", "detail": "Unrestricted file upload allows PHP webshell execution"},
    {"tool": "naabu", "finding_type": "open_port", "target": "10.0.0.5:6379", "detail": "Redis exposed on port 6379 without authentication"},
    {"tool": "nuclei", "finding_type": "auth_bypass", "target": "https://api.example.com/admin", "detail": "JWT signature not verified, can forge admin tokens"},
]


def generate_classifier_data(num_samples: int = 100):
    generator = SyntheticDataGenerator()

    variables = []
    for i in range(num_samples):
        variables.append(FINDING_TYPES[i % len(FINDING_TYPES)])

    output_file = os.path.join(OUTPUT_DIR, "classifier", "classifier_train.jsonl")

    samples = generator.generate_batch(
        prompt_template=PROMPT_TEMPLATE,
        variables_list=variables,
        schema=ClassifiedFinding,
        output_file=output_file,
    )

    samples = generator.deduplicate(samples)
    train, val, test = generator.split_dataset(samples)
    print(f"  Splits: {len(train)} train, {len(val)} val, {len(test)} test")

    return samples


if __name__ == "__main__":
    print("Generating classifier agent training data...")
    generate_classifier_data(num_samples=10)
