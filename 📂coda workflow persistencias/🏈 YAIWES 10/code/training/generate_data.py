"""
Synthetic training data generation framework for autopentest specialist models.

Uses Claude API to generate high-quality training samples for all 4 models:
- Recon Agent (Qwen 2.5 7B)
- Classifier Agent (Mistral 7B)
- Exploit Agent (DeepSeek R1 8B)
- Report Agent (Llama 3.1 8B)
"""

import json
import hashlib
import os
from typing import Any
from dataclasses import dataclass, field

import anthropic
import jsonlines
from pydantic import BaseModel, ValidationError
from tqdm import tqdm


# --- Configuration ---

CLAUDE_MODEL = "claude-sonnet-4-6"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# --- Schemas ---

class AttackSurface(BaseModel):
    target: str
    subdomains: list[dict[str, Any]] = []
    hosts: list[dict[str, Any]] = []
    endpoints: list[dict[str, Any]] = []
    technologies: dict[str, str] = {}


class ClassifiedFinding(BaseModel):
    title: str
    description: str
    cve_ids: list[str] = []
    cvss_score: float = 0.0
    severity: str = "informational"
    attack_category: str = ""
    confidence: str = "unverified"


class AttackPlan(BaseModel):
    reasoning: str = ""
    paths: list[dict[str, Any]] = []


class ReportSection(BaseModel):
    section_type: str  # executive_summary, finding_writeup, remediation
    content: str


# --- Generator Framework ---

@dataclass
class SyntheticDataGenerator:
    """Framework for generating synthetic training data using Claude."""

    client: anthropic.Anthropic = field(default_factory=lambda: anthropic.Anthropic())
    model: str = CLAUDE_MODEL

    def generate_batch(
        self,
        prompt_template: str,
        variables_list: list[dict[str, Any]],
        schema: type[BaseModel],
        output_file: str,
    ) -> list[dict]:
        """Generate a batch of samples by varying template variables."""
        samples = []

        for variables in tqdm(variables_list, desc=f"Generating {output_file}"):
            prompt = prompt_template.format(**variables)

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text

                # Validate against schema
                parsed = self._parse_and_validate(content, schema)
                if parsed:
                    sample = {
                        "instruction": prompt,
                        "input": json.dumps(variables),
                        "output": content,
                    }
                    samples.append(sample)

            except Exception as e:
                print(f"  Error generating sample: {e}")
                continue

        # Save to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with jsonlines.open(output_file, mode="w") as writer:
            writer.write_all(samples)

        print(f"  Generated {len(samples)} samples -> {output_file}")
        return samples

    def _parse_and_validate(self, content: str, schema: type[BaseModel]) -> bool:
        """Validate generated content against schema."""
        # Strip markdown fences
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    schema.model_validate(item)
            else:
                schema.model_validate(data)
            return True
        except (json.JSONDecodeError, ValidationError):
            return False

    def deduplicate(self, samples: list[dict], threshold: float = 0.9) -> list[dict]:
        """Remove near-duplicate samples based on output hash similarity."""
        seen_hashes = set()
        unique = []

        for sample in samples:
            h = hashlib.md5(sample["output"].encode()).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique.append(sample)

        removed = len(samples) - len(unique)
        if removed > 0:
            print(f"  Deduplication removed {removed} samples")
        return unique

    def score_quality(self, sample: dict) -> float:
        """Score sample quality using Claude (1-5 scale)."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"Rate the quality of this training sample from 1-5. "
                               f"Respond with ONLY a number.\n\n"
                               f"Instruction: {sample['instruction'][:200]}\n"
                               f"Output: {sample['output'][:500]}"
                }],
            )
            score = float(response.content[0].text.strip())
            return min(max(score, 1.0), 5.0)
        except Exception:
            return 3.0  # default mid-range

    def split_dataset(
        self, samples: list[dict], train_ratio: float = 0.9, val_ratio: float = 0.08
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """Split samples into train/val/test sets."""
        n = len(samples)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        return samples[:train_end], samples[train_end:val_end], samples[val_end:]


if __name__ == "__main__":
    print("autopentest synthetic data generator")
    print("Run individual generation scripts:")
    print("  python training/generate_recon_data.py")
    print("  python training/generate_classifier_data.py")
    print("  python training/generate_exploit_data.py")
    print("  python training/generate_report_data.py")
