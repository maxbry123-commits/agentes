"""Generate synthetic training data for the Report Agent (Llama 3.1 8B).

Target: 20,000 samples
Format: campaign findings summary -> report section
"""

from generate_data import SyntheticDataGenerator, ReportSection, OUTPUT_DIR
import os

EXEC_SUMMARY_TEMPLATE = """Generate a professional penetration test executive summary.

Target: {target}
Industry: {industry}
Findings: {finding_summary}
Overall risk: {risk_level}

Write a 2-3 paragraph executive summary for a NON-TECHNICAL audience.
Focus on business risk, compliance implications, and recommended actions.
Do NOT include CVE IDs, commands, or technical jargon.

Respond as a JSON: {{"section_type": "executive_summary", "content": "..."}}"""

FINDING_WRITEUP_TEMPLATE = """Generate a professional finding writeup for a pentest report.

Title: {title}
Severity: {severity}
CVSS: {cvss}
Category: {category}
Target: {target}
Description: {description}

Write a detailed technical writeup covering:
1. What it is
2. Why it matters (business impact)
3. How it was found (methodology)
4. How to fix it (specific, actionable remediation)

Respond as JSON: {{"section_type": "finding_writeup", "content": "..."}}"""

REMEDIATION_TEMPLATE = """Generate a prioritized remediation plan for these findings:

{findings_list}

Write a remediation plan ordered by severity × ease of fix.
Be specific and actionable — include code examples where helpful.

Respond as JSON: {{"section_type": "remediation", "content": "..."}}"""

EXEC_SCENARIOS = [
    {"target": "example.com", "industry": "E-commerce", "finding_summary": "2 critical (SQLi, RCE), 3 high, 5 medium", "risk_level": "critical"},
    {"target": "app.fintech.io", "industry": "Financial services", "finding_summary": "1 critical (auth bypass), 2 high, 4 medium", "risk_level": "critical"},
    {"target": "portal.health.org", "industry": "Healthcare", "finding_summary": "0 critical, 2 high, 8 medium", "risk_level": "high"},
    {"target": "api.saas.dev", "industry": "SaaS/Technology", "finding_summary": "3 high (SSRF, IDOR, weak JWT), 6 medium", "risk_level": "high"},
]

FINDING_SCENARIOS = [
    {"title": "SQL Injection in Search", "severity": "critical", "cvss": "9.8", "category": "sqli", "target": "example.com/search", "description": "Error-based SQL injection"},
    {"title": "Reflected XSS in Comments", "severity": "high", "cvss": "7.1", "category": "xss", "target": "example.com/comments", "description": "Unsanitized user input"},
    {"title": "SSRF via URL Parameter", "severity": "high", "cvss": "8.6", "category": "ssrf", "target": "api.example.com/fetch", "description": "Server-side request forgery"},
    {"title": "Exposed Admin Panel", "severity": "medium", "cvss": "5.3", "category": "misconfig", "target": "admin.example.com", "description": "No authentication required"},
]


def generate_report_data(num_samples: int = 100):
    generator = SyntheticDataGenerator()

    # Mix of section types
    variables_exec = [EXEC_SCENARIOS[i % len(EXEC_SCENARIOS)] for i in range(num_samples // 3)]
    variables_finding = [FINDING_SCENARIOS[i % len(FINDING_SCENARIOS)] for i in range(num_samples // 3)]
    variables_remediation = [
        {"findings_list": f"1. {s['title']} ({s['severity']}, CVSS {s['cvss']})" for s in FINDING_SCENARIOS[:3]}
        for _ in range(num_samples // 3)
    ]

    output_dir = os.path.join(OUTPUT_DIR, "report")
    os.makedirs(output_dir, exist_ok=True)

    # Generate each type
    exec_samples = generator.generate_batch(EXEC_SUMMARY_TEMPLATE, variables_exec, ReportSection, os.path.join(output_dir, "exec_summary.jsonl"))
    finding_samples = generator.generate_batch(FINDING_WRITEUP_TEMPLATE, variables_finding, ReportSection, os.path.join(output_dir, "finding_writeups.jsonl"))
    remediation_samples = generator.generate_batch(REMEDIATION_TEMPLATE, variables_remediation, ReportSection, os.path.join(output_dir, "remediation.jsonl"))

    total = len(exec_samples) + len(finding_samples) + len(remediation_samples)
    print(f"  Total report samples: {total}")

    return exec_samples + finding_samples + remediation_samples


if __name__ == "__main__":
    print("Generating report agent training data...")
    generate_report_data(num_samples=12)
