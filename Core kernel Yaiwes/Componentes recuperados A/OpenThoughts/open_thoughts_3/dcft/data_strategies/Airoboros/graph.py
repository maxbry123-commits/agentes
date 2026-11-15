import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datasets import load_dataset

# Set Seaborn style
sns.set_style("whitegrid")
plt.style.use("seaborn-v0_8-whitegrid")

# Load dataset
dataset = load_dataset("mlfoundations-dev/airoboros_gpt-4o-mini", split="train")
df = dataset.to_pandas()


def extract_category(shard_id):
    if pd.isna(shard_id):
        return "unknown"
    parts = shard_id.split("::")[0]
    category = parts.replace("airoboros_stage_3", "").replace(
        "instructions_gpt-4o-mini", ""
    )
    return category.strip("_").rstrip("_")


# Apply category extraction
df["category"] = df["shard_id"].apply(extract_category)

# Calculate percentages
category_counts = df["category"].value_counts()
total = len(df)
category_percentages = (category_counts / total * 100).round(1)

# Set color scheme
colors = {
    "trivia": "#9966CC",  # Purple/violet
    "joke": "#FF4D79",  # Hot pink
    "roleplay": "#6699CC",  # Light blue
    "writing": "#FFB6C1",  # Light pink
    "agent": "#0066FF",  # Bright blue
    "coding": "#FF1493",  # Deep pink
    "contextual": "#FF8C00",  # Dark orange
    "general": "#00BFFF",  # Sky blue
    "orca": "#808080",  # Grey
    "wordgame": "#CD853F",  # Brown/tan
    "plan": "#FF6B6B",  # Coral red
    "cot": "#FFA500",  # Orange
    "counterfactual_contextual": "#90EE90",  # Light green
    "riddle": "#98FB98",  # Pale green
    "experience": "#483D8B",  # Dark slate blue
    "song": "#FFAA77",  # Peach
    "card": "#20B2AA",  # Light sea green
}

# Create donut chart
plt.figure(figsize=(10, 7), facecolor="white")
plt.pie(
    category_percentages[::-1],
    labels=None,
    colors=[colors.get(cat, "#333333") for cat in category_percentages.index[::-1]],
    autopct=lambda pct: f"{pct:.1f}%" if pct >= 3 else "",
    startangle=90,
    pctdistance=0.85,
    wedgeprops=dict(width=0.5, edgecolor="white"),
    labeldistance=1.1,
    textprops={"fontsize": 12, "weight": "bold"},
)

# Add legend with tighter positioning
plt.legend(
    category_percentages.index,
    title="Categories",
    loc="center left",
    bbox_to_anchor=(1, 0, 0.2, 1),
    frameon=False,
    facecolor="white",
    edgecolor="none",
    prop={"size": 10, "weight": "bold"},
)

plt.title(
    f"DCFT Airoboros dataset - {len(dataset)} rows", pad=20, fontsize=16, weight="bold"
)

plt.axis("equal")

# Save plot with tighter bounds
plt.savefig(
    os.path.join(str(Path.home()), "Downloads", "airoboros_category_distribution.png"),
    bbox_inches="tight",
    dpi=300,
    pad_inches=0.1,
)
plt.close()
