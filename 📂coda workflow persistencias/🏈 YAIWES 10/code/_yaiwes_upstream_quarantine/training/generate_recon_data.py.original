"""Generate synthetic training data for the Recon Agent (Qwen 2.5 7B).

Target: 50,000 samples
Format: tool output -> structured AttackSurface JSON
"""

from generate_data import SyntheticDataGenerator, AttackSurface, OUTPUT_DIR
import os

PROMPT_TEMPLATE = """You are generating training data for an AI security reconnaissance agent.

Given the following simulated target profile:
- Target: {target}
- Subdomains: {subdomain_count}
- Open ports: {ports}
- Technologies: {technologies}
- OS: {os_type}

Generate TWO things:
1. Realistic raw tool output as if running nmap, subfinder, httpx against this target.
   Include realistic banners, version strings, and response headers.

2. The correct structured AttackSurface JSON that should be extracted from that output.

Format your response as JSON with two keys:
- "tool_output": the raw tool output string
- "attack_surface": the structured AttackSurface object

The AttackSurface must have: target, subdomains (list of {{domain, ip, source}}),
hosts (list of {{ip, hostnames, open_ports, services}}), endpoints (list of {{url, status_code}}),
technologies (dict of name->version)."""

# Target profiles for diversity
PROFILES = [
    {"target": "example.com", "subdomain_count": 5, "ports": "80,443,8080", "technologies": "nginx, PHP, MySQL", "os_type": "Linux"},
    {"target": "shop.example.com", "subdomain_count": 3, "ports": "80,443,3000", "technologies": "Next.js, Node.js, PostgreSQL", "os_type": "Linux"},
    {"target": "api.startup.io", "subdomain_count": 8, "ports": "443,8443,9090", "technologies": "Go, gRPC, Redis, Kubernetes", "os_type": "Linux"},
    {"target": "legacy.corp.net", "subdomain_count": 12, "ports": "80,443,8080,21,22,3389", "technologies": "IIS, ASP.NET, MSSQL", "os_type": "Windows"},
    {"target": "cloud.saas.dev", "subdomain_count": 20, "ports": "443", "technologies": "React, Python, Django, AWS", "os_type": "Linux"},
]


def generate_recon_data(num_samples: int = 100):
    """Generate recon training data. Set num_samples=50000 for full dataset."""
    generator = SyntheticDataGenerator()

    # Expand profiles to target count by cycling
    variables = []
    for i in range(num_samples):
        profile = PROFILES[i % len(PROFILES)].copy()
        profile["subdomain_count"] = profile["subdomain_count"] + (i % 10)
        variables.append(profile)

    output_file = os.path.join(OUTPUT_DIR, "recon", "recon_train.jsonl")

    samples = generator.generate_batch(
        prompt_template=PROMPT_TEMPLATE,
        variables_list=variables,
        schema=AttackSurface,
        output_file=output_file,
    )

    # Deduplicate
    samples = generator.deduplicate(samples)

    # Split
    train, val, test = generator.split_dataset(samples)
    print(f"  Splits: {len(train)} train, {len(val)} val, {len(test)} test")

    return samples


if __name__ == "__main__":
    print("Generating recon agent training data...")
    print("Set num_samples=50000 for full dataset (costs ~$50 in Claude API calls)")
    generate_recon_data(num_samples=10)  # small sample for testing
